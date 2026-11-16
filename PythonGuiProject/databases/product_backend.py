"""
databases/product_backend.py

This file handles all product-related database actions.

Used by:
- admin/productsTotal.py
- inventory modules
- cashier modules
- order_backend.py indirectly when stock is deducted
"""

# ============================================================
# IMPORT DATABASE HELPERS
# ============================================================
from databases.db import fetch_all, fetch_one, execute_query, execute_insert
from databases.log_backend import add_log


# ============================================================
# GET ALL ACTIVE PRODUCTS
# ============================================================
def get_all_products():
    """
    Gets all active products from the products table.

    Used by:
    - admin/productsTotal.py
    - cashier product selection
    - inventory display

    Only products with status = 'active' are shown.
    """

    query = """
        SELECT 
            product_id, 
            product_name, 
            price, 
            unit, 
            quantity, 
            status
        FROM products
        WHERE status = 'active'
        ORDER BY product_name ASC
    """

    return fetch_all(query)



def get_inventory_products():
    """
    Gets all products for inventory display.

    Unlike get_all_products(), this includes:
    - active products
    - inactive/unavailable products
    """

    query = """
        SELECT 
            product_id, 
            product_name, 
            price, 
            unit, 
            quantity, 
            status
        FROM products
        ORDER BY 
            CASE 
                WHEN status = 'active' THEN 1
                WHEN status = 'inactive' THEN 2
                ELSE 3
            END,
            product_name ASC
    """

    return fetch_all(query)




# ============================================================
# SEARCH PRODUCTS
# ============================================================
def search_products(keyword):
    """
    Searches active products by product name.

    Example:
    keyword = "wing"
    It can find "Chicken Wings".
    """

    query = """
        SELECT 
            product_id, 
            product_name, 
            price, 
            unit, 
            quantity, 
            status
        FROM products
        WHERE status = 'active'
        AND product_name LIKE %s
        ORDER BY product_name ASC
    """

    return fetch_all(query, (f"%{keyword}%",))


# ============================================================
# GET PRODUCT BY ID
# ============================================================
def get_product_by_id(product_id):
    """
    Gets one product using product_id.
    """

    query = """
        SELECT 
            product_id, 
            product_name, 
            price, 
            unit, 
            quantity, 
            status
        FROM products
        WHERE product_id = %s
        LIMIT 1
    """

    return fetch_one(query, (product_id,))


# ============================================================
# GET PRODUCT SUMMARY FOR ADMIN PRODUCTS TOTAL
# ============================================================
def get_product_summary():
    """
    Gets summary numbers for admin/productsTotal.py.

    Returns:
    - total_products
    - total_units
    - stock_value
    - low_stock_count

    Low stock means quantity is less than 10.
    """

    query = """
        SELECT
            COUNT(product_id) AS total_products,
            COALESCE(SUM(quantity), 0) AS total_units,
            COALESCE(SUM(price * quantity), 0) AS stock_value,
            SUM(CASE WHEN quantity < 10 THEN 1 ELSE 0 END) AS low_stock_count
        FROM products
        WHERE status = 'active'
    """

    result = fetch_one(query)

    if not result:
        return {
            "total_products": 0,
            "total_units": 0,
            "stock_value": 0,
            "low_stock_count": 0
        }

    return result


# ============================================================
# ADD PRODUCT
# ============================================================
def add_product(product_name, price, unit, quantity, user_id=None):
    """
    Adds a new product.

    What happens:
    1. Insert product into products table.
    2. Add activity log.
    3. Add stock movement record for initial stock.
    """

    query = """
        INSERT INTO products (product_name, price, unit, quantity)
        VALUES (%s, %s, %s, %s)
    """

    product_id = execute_insert(query, (product_name, price, unit, quantity))

    if product_id:
        add_log(user_id, "ADD_PRODUCT", f"Added product: {product_name}")

        add_stock_movement(
            product_id,
            "add",
            quantity,
            "Initial product stock"
        )

    return product_id


# ============================================================
# UPDATE PRODUCT
# ============================================================
def update_product(product_id, product_name, price, unit, quantity, user_id=None):
    """
    Updates an existing product.

    What happens:
    1. Gets old product data.
    2. Updates product details.
    3. Logs the edit.
    4. Adds stock movement if quantity changed.
    """

    old_product = get_product_by_id(product_id)

    query = """
        UPDATE products
        SET product_name = %s,
            price = %s,
            unit = %s,
            quantity = %s
        WHERE product_id = %s
    """

    result = execute_query(
        query,
        (product_name, price, unit, quantity, product_id)
    )

    if result:
        add_log(
            user_id,
            "EDIT_PRODUCT",
            f"Edited product ID {product_id}: {product_name}"
        )

        if old_product:
            old_quantity = int(old_product["quantity"])
            new_quantity = int(quantity)
            quantity_difference = new_quantity - old_quantity

            if quantity_difference != 0:
                add_stock_movement(
                    product_id,
                    "edit",
                    quantity_difference,
                    "Product stock updated"
                )

    return result


# ============================================================
# DELETE PRODUCT / MARK INACTIVE
# ============================================================
def delete_product(product_id, user_id=None):
    """
    Soft deletes a product.

    It does not remove the product row.
    It only changes status to inactive.

    This is better because old order records can still keep their product history.
    """

    query = """
        UPDATE products
        SET status = 'inactive'
        WHERE product_id = %s
    """

    result = execute_query(query, (product_id,))

    if result:
        add_log(user_id, "DELETE_PRODUCT", f"Deleted product ID {product_id}")

        add_stock_movement(
            product_id,
            "delete",
            0,
            "Product marked inactive"
        )

    return result


# ============================================================
# RESTORE PRODUCT
# ============================================================
def restore_product(product_id, user_id=None):
    """
    Restores an inactive product back to active.

    This is optional, but useful if you accidentally deleted a product.
    """

    query = """
        UPDATE products
        SET status = 'active'
        WHERE product_id = %s
    """

    result = execute_query(query, (product_id,))

    if result:
        add_log(user_id, "RESTORE_PRODUCT", f"Restored product ID {product_id}")

        add_stock_movement(
            product_id,
            "restore",
            0,
            "Product restored to active"
        )

    return result


# ============================================================
# ADD STOCK MOVEMENT
# ============================================================
def add_stock_movement(product_id, movement_type, quantity_changed, remarks):
    """
    Adds a record to stock_movements table.

    This helps track what happened to product stock.

    movement_type examples:
    - add
    - edit
    - sale
    - delete
    - restore
    """

    query = """
        INSERT INTO stock_movements 
        (product_id, movement_type, quantity_changed, remarks)
        VALUES (%s, %s, %s, %s)
    """

    return execute_query(
        query,
        (product_id, movement_type, quantity_changed, remarks)
    )




def set_product_status(product_id, status, user_id=None):
    """
    Changes product status.

    status:
    - active = Available
    - inactive = Unavailable
    """

    if status not in ("active", "inactive"):
        return False

    query = """
        UPDATE products
        SET status = %s
        WHERE product_id = %s
    """

    result = execute_query(query, (status, product_id))

    if result:
        action = "RESTORE_PRODUCT" if status == "active" else "MARK_UNAVAILABLE"
        remarks = "Product restored to active" if status == "active" else "Product marked unavailable"

        add_log(user_id, action, f"{remarks}: Product ID {product_id}")

        add_stock_movement(
            product_id,
            "restore" if status == "active" else "delete",
            0,
            remarks
        )

    return result


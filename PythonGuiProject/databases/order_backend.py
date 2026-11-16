"""
databases/order_backend.py

This file handles all order-related database actions.

Used by:
- cashier/orders.py       -> create_order()
- admin/orders.py         -> view, accept, cancel orders
- admin/adminDashboard.py -> indirectly through reports/backend

Updated:
- Supports typed quantity from cashier side through cart_items
- Supports discount type and discount amount
- Supports cash and online payment
- Supports online payment reference number
"""

# ============================================================
# IMPORT DATABASE HELPERS
# ============================================================
from databases.db import fetch_all, fetch_one, execute_query, get_connection
from databases.log_backend import add_log


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def safe_float(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def safe_int(value):
    try:
        return int(value or 0)
    except Exception:
        return 0


# ============================================================
# CREATE ORDER - USED BY CASHIER
# ============================================================
def create_order(
    cashier_id,
    cart_items,
    amount_received=0,
    change_amount=None,
    discount_type="No Discount",
    discount_amount=0,
    payment_method="Cash",
    online_reference=None
):
    """
    Creates a new pending order.

    cart_items sample:
    [
        {
            "product_id": 1,
            "product_name": "Whole Chicken",
            "price": 180.00,
            "quantity": 2
        }
    ]

    What happens:
    1. Compute subtotal amount.
    2. Apply discount.
    3. Compute final total amount.
    4. Validate payment.
    5. Insert order into orders table.
    6. Insert items into order_items table.
    7. Insert payment into payments table.
    8. Save activity log.

    Notes:
    - subtotal_amount = total before discount
    - total_amount = final payable total after discount
    """

    if not cart_items:
        return None, "Cart is empty."

    subtotal_amount = 0.0

    for item in cart_items:
        price = safe_float(item.get("price") or item.get("unit_price"))
        quantity = safe_int(item.get("quantity") or item.get("qty"))
        subtotal_amount += price * quantity

    discount_amount = safe_float(discount_amount)

    if discount_amount < 0:
        discount_amount = 0.0

    if discount_amount > subtotal_amount:
        discount_amount = subtotal_amount

    total_amount = subtotal_amount - discount_amount

    amount_received = safe_float(amount_received)

    payment_method = str(payment_method or "Cash").strip()

    if payment_method == "":
        payment_method = "Cash"

    if payment_method.lower() == "online payment":
        amount_received = total_amount
        change_amount = 0.0
    else:
        payment_method = "Cash"

        if amount_received < total_amount:
            return None, "Amount received is not enough."

        if change_amount is None:
            change_amount = amount_received - total_amount

    change_amount = safe_float(change_amount)

    connection = get_connection()

    if connection is None:
        return None, "Database connection failed."

    cursor = connection.cursor()

    try:
        # --------------------------------------------------------
        # 1. Create pending order
        # --------------------------------------------------------
        cursor.execute(
            """
            INSERT INTO orders
            (
                cashier_id,
                subtotal_amount,
                discount_type,
                discount_amount,
                total_amount,
                order_status
            )
            VALUES (%s, %s, %s, %s, %s, 'pending')
            """,
            (
                cashier_id,
                subtotal_amount,
                discount_type,
                discount_amount,
                total_amount
            )
        )

        order_id = cursor.lastrowid

        # --------------------------------------------------------
        # 2. Insert each item in the order
        # --------------------------------------------------------
        for item in cart_items:
            product_id = item["product_id"]
            product_name = item["product_name"]
            price = safe_float(item.get("price") or item.get("unit_price"))
            quantity = safe_int(item.get("quantity") or item.get("qty"))
            subtotal = price * quantity

            cursor.execute(
                """
                INSERT INTO order_items
                (
                    order_id,
                    product_id,
                    product_name,
                    price,
                    quantity,
                    subtotal
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    order_id,
                    product_id,
                    product_name,
                    price,
                    quantity,
                    subtotal
                )
            )

        # --------------------------------------------------------
        # 3. Insert payment
        # --------------------------------------------------------
        cursor.execute(
            """
            INSERT INTO payments
            (
                order_id,
                amount_received,
                change_amount,
                payment_method,
                online_reference
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                order_id,
                amount_received,
                change_amount,
                payment_method,
                online_reference
            )
        )

        # --------------------------------------------------------
        # 4. Insert activity log
        # --------------------------------------------------------
        cursor.execute(
            """
            INSERT INTO activity_logs
            (
                user_id,
                action_type,
                description
            )
            VALUES (%s, %s, %s)
            """,
            (
                cashier_id,
                "CREATE_ORDER",
                (
                    f"Created pending order #{order_id}. "
                    f"Subtotal: {subtotal_amount}, "
                    f"Discount: {discount_amount}, "
                    f"Total: {total_amount}, "
                    f"Payment: {payment_method}"
                )
            )
        )

        connection.commit()

        return {
            "order_id": order_id,
            "subtotal_amount": subtotal_amount,
            "discount_type": discount_type,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
            "amount_received": amount_received,
            "change_amount": change_amount,
            "payment_method": payment_method,
            "online_reference": online_reference,
            "status": "pending"
        }, "Order sent to admin for confirmation."

    except Exception as e:
        connection.rollback()
        return None, str(e)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# GET ADMIN ORDERS - USED BY ADMIN ORDERS PAGE
# ============================================================
def get_admin_orders(status_filter="All"):
    """
    Gets orders for admin/orders.py.

    status_filter can be:
    - All
    - Pending
    - Accepted
    - Cancelled
    """

    query = """
        SELECT
            o.order_id,
            u.full_name AS cashier_name,
            COALESCE(o.subtotal_amount, o.total_amount, 0) AS subtotal_amount,
            COALESCE(o.discount_type, 'No Discount') AS discount_type,
            COALESCE(o.discount_amount, 0) AS discount_amount,
            COALESCE(o.total_amount, 0) AS total_amount,
            o.order_status,
            o.created_at,
            o.accepted_at,
            o.cancelled_at,
            COALESCE(p.amount_received, 0) AS amount_received,
            COALESCE(p.change_amount, 0) AS change_amount,
            COALESCE(p.payment_method, 'Cash') AS payment_method,
            COALESCE(p.online_reference, '') AS online_reference
        FROM orders o
        JOIN users u ON o.cashier_id = u.user_id
        LEFT JOIN payments p ON o.order_id = p.order_id
    """

    params = []

    if status_filter != "All":
        query += " WHERE o.order_status = %s "
        params.append(status_filter.lower())

    query += """
        ORDER BY o.created_at DESC, o.order_id DESC
    """

    return fetch_all(query, tuple(params))


# ============================================================
# GET PENDING ORDERS ONLY
# ============================================================
def get_pending_orders():
    """
    Gets pending orders only.
    """

    query = """
        SELECT
            o.order_id,
            u.full_name AS cashier_name,
            COALESCE(o.subtotal_amount, o.total_amount, 0) AS subtotal_amount,
            COALESCE(o.discount_type, 'No Discount') AS discount_type,
            COALESCE(o.discount_amount, 0) AS discount_amount,
            COALESCE(o.total_amount, 0) AS total_amount,
            o.order_status,
            o.created_at,
            COALESCE(p.amount_received, 0) AS amount_received,
            COALESCE(p.change_amount, 0) AS change_amount,
            COALESCE(p.payment_method, 'Cash') AS payment_method,
            COALESCE(p.online_reference, '') AS online_reference
        FROM orders o
        JOIN users u ON o.cashier_id = u.user_id
        LEFT JOIN payments p ON o.order_id = p.order_id
        WHERE o.order_status = 'pending'
        ORDER BY o.created_at DESC
    """

    return fetch_all(query)


# ============================================================
# GET ALL ORDERS
# ============================================================
def get_all_orders():
    """
    Gets all orders.
    """

    return get_admin_orders("All")


# ============================================================
# GET ONE ORDER BY ID
# ============================================================
def get_order_by_id(order_id):
    """
    Gets one order using order_id.
    """

    query = """
        SELECT
            o.order_id,
            o.cashier_id,
            COALESCE(o.subtotal_amount, o.total_amount, 0) AS subtotal_amount,
            COALESCE(o.discount_type, 'No Discount') AS discount_type,
            COALESCE(o.discount_amount, 0) AS discount_amount,
            COALESCE(o.total_amount, 0) AS total_amount,
            o.order_status,
            o.created_at,
            o.accepted_at,
            o.cancelled_at,
            COALESCE(p.amount_received, 0) AS amount_received,
            COALESCE(p.change_amount, 0) AS change_amount,
            COALESCE(p.payment_method, 'Cash') AS payment_method,
            COALESCE(p.online_reference, '') AS online_reference
        FROM orders o
        LEFT JOIN payments p ON o.order_id = p.order_id
        WHERE o.order_id = %s
        LIMIT 1
    """

    return fetch_one(query, (order_id,))


# ============================================================
# GET ORDER ITEMS
# ============================================================
def get_order_items(order_id):
    """
    Gets all items from one order.
    """

    query = """
        SELECT
            order_item_id,
            product_id,
            product_name,
            price,
            quantity,
            subtotal
        FROM order_items
        WHERE order_id = %s
        ORDER BY order_item_id ASC
    """

    return fetch_all(query, (order_id,))


# ============================================================
# ACCEPT ORDER - USED BY ADMIN
# ============================================================
def accept_order(order_id, admin_id=None):
    """
    Accepts a pending order.

    What happens:
    1. Check if order exists.
    2. Check if order is pending.
    3. Get order items.
    4. Check if products have enough stock.
    5. Deduct product stock.
    6. Insert stock movement logs.
    7. Update order status to accepted.
    8. Insert activity log.

    Important:
    Sales are counted only after order_status becomes accepted.
    """

    connection = get_connection()

    if connection is None:
        return False, "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT order_id, order_status
            FROM orders
            WHERE order_id = %s
            LIMIT 1
            """,
            (order_id,)
        )

        order = cursor.fetchone()

        if not order:
            return False, "Order not found."

        if order["order_status"] != "pending":
            return False, "Only pending orders can be accepted."

        cursor.execute(
            """
            SELECT product_id, product_name, quantity
            FROM order_items
            WHERE order_id = %s
            """,
            (order_id,)
        )

        items = cursor.fetchall()

        if not items:
            return False, "This order has no items."

        # --------------------------------------------------------
        # Check product stock first
        # --------------------------------------------------------
        for item in items:
            cursor.execute(
                """
                SELECT product_id, product_name, quantity, status
                FROM products
                WHERE product_id = %s
                LIMIT 1
                """,
                (item["product_id"],)
            )

            product = cursor.fetchone()

            if not product:
                return False, f"Product not found: {item['product_name']}"

            if product["status"] != "active":
                return False, f"Product is inactive: {item['product_name']}"

            if int(product["quantity"]) < int(item["quantity"]):
                return False, f"Not enough stock for {product['product_name']}."

        # --------------------------------------------------------
        # Deduct product stock
        # --------------------------------------------------------
        for item in items:
            cursor.execute(
                """
                UPDATE products
                SET quantity = quantity - %s
                WHERE product_id = %s
                """,
                (item["quantity"], item["product_id"])
            )

            cursor.execute(
                """
                INSERT INTO stock_movements
                (
                    product_id,
                    movement_type,
                    quantity_changed,
                    remarks
                )
                VALUES (%s, 'sale', %s, %s)
                """,
                (
                    item["product_id"],
                    -int(item["quantity"]),
                    f"Sold from accepted order #{order_id}"
                )
            )

        # --------------------------------------------------------
        # Update order status
        # --------------------------------------------------------
        cursor.execute(
            """
            UPDATE orders
            SET order_status = 'accepted',
                accepted_at = CURRENT_TIMESTAMP
            WHERE order_id = %s
            """,
            (order_id,)
        )

        cursor.execute(
            """
            INSERT INTO activity_logs
            (
                user_id,
                action_type,
                description
            )
            VALUES (%s, %s, %s)
            """,
            (
                admin_id,
                "ACCEPT_ORDER",
                f"Accepted order #{order_id}"
            )
        )

        connection.commit()
        return True, "Order accepted successfully."

    except Exception as e:
        connection.rollback()
        return False, str(e)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# CANCEL ORDER - USED BY ADMIN
# ============================================================
def cancel_order(order_id, admin_id=None):
    """
    Cancels a pending order.

    Important:
    Only pending orders can be cancelled.
    Accepted orders should not be cancelled here because stock was already deducted.
    """

    order = get_order_by_id(order_id)

    if not order:
        return False, "Order not found."

    if order["order_status"] != "pending":
        return False, "Only pending orders can be cancelled."

    query = """
        UPDATE orders
        SET order_status = 'cancelled',
            cancelled_at = CURRENT_TIMESTAMP
        WHERE order_id = %s
        AND order_status = 'pending'
    """

    result = execute_query(query, (order_id,))

    if result:
        add_log(admin_id, "CANCEL_ORDER", f"Cancelled order #{order_id}")
        return True, "Order cancelled successfully."

    return False, "Unable to cancel order."
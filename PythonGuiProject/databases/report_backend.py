"""
databases/report_backend.py

This file handles report-related database queries.

Used by:
- admin/adminDashboard.py
- admin/mostbuyedproducts.py
- admin/report.py
- databases/pdf_report_backend.py

Flow:
admin UI
→ report_backend.py
→ db.py
→ MySQL
"""

# ============================================================
# IMPORT DATABASE HELPERS
# ============================================================
from databases.db import fetch_all, fetch_one


# ============================================================
# SALES SUMMARY: TODAY
# ============================================================
def get_sales_today():
    """
    Gets total sales and total accepted orders for today.
    """

    query = """
        SELECT 
            COALESCE(SUM(total_amount), 0) AS total_sales,
            COUNT(order_id) AS total_orders
        FROM orders
        WHERE order_status = 'accepted'
        AND DATE(accepted_at) = CURDATE()
    """

    return fetch_one(query)


# ============================================================
# SALES SUMMARY: SPECIFIC DAY
# ============================================================
def get_sales_by_day(date_value):
    """
    Gets total sales and total accepted orders for a specific date.
    """

    query = """
        SELECT 
            COALESCE(SUM(total_amount), 0) AS total_sales,
            COUNT(order_id) AS total_orders
        FROM orders
        WHERE order_status = 'accepted'
        AND DATE(accepted_at) = %s
    """

    return fetch_one(query, (date_value,))


# ============================================================
# SALES SUMMARY: MONTH
# ============================================================
def get_sales_by_month(year_value, month_value):
    """
    Gets total sales and total accepted orders for a specific month.
    """

    query = """
        SELECT 
            COALESCE(SUM(total_amount), 0) AS total_sales,
            COUNT(order_id) AS total_orders
        FROM orders
        WHERE order_status = 'accepted'
        AND YEAR(accepted_at) = %s
        AND MONTH(accepted_at) = %s
    """

    return fetch_one(query, (year_value, month_value))


# ============================================================
# SALES SUMMARY: YEAR
# ============================================================
def get_sales_by_year(year_value):
    """
    Gets total sales and total accepted orders for a specific year.
    """

    query = """
        SELECT 
            COALESCE(SUM(total_amount), 0) AS total_sales,
            COUNT(order_id) AS total_orders
        FROM orders
        WHERE order_status = 'accepted'
        AND YEAR(accepted_at) = %s
    """

    return fetch_one(query, (year_value,))


# ============================================================
# SALES SUMMARY: WEEK RANGE
# ============================================================
def get_sales_by_week_range(start_date, end_date):
    """
    Gets total sales and total accepted orders between two dates.
    Usually used for weekly reports.
    """

    query = """
        SELECT 
            COALESCE(SUM(total_amount), 0) AS total_sales,
            COUNT(order_id) AS total_orders
        FROM orders
        WHERE order_status = 'accepted'
        AND DATE(accepted_at) BETWEEN %s AND %s
    """

    return fetch_one(query, (start_date, end_date))


# ============================================================
# REPORT ORDERS
# ============================================================
def get_report_orders(start_date, end_date):
    """
    Gets accepted orders summary for PDF reports.

    This returns one row per order.

    Tables used:
    - orders
    - users
    - payments
    """

    query = """
        SELECT 
            o.order_id,
            COALESCE(u.full_name, 'Unknown') AS cashier_name,
            o.total_amount,
            COALESCE(p.amount_received, 0) AS amount_received,
            COALESCE(p.change_amount, 0) AS change_amount,
            o.accepted_at
        FROM orders o
        LEFT JOIN users u ON o.cashier_id = u.user_id
        LEFT JOIN payments p ON o.order_id = p.order_id
        WHERE o.order_status = 'accepted'
        AND DATE(o.accepted_at) BETWEEN %s AND %s
        ORDER BY o.accepted_at DESC
    """

    return fetch_all(query, (start_date, end_date))


# ============================================================
# REPORT SALES RECORDS
# ============================================================
def get_report_sales_records(start_date, end_date):
    """
    Gets sales records for admin/report.py.

    This returns one row per product item sold.

    Tables used:
    - orders
    - order_items
    - users

    Only accepted orders are included.
    """

    query = """
        SELECT
            oi.order_item_id AS sale_id,
            o.order_id,
            oi.product_name,
            oi.quantity,
            oi.price AS unit_price,
            oi.subtotal,
            COALESCE(u.full_name, 'Unknown') AS cashier_name,
            o.accepted_at AS sale_date
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN users u ON o.cashier_id = u.user_id
        WHERE o.order_status = 'accepted'
        AND DATE(o.accepted_at) BETWEEN %s AND %s
        ORDER BY o.accepted_at DESC, o.order_id DESC, oi.order_item_id ASC
    """

    return fetch_all(query, (start_date, end_date))


# ============================================================
# BEST SELLING PRODUCTS: ALL TIME
# ============================================================
def get_best_selling_products(limit=10):
    """
    Gets best-selling products based on all accepted orders.

    This is used for:
    - All Time best products
    """

    query = """
        SELECT 
            oi.product_id,
            oi.product_name,
            SUM(oi.quantity) AS total_quantity_sold,
            SUM(oi.subtotal) AS total_sales
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'accepted'
        GROUP BY oi.product_id, oi.product_name
        ORDER BY total_quantity_sold DESC, total_sales DESC
        LIMIT %s
    """

    return fetch_all(query, (limit,))


# ============================================================
# BEST SELLING PRODUCTS: MONTH
# ============================================================
def get_best_selling_products_by_month(year_value, month_value, limit=10):
    """
    Gets best-selling products for a selected month.

    Example:
    year_value = 2026
    month_value = 5
    """

    query = """
        SELECT 
            oi.product_id,
            oi.product_name,
            SUM(oi.quantity) AS total_quantity_sold,
            SUM(oi.subtotal) AS total_sales
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'accepted'
        AND YEAR(o.accepted_at) = %s
        AND MONTH(o.accepted_at) = %s
        GROUP BY oi.product_id, oi.product_name
        ORDER BY total_quantity_sold DESC, total_sales DESC
        LIMIT %s
    """

    return fetch_all(query, (year_value, month_value, limit))


# ============================================================
# BEST SELLING PRODUCTS: YEAR
# ============================================================
def get_best_selling_products_by_year(year_value, limit=10):
    """
    Gets best-selling products for a selected year.

    Example:
    year_value = 2026
    """

    query = """
        SELECT 
            oi.product_id,
            oi.product_name,
            SUM(oi.quantity) AS total_quantity_sold,
            SUM(oi.subtotal) AS total_sales
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'accepted'
        AND YEAR(o.accepted_at) = %s
        GROUP BY oi.product_id, oi.product_name
        ORDER BY total_quantity_sold DESC, total_sales DESC
        LIMIT %s
    """

    return fetch_all(query, (year_value, limit))


# ============================================================
# ACTIVITY LOGS
# ============================================================
def get_activity_logs():
    """
    Gets all activity logs.

    Used by report/admin activity logs.
    """

    query = """
        SELECT 
            l.log_id,
            COALESCE(u.full_name, 'Unknown') AS full_name,
            COALESCE(u.role, 'Unknown') AS role,
            l.action_type,
            l.description,
            l.created_at
        FROM activity_logs l
        LEFT JOIN users u ON l.user_id = u.user_id
        ORDER BY l.created_at DESC
    """

    return fetch_all(query)


# ============================================================
# ADMIN DASHBOARD: SALES RECORDS
# ============================================================
def get_dashboard_sales_records(start_date, end_date):
    """
    Gets sales records for adminDashboard.py.

    This is used in the Sales Records table.

    Tables used:
    - orders
    - order_items
    - users

    Only accepted orders are counted as sales.
    """

    query = """
        SELECT 
            o.order_id,
            oi.product_name,
            oi.quantity,
            oi.price AS unit_price,
            oi.subtotal,
            COALESCE(u.full_name, 'Unknown') AS cashier_name,
            DATE(o.accepted_at) AS sale_date
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN users u ON o.cashier_id = u.user_id
        WHERE o.order_status = 'accepted'
        AND DATE(o.accepted_at) BETWEEN %s AND %s
        ORDER BY o.accepted_at DESC, o.order_id DESC
    """

    return fetch_all(query, (start_date, end_date))


# ============================================================
# ADMIN DASHBOARD: PENDING ORDERS COUNT
# ============================================================
def get_pending_orders_count():
    """
    Counts all pending orders for adminDashboard.py.
    """

    query = """
        SELECT COUNT(order_id) AS pending_count
        FROM orders
        WHERE order_status = 'pending'
    """

    result = fetch_one(query)

    if result and result["pending_count"] is not None:
        return result["pending_count"]

    return 0


# ============================================================
# ADMIN DASHBOARD: CALENDAR SALES DATES
# ============================================================
def get_sales_dates_for_month(year, month):
    """
    Gets all days in a selected month that have accepted sales.

    This is used by adminDashboard.py to highlight calendar dates.
    """

    query = """
        SELECT DISTINCT DATE(accepted_at) AS sale_date
        FROM orders
        WHERE order_status = 'accepted'
        AND YEAR(accepted_at) = %s
        AND MONTH(accepted_at) = %s
    """

    rows = fetch_all(query, (year, month))

    sales_days = set()

    for row in rows:
        sale_date = row.get("sale_date")

        if sale_date:
            sales_days.add(sale_date.day)

    return sales_days





def get_receipt_sales_records(start_date, end_date):
    query = """
        SELECT
            oi.order_item_id AS sale_id,
            o.order_id,
            oi.product_name,
            oi.quantity,
            oi.price AS unit_price,
            oi.subtotal,
            COALESCE(u.full_name, 'Unknown Cashier') AS cashier_name,
            o.accepted_at AS sale_date,
            o.total_amount,
            COALESCE(p.amount_received, 0) AS amount_received,
            COALESCE(p.change_amount, 0) AS change_amount
        FROM orders o
        JOIN order_items oi 
            ON o.order_id = oi.order_id
        LEFT JOIN users u 
            ON o.cashier_id = u.user_id
        LEFT JOIN payments p 
            ON o.order_id = p.order_id
        WHERE 
            o.order_status = 'accepted'
            AND DATE(o.accepted_at) BETWEEN %s AND %s
        ORDER BY 
            o.accepted_at DESC,
            o.order_id DESC,
            oi.order_item_id ASC
    """

    return fetch_all(query, (start_date, end_date))
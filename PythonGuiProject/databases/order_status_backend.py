from databases.db import get_connection


def normalize_status(status):
    status = str(status or "").lower().strip()

    if status in ("accepted", "accept", "approved", "approve", "completed", "complete"):
        return "accepted"

    if status in ("cancelled", "canceled", "cancel", "declined", "rejected", "void", "voided"):
        return "cancelled"

    return status


def get_admin_order_status(search="", status_filter="All"):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                o.order_id,
                'Walk-in Customer' AS customer_name,
                COALESCE(u.full_name, 'Cashier') AS cashier_name,
                o.total_amount,
                o.order_status AS status,
                CASE
                    WHEN LOWER(TRIM(o.order_status)) IN ('accepted', 'accept', 'approved', 'approve', 'completed', 'complete')
                        THEN 'Accepted by admin'
                    WHEN LOWER(TRIM(o.order_status)) IN ('cancelled', 'canceled', 'cancel', 'declined', 'rejected', 'void', 'voided')
                        THEN 'Cancelled by admin'
                    ELSE ''
                END AS admin_remarks,
                o.created_at,
                CASE
                    WHEN LOWER(TRIM(o.order_status)) IN ('accepted', 'accept', 'approved', 'approve', 'completed', 'complete')
                        THEN o.accepted_at
                    WHEN LOWER(TRIM(o.order_status)) IN ('cancelled', 'canceled', 'cancel', 'declined', 'rejected', 'void', 'voided')
                        THEN o.cancelled_at
                    ELSE o.created_at
                END AS updated_at
            FROM orders o
            LEFT JOIN users u ON o.cashier_id = u.user_id
            WHERE LOWER(TRIM(o.order_status)) IN (
                'accepted',
                'accept',
                'approved',
                'approve',
                'completed',
                'complete',
                'cancelled',
                'canceled',
                'cancel',
                'declined',
                'rejected',
                'void',
                'voided'
            )
        """

        params = []

        if search:
            query += """
                AND (
                    CAST(o.order_id AS CHAR) LIKE %s
                    OR COALESCE(u.full_name, '') LIKE %s
                    OR COALESCE(o.order_status, '') LIKE %s
                )
            """
            keyword = f"%{search}%"
            params.extend([keyword, keyword, keyword])

        query += """
            ORDER BY 
                CASE
                    WHEN LOWER(TRIM(o.order_status)) IN ('accepted', 'accept', 'approved', 'approve', 'completed', 'complete')
                        THEN o.accepted_at
                    WHEN LOWER(TRIM(o.order_status)) IN ('cancelled', 'canceled', 'cancel', 'declined', 'rejected', 'void', 'voided')
                        THEN o.cancelled_at
                    ELSE o.created_at
                END DESC,
                o.order_id DESC
        """

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        final_rows = []

        for row in rows:
            row["status"] = normalize_status(row.get("status"))

            if status_filter != "All":
                selected_filter = normalize_status(status_filter)

                if row["status"] != selected_filter:
                    continue

            final_rows.append(row)

        return final_rows

    except Exception as e:
        print("Error fetching admin order status:", e)
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_order_status_counts():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                o.order_status AS status
            FROM orders o
            WHERE LOWER(TRIM(o.order_status)) IN (
                'accepted',
                'accept',
                'approved',
                'approve',
                'completed',
                'complete',
                'cancelled',
                'canceled',
                'cancel',
                'declined',
                'rejected',
                'void',
                'voided'
            )
        """)

        rows = cursor.fetchall()

        accepted_count = 0
        cancelled_count = 0

        for row in rows:
            status = normalize_status(row.get("status"))

            if status == "accepted":
                accepted_count += 1

            elif status == "cancelled":
                cancelled_count += 1

        return {
            "accepted_count": accepted_count,
            "cancelled_count": cancelled_count
        }

    except Exception as e:
        print("Error fetching order status counts:", e)
        return {
            "accepted_count": 0,
            "cancelled_count": 0
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def debug_order_statuses():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                order_id,
                order_status,
                created_at,
                accepted_at,
                cancelled_at
            FROM orders
            ORDER BY order_id DESC
        """)

        rows = cursor.fetchall()

        print("\n========== ORDER STATUS DEBUG ==========")

        if not rows:
            print("No orders found in the orders table.")
        else:
            for row in rows:
                print(
                    f"Order ID: {row.get('order_id')} | "
                    f"Status: {row.get('order_status')} | "
                    f"Created: {row.get('created_at')} | "
                    f"Accepted: {row.get('accepted_at')} | "
                    f"Cancelled: {row.get('cancelled_at')}"
                )

        print("========================================\n")

        return rows

    except Exception as e:
        print("Error debugging order statuses:", e)
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
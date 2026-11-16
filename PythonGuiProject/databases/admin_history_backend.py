from databases.db import get_connection


def log_activity(
    current_user=None,
    action_type="UNKNOWN_ACTION",
    target_module="General",
    target_id=None,
    description="No description provided."
):
    """
    Insert activity logs into activity_logs table.

    current_user should be:
    {
        "user_id": 1,
        "username": "admin01",
        "role": "admin"
    }
    """

    conn = None
    cursor = None

    try:
        actor_user_id = None
        actor_username = None
        actor_role = None

        if isinstance(current_user, dict):
            actor_user_id = current_user.get("user_id")
            actor_username = current_user.get("username")
            actor_role = current_user.get("role")

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO activity_logs (
                actor_user_id,
                actor_username,
                actor_role,
                action_type,
                target_module,
                target_id,
                description
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(query, (
            actor_user_id,
            actor_username,
            actor_role,
            action_type,
            target_module,
            str(target_id) if target_id is not None else None,
            description
        ))

        conn.commit()
        return True

    except Exception as e:
        print("Activity log error:", e)
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_activity_logs(
    search="",
    role_filter="All",
    module_filter="All",
    action_filter="All",
    date_from="",
    date_to="",
    limit=500
):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        conditions = []
        params = []

        if search:
            conditions.append("""
                (
                    CAST(log_id AS CHAR) LIKE %s
                    OR actor_username LIKE %s
                    OR actor_role LIKE %s
                    OR action_type LIKE %s
                    OR target_module LIKE %s
                    OR target_id LIKE %s
                    OR description LIKE %s
                )
            """)

            search_value = f"%{search}%"
            params.extend([
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value
            ])

        if role_filter and role_filter != "All":
            conditions.append("actor_role = %s")
            params.append(role_filter)

        if module_filter and module_filter != "All":
            conditions.append("target_module = %s")
            params.append(module_filter)

        if action_filter and action_filter != "All":
            conditions.append("action_type = %s")
            params.append(action_filter)

        if date_from:
            conditions.append("DATE(created_at) >= %s")
            params.append(date_from)

        if date_to:
            conditions.append("DATE(created_at) <= %s")
            params.append(date_to)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                log_id,
                actor_user_id,
                COALESCE(actor_username, 'System/Unknown') AS actor_username,
                COALESCE(actor_role, 'unknown') AS actor_role,
                action_type,
                COALESCE(target_module, 'General') AS target_module,
                COALESCE(target_id, '-') AS target_id,
                description,
                DATE_FORMAT(created_at, '%%Y-%%m-%%d %%h:%%i %%p') AS formatted_created_at,
                created_at
            FROM activity_logs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s
        """

        params.append(limit)

        cursor.execute(query, tuple(params))
        return cursor.fetchall()

    except Exception as e:
        print("Get activity logs error:", e)
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_history_summary():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS total_logs FROM activity_logs")
        total_logs = cursor.fetchone()["total_logs"]

        cursor.execute("""
            SELECT COUNT(*) AS today_logs
            FROM activity_logs
            WHERE DATE(created_at) = CURDATE()
        """)
        today_logs = cursor.fetchone()["today_logs"]

        cursor.execute("""
            SELECT COUNT(*) AS admin_logs
            FROM activity_logs
            WHERE actor_role = 'admin'
        """)
        admin_logs = cursor.fetchone()["admin_logs"]

        cursor.execute("""
            SELECT COUNT(*) AS cashier_logs
            FROM activity_logs
            WHERE actor_role = 'cashier'
        """)
        cashier_logs = cursor.fetchone()["cashier_logs"]

        cursor.execute("""
            SELECT COUNT(*) AS inventory_logs
            FROM activity_logs
            WHERE actor_role = 'inventory'
        """)
        inventory_logs = cursor.fetchone()["inventory_logs"]

        return {
            "total_logs": total_logs,
            "today_logs": today_logs,
            "admin_logs": admin_logs,
            "cashier_logs": cashier_logs,
            "inventory_logs": inventory_logs
        }

    except Exception as e:
        print("Get history summary error:", e)
        return {
            "total_logs": 0,
            "today_logs": 0,
            "admin_logs": 0,
            "cashier_logs": 0,
            "inventory_logs": 0
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_filter_options():
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT DISTINCT target_module
            FROM activity_logs
            WHERE target_module IS NOT NULL
              AND target_module != ''
            ORDER BY target_module ASC
        """)
        modules = [row["target_module"] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT action_type
            FROM activity_logs
            WHERE action_type IS NOT NULL
              AND action_type != ''
            ORDER BY action_type ASC
        """)
        actions = [row["action_type"] for row in cursor.fetchall()]

        return {
            "modules": modules,
            "actions": actions
        }

    except Exception as e:
        print("Get filter options error:", e)
        return {
            "modules": [],
            "actions": []
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
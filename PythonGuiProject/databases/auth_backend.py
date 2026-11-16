"""
databases/auth_backend.py

This file handles all user/account-related database actions.

Used by:
- logins/login.py
- admin/manageAccounts.py

Flow:
UI file
→ auth_backend.py
→ db.py
→ MySQL
"""

# ============================================================
# IMPORT DATABASE HELPERS
# ============================================================
from databases.db import fetch_one, fetch_all, execute_query, execute_insert
from databases.log_backend import add_log


# ============================================================
# LOGIN USER
# ============================================================
def login_user(username, password):
    """
    Checks if the username and password exist in the database.

    Only active users can log in.

    Allowed roles:
    - admin
    - cashier
    - inventory
    """

    print("Checking user in database...")

    query = """
        SELECT 
            user_id, 
            full_name, 
            username, 
            role, 
            status
        FROM users
        WHERE username = %s 
        AND password = %s 
        AND status = 'active'
        AND role IN ('admin', 'cashier', 'inventory')
        LIMIT 1
    """

    return fetch_one(query, (username, password))


# ============================================================
# GET ALL USERS
# ============================================================
def get_all_users():
    """
    Gets all users from the users table.

    This is used by admin/manageAccounts.py.
    """

    query = """
        SELECT 
            user_id, 
            full_name, 
            username, 
            password,
            role, 
            status, 
            created_at
        FROM users
        ORDER BY created_at DESC, user_id DESC
    """

    return fetch_all(query)


# ============================================================
# GET USERS BY ROLE
# ============================================================
def get_users_by_role(role):
    """
    Gets users by role.

    Example:
    role = cashier
    role = inventory
    """

    query = """
        SELECT 
            user_id, 
            full_name, 
            username, 
            password,
            role, 
            status, 
            created_at
        FROM users
        WHERE role = %s
        ORDER BY created_at DESC, user_id DESC
    """

    return fetch_all(query, (role,))


# ============================================================
# GET USER BY ID
# ============================================================
def get_user_by_id(user_id):
    """
    Gets one user using user_id.
    """

    query = """
        SELECT 
            user_id, 
            full_name, 
            username, 
            password,
            role, 
            status, 
            created_at
        FROM users
        WHERE user_id = %s
        LIMIT 1
    """

    return fetch_one(query, (user_id,))


# ============================================================
# GET USER BY USERNAME
# ============================================================
def get_user_by_username(username):
    """
    Gets one user using username.

    Used to check duplicate usernames.
    """

    query = """
        SELECT 
            user_id, 
            full_name, 
            username, 
            password,
            role, 
            status, 
            created_at
        FROM users
        WHERE username = %s
        LIMIT 1
    """

    return fetch_one(query, (username,))


# ============================================================
# CHECK IF USERNAME EXISTS
# ============================================================
def username_exists(username, exclude_user_id=None):
    """
    Checks if a username already exists.

    exclude_user_id is used when editing.
    Example:
    If you are editing user ID 5, it ignores user ID 5
    so the user can keep their own username.
    """

    if exclude_user_id:
        query = """
            SELECT user_id
            FROM users
            WHERE username = %s
            AND user_id != %s
            LIMIT 1
        """
        result = fetch_one(query, (username, exclude_user_id))
    else:
        query = """
            SELECT user_id
            FROM users
            WHERE username = %s
            LIMIT 1
        """
        result = fetch_one(query, (username,))

    return result is not None


# ============================================================
# ADD USER
# ============================================================
def add_user(full_name, username, password, role, admin_id=None):
    """
    Adds a new user account.

    Used by:
    - admin/manageAccounts.py

    Allowed roles here:
    - cashier
    - inventory

    Admin accounts should not be created from Manage Accounts.
    """

    # Prevent invalid role.
    if role not in ("cashier", "inventory"):
        return None

    # Prevent duplicate username.
    if username_exists(username):
        return None

    query = """
        INSERT INTO users (full_name, username, password, role, status)
        VALUES (%s, %s, %s, %s, 'active')
    """

    user_id = execute_insert(query, (full_name, username, password, role))

    if user_id:
        add_log(
            admin_id,
            "ADD_USER",
            f"Added new {role} account: {username}"
        )

    return user_id


# ============================================================
# UPDATE USER
# ============================================================
def update_user(user_id, full_name, username, password, role, status="active", admin_id=None):
    """
    Updates an existing user account.

    Used by:
    - admin/manageAccounts.py

    It updates:
    - full name
    - username
    - password
    - role
    - status
    """

    # Prevent invalid role.
    if role not in ("cashier", "inventory"):
        return False

    # Prevent invalid status.
    if status not in ("active", "inactive"):
        return False

    # Prevent duplicate username.
    if username_exists(username, exclude_user_id=user_id):
        return False

    query = """
        UPDATE users
        SET full_name = %s,
            username = %s,
            password = %s,
            role = %s,
            status = %s
        WHERE user_id = %s
        AND role IN ('cashier', 'inventory')
    """

    result = execute_query(
        query,
        (full_name, username, password, role, status, user_id)
    )

    if result:
        add_log(
            admin_id,
            "UPDATE_USER",
            f"Updated account ID {user_id}: {username}"
        )

    return result


# ============================================================
# UPDATE USER STATUS
# ============================================================
def update_user_status(user_id, status, admin_id=None):
    """
    Updates user status.

    status can be:
    - active
    - inactive
    """

    if status not in ("active", "inactive"):
        return False

    query = """
        UPDATE users
        SET status = %s
        WHERE user_id = %s
        AND role IN ('cashier', 'inventory')
    """

    result = execute_query(query, (status, user_id))

    if result:
        add_log(
            admin_id,
            "UPDATE_USER_STATUS",
            f"Changed user ID {user_id} status to {status}"
        )

    return result


# ============================================================
# DELETE USER / DEACTIVATE USER
# ============================================================
def delete_user(user_id, admin_id=None):
    """
    Soft deletes a user account.

    It does not permanently remove the account.
    It only changes status to inactive.

    This is safer because old orders and logs can still reference the user.
    """

    query = """
        UPDATE users
        SET status = 'inactive'
        WHERE user_id = %s
        AND role IN ('cashier', 'inventory')
    """

    result = execute_query(query, (user_id,))

    if result:
        add_log(
            admin_id,
            "DELETE_USER",
            f"Deactivated user ID {user_id}"
        )

    return result


# ============================================================
# RESTORE USER
# ============================================================
def restore_user(user_id, admin_id=None):
    """
    Restores an inactive cashier/inventory account.
    """

    query = """
        UPDATE users
        SET status = 'active'
        WHERE user_id = %s
        AND role IN ('cashier', 'inventory')
    """

    result = execute_query(query, (user_id,))

    if result:
        add_log(
            admin_id,
            "RESTORE_USER",
            f"Restored user ID {user_id}"
        )

    return result
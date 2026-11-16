import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "pos_inventory_system",
    "use_pure": True
}


def get_connection():
    try:
        print("Connecting to MySQL...")

        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            print("MySQL connected successfully.")

        return connection

    except Error as e:
        print("Database connection error:", e)
        return None

    except Exception as e:
        print("Unexpected database error:", e)
        return None


def fetch_all(query, params=None):
    connection = get_connection()

    if connection is None:
        print("No database connection.")
        return []

    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        return result

    except Error as e:
        print("Fetch error:", e)
        return []

    except Exception as e:
        print("Unexpected fetch error:", e)
        return []

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def fetch_one(query, params=None):
    connection = get_connection()

    if connection is None:
        print("No database connection.")
        return None

    cursor = None

    try:
        print("Running query...")
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchone()
        print("Query result:", result)
        return result

    except Error as e:
        print("Fetch one error:", e)
        return None

    except Exception as e:
        print("Unexpected fetch one error:", e)
        return None

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def execute_query(query, params=None):
    connection = get_connection()

    if connection is None:
        print("No database connection.")
        return False

    cursor = None

    try:
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        connection.commit()
        return True

    except Error as e:
        print("Execute error:", e)
        connection.rollback()
        return False

    except Exception as e:
        print("Unexpected execute error:", e)
        connection.rollback()
        return False

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def execute_insert(query, params=None):
    connection = get_connection()

    if connection is None:
        print("No database connection.")
        return None

    cursor = None

    try:
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        connection.commit()
        return cursor.lastrowid

    except Error as e:
        print("Insert error:", e)
        connection.rollback()
        return None

    except Exception as e:
        print("Unexpected insert error:", e)
        connection.rollback()
        return None

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
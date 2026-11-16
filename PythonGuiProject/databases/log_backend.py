from databases.db import execute_query


def add_log(user_id, action_type, description):
    query = """
        INSERT INTO activity_logs (user_id, action_type, description)
        VALUES (%s, %s, %s)
    """
    return execute_query(query, (user_id, action_type, description))
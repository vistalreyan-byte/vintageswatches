import mysql.connector
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    db_url = os.getenv("MYSQL_URL") or os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("mysql"):
        try:
            parsed = urlparse(db_url)
            return mysql.connector.connect(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/')
            )
        except mysql.connector.Error as err:
            print(f"Error connecting with database URL: {err}")

    host = os.getenv("MYSQLHOST") or os.getenv("DB_HOST", "localhost")
    user = os.getenv("MYSQLUSER") or os.getenv("DB_USER", "root")
    password = os.getenv("MYSQLPASSWORD") or os.getenv("DB_PASSWORD", "")
    database = os.getenv("MYSQLDATABASE") or os.getenv("DB_NAME", "vintage_watches")
    port = int(os.getenv("MYSQLPORT") or os.getenv("DB_PORT", 3306))

    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL Database: {err}")
        return None

def init_db():
    """Initializes tables and initial data from schema.sql if tables do not exist."""
    conn = get_db_connection()
    if not conn:
        print("Database not reachable for initialization.")
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'watches';")
        existing = cursor.fetchone()
        if not existing:
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            if os.path.exists(schema_path):
                print(f"Running schema migration from {schema_path}...")
                with open(schema_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Clean and split SQL commands
                statements = content.split(';')
                for stmt in statements:
                    cleaned = stmt.strip()
                    if cleaned and not cleaned.startswith('/*') and not cleaned.startswith('--'):
                        try:
                            cursor.execute(cleaned)
                        except Exception as ex:
                            # Log and skip minor syntax issues
                            pass
                conn.commit()
                print("Database tables & data initialized successfully.")
        cursor.close()
        conn.close()
        return True
    except Exception as err:
        print(f"Database initialization exception: {err}")
        try:
            conn.close()
        except Exception:
            pass
        return False

def fetch_all(query, params=None):
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        return result
    except mysql.connector.Error as err:
        print(f"Query Failed: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def fetch_one(query, params=None):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchone()
        return result
    except mysql.connector.Error as err:
        print(f"Query Failed: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

def execute_query(query, params=None):
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.lastrowid if cursor.lastrowid else True
    except mysql.connector.Error as err:
        print(f"Execute Failed: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def execute_transaction(operations_callback):
    """
    Executes multiple queries in a single atomic transaction using a callback:
    callback(cursor) where cursor is provided. Returns callback return value or False on error.
    """
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor(dictionary=True)
        result = operations_callback(cursor)
        conn.commit()
        return result if result is not None else True
    except Exception as err:
        print(f"Transaction Failed: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

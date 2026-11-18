import os
import sqlite3
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# Determine if we should use MySQL or SQLite
def use_mysql():
    if os.getenv("RENDER"):
        return bool(os.getenv("MYSQL_URL") or os.getenv("DATABASE_URL") or (os.getenv("DB_HOST") and os.getenv("DB_HOST") != "localhost"))
    return bool(os.getenv("MYSQL_URL") or os.getenv("DATABASE_URL") or os.getenv("DB_HOST") or os.getenv("MYSQLHOST"))

def get_mysql_connection():
    try:
        import mysql.connector
        db_url = os.getenv("MYSQL_URL") or os.getenv("DATABASE_URL")
        if db_url and db_url.startswith("mysql"):
            parsed = urlparse(db_url)
            return mysql.connector.connect(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/')
            )

        host = os.getenv("MYSQLHOST") or os.getenv("DB_HOST", "localhost")
        user = os.getenv("MYSQLUSER") or os.getenv("DB_USER", "root")
        password = os.getenv("MYSQLPASSWORD") or os.getenv("DB_PASSWORD", "")
        database = os.getenv("MYSQLDATABASE") or os.getenv("DB_NAME", "vintage_watches")
        port = int(os.getenv("MYSQLPORT") or os.getenv("DB_PORT", 3306))

        return mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            connection_timeout=2
        )
    except Exception as err:
        print(f"MySQL connection failed: {err}. Falling back to SQLite.")
        return None

def get_sqlite_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'vintage_watches.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Register MySQL compatible functions
    conn.create_function("CURDATE", 0, lambda: datetime.now().strftime("%Y-%m-%d"))
    conn.create_function("NOW", 0, lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    conn.create_function("MONTH", 1, lambda d: int(str(d).split('-')[1]) if d and '-' in str(d) else 1)
    conn.create_function("YEAR", 1, lambda d: int(str(d).split('-')[0]) if d and '-' in str(d) else datetime.now().year)
    return conn

def get_db_connection():
    if use_mysql():
        conn = get_mysql_connection()
        if conn:
            return conn
    return get_sqlite_connection()

def is_sqlite_conn(conn):
    return isinstance(conn, sqlite3.Connection)

def prepare_query(query, is_sqlite):
    if is_sqlite:
        return query.replace('%s', '?')
    return query

def init_db():
    """Seeds tables and ensures watch images and descriptions are linked."""
    conn = get_db_connection()
    if not conn:
        return False

    if is_sqlite_conn(conn):
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(watches)")
            cols = [r[1] for r in cursor.fetchall()]
            if 'image' not in cols:
                cursor.execute("ALTER TABLE watches ADD COLUMN image TEXT")
            if 'description' not in cols:
                cursor.execute("ALTER TABLE watches ADD COLUMN description TEXT")

            image_map = {
                1: ('rolex_submariner_116610ln.jpg', 'Iconic luxury diving watch with black Cerachrom bezel and robust Oystersteel bracelet.'),
                2: ('omega_seamaster_21030422001001.jpg', 'Legendary maritime timepiece with laser-engraved wave dial and Co-Axial Master Chronometer.'),
                3: ('seiko_presage_srpb43j1.jpg', 'Elegant dress watch inspired by the glamour of cocktail lounges with radiant sunburst dial.'),
                4: ('tissot_prx_t1374071105100.jpg', 'Retro 1970s integrated bracelet sport watch powered by an 80-hour Powermatic movement.'),
                5: ('citizen_ca0690_88e.jpg', 'Solar-powered aviator chronograph with perpetual Eco-Drive technology and compass bezel.'),
                6: ('casio_gg1000_1a3.jpg', 'Tough Master of G mud-resistant tactical timepiece with Twin Sensor compass and thermometer.'),
                7: ('orient_fac08003a0.jpg', 'Classic vintage dress watch with domed crystal, roman numerals, and exhibition caseback.'),
                8: ('longines_l37814566.jpg', 'High-performance Swiss diver with polished ceramic bezel and 300-meter water resistance.'),
                9: ('hamilton_h70455553.jpg', 'Authentic military heritage field watch featuring a bold dial and rugged leather strap.'),
                10: ('tag_heuer_war211a_fc6180.jpg', 'Prestige Swiss motor-racing inspired automatic watch with clean black dial and alligator strap.')
            }
            for w_id, (img, desc) in image_map.items():
                cursor.execute("UPDATE watches SET image = ?, description = ? WHERE watch_id = ?", (img, desc, w_id))
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Auto-migration error: {e}")
        finally:
            conn.close()
        return True

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
                for stmt in content.split(';'):
                    cleaned = stmt.strip()
                    if cleaned and not cleaned.startswith('/*') and not cleaned.startswith('--'):
                        try:
                            cursor.execute(cleaned)
                        except Exception:
                            pass
                conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as err:
        print(f"Init DB error: {err}")
        try: conn.close()
        except: pass
        return False

def fetch_all(query, params=None):
    conn = get_db_connection()
    if not conn: return []
    sqlite = is_sqlite_conn(conn)
    q = prepare_query(query, sqlite)
    try:
        if sqlite:
            cursor = conn.cursor()
            cursor.execute(q, params or ())
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        else:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(q, params or ())
            return cursor.fetchall()
    except Exception as err:
        print(f"Query Failed: {err}")
        return []
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass

def fetch_one(query, params=None):
    conn = get_db_connection()
    if not conn: return None
    sqlite = is_sqlite_conn(conn)
    q = prepare_query(query, sqlite)
    try:
        if sqlite:
            cursor = conn.cursor()
            cursor.execute(q, params or ())
            row = cursor.fetchone()
            return dict(row) if row else None
        else:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(q, params or ())
            return cursor.fetchone()
    except Exception as err:
        print(f"Query Failed: {err}")
        return None
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass

def execute_query(query, params=None):
    conn = get_db_connection()
    if not conn: return False
    sqlite = is_sqlite_conn(conn)
    q = prepare_query(query, sqlite)
    try:
        cursor = conn.cursor()
        cursor.execute(q, params or ())
        conn.commit()
        return cursor.lastrowid if cursor.lastrowid else True
    except Exception as err:
        print(f"Execute Failed: {err}")
        try: conn.rollback()
        except: pass
        return False
    finally:
        try: cursor.close()
        except: pass
        try: conn.close()
        except: pass

def execute_transaction(operations_callback):
    conn = get_db_connection()
    if not conn: return False
    sqlite = is_sqlite_conn(conn)
    try:
        if sqlite:
            class SqliteCursorWrapper:
                def __init__(self, cur):
                    self.cur = cur
                def execute(self, q, p=None):
                    return self.cur.execute(prepare_query(q, True), p or ())
                def fetchone(self):
                    r = self.cur.fetchone()
                    return dict(r) if r else None
                def fetchall(self):
                    return [dict(r) for r in self.cur.fetchall()]
                @property
                def lastrowid(self):
                    return self.cur.lastrowid

            cursor = SqliteCursorWrapper(conn.cursor())
        else:
            cursor = conn.cursor(dictionary=True)

        result = operations_callback(cursor)
        conn.commit()
        return result if result is not None else True
    except Exception as err:
        print(f"Transaction Failed: {err}")
        try: conn.rollback()
        except: pass
        return False
    finally:
        try: conn.close()
        except: pass

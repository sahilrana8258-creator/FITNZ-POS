# File: FITNZ/database.py
import mysql.connector
from datetime import date
import re # Needed for ID parsing

from .models.customer import Customer, BronzeMember, SilverMember, GoldMember, StudentMember
from .models.employee import Employee
from .models.product import Product
from .models.sales import Sale

# CONFIGURATION
SERVER_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Apple@2310' # <--- CHECK YOUR PASSWORD HERE
}
DB_NAME = 'fitnz'

def get_db_connection():
    config = SERVER_CONFIG.copy()
    config['database'] = DB_NAME
    return mysql.connector.connect(**config)

def setup_database():
    try:
        server_conn = mysql.connector.connect(**SERVER_CONFIG)
        server_cursor = server_conn.cursor()
        server_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        server_conn.close()
    except Exception as e:
        print(f"DB Setup Error: {e}")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(50) UNIQUE, 
            username VARCHAR(50) UNIQUE, password VARCHAR(255), role VARCHAR(50), 
            name VARCHAR(100), contact VARCHAR(100), address VARCHAR(255), 
            membership_level VARCHAR(50) DEFAULT 'Standard', loyalty_points INT DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id VARCHAR(50) PRIMARY KEY, name VARCHAR(100), 
            price DECIMAL(10, 2), stock INT, description TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INT AUTO_INCREMENT PRIMARY KEY, customer_id VARCHAR(50), 
            employee_id VARCHAR(50), sale_date DATE, delivery_date DATE, total_amount DECIMAL(10, 2),
            FOREIGN KEY (customer_id) REFERENCES users (user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sale_items (
            id INT AUTO_INCREMENT PRIMARY KEY, sale_id INT, product_id VARCHAR(50), 
            quantity INT, price_at_sale DECIMAL(10, 2),
            FOREIGN KEY (sale_id) REFERENCES sales (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        users = [
            ('E001', 'dev', 'dev123', 'Developer', 'Om Patel', 'dev@fit.nz'),
            ('E002', 'manager', 'man123', 'Manager', 'Jane Doe', 'jane@fit.nz'),
            ('E003', 'emp', 'emp123', 'Employee', 'John Smith', 'john@fit.nz'),
            ('C101', 'alice', 'alice123', 'Customer', 'Alice Johnson', 'alice@example.com')
        ]
        sql = "INSERT INTO users (user_id, username, password, role, name, contact) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.executemany(sql, users)
    
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        prods = [
            ('P1001','Resistance Bands',35.00,50, 'Set of 5 latex bands.'), 
            ('P1002','Yoga Mat',45.50,30, 'Non-slip yoga mat.'), 
            ('P1003','Dumbbell Set',75.00,0, 'Pair of 5kg dumbbells.'), 
            ('P1004','Whey Protein',90.00,40, 'Gold Standard Whey.')
        ]
        sql = "INSERT INTO products (id, name, price, stock, description) VALUES (%s, %s, %s, %s, %s)"
        cursor.executemany(sql, prods)

    conn.commit()
    conn.close()

# Helper functions
def _create_user(row):
    if not row: return None
    if row['role'] == 'Customer':
        c = Customer(row['user_id'], row['name'], row['contact'], row['username'], row['password'])
        c.address = row['address']; c.loyalty_points = row['loyalty_points']
        lvl = row['membership_level']
        if lvl == "Bronze": return BronzeMember(c)
        if lvl == "Silver": return SilverMember(c)
        if lvl == "Gold": return GoldMember(c)
        if lvl == "Student": return StudentMember(c)
        return c
    return Employee(row['user_id'], row['name'], row['role'], row['username'], row['password'])

def authenticate_user(username, password, role):
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s AND role=%s", (username, password, role))
    row = cursor.fetchone(); conn.close()
    return _create_user(row)

def get_user_by_id(uid):
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE user_id=%s", (uid,))
    row = cursor.fetchone(); conn.close()
    return _create_user(row)

def add_user(name, contact, username, password, role, address):
    conn = get_db_connection(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        uid = f"{'C' if role=='Customer' else 'E'}{cursor.fetchone()[0]+101}"
        cursor.execute("INSERT INTO users (user_id, username, password, role, name, contact, address) VALUES (%s,%s,%s,%s,%s,%s,%s)", 
                       (uid, username, password, role, name, contact, address))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def get_all_products():
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products"); rows = cursor.fetchall(); conn.close()
    return [Product(r['id'], r['name'], float(r['price']), r['stock'], r['description']) for r in rows]

def get_product_by_id(pid):
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE id=%s", (pid,)); row = cursor.fetchone(); conn.close()
    if row: return Product(row['id'], row['name'], float(row['price']), row['stock'], row['description'])
    return None

def update_product_stock(pid, qty):
    conn = get_db_connection(); conn.cursor().execute("UPDATE products SET stock=%s WHERE id=%s", (qty, pid))
    conn.commit(); conn.close(); return True

# --- MODIFIED: Auto-generate ID ---
def add_product(name, price, stock, desc):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Find the highest current Product ID to generate the next one
        cursor.execute("SELECT id FROM products ORDER BY id DESC LIMIT 1")
        last_id = cursor.fetchone()
        
        if last_id:
            # Extract numbers from "P1001" -> 1001
            last_num = int(re.search(r'\d+', last_id[0]).group())
            new_id = f"P{last_num + 1}"
        else:
            new_id = "P1001"

        cursor.execute("INSERT INTO products (id, name, price, stock, description) VALUES (%s,%s,%s,%s,%s)", (new_id, name, price, stock, desc))
        conn.commit(); return True
    except Exception as e: 
        print(e)
        return False
    finally: conn.close()

# --- NEW: Update Product ---
def update_product(pid, name, price, stock, desc):
    conn = get_db_connection()
    try:
        conn.cursor().execute("UPDATE products SET name=%s, price=%s, stock=%s, description=%s WHERE id=%s", (name, price, stock, desc, pid))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def search_products(query):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT * FROM products WHERE name LIKE %s OR description LIKE %s"
    val = (f"%{query}%", f"%{query}%")
    cursor.execute(sql, val)
    rows = cursor.fetchall()
    conn.close()
    return [Product(r['id'], r['name'], float(r['price']), r['stock'], r['description']) for r in rows]

def delete_product(pid):
    conn = get_db_connection()
    try:
        conn.cursor().execute("DELETE FROM sale_items WHERE product_id=%s", (pid,))
        conn.cursor().execute("DELETE FROM products WHERE id=%s", (pid,))
        conn.commit(); return True
    except: return False
    finally: conn.close()

def process_sale(cust, cart, points, student, date):
    conn = get_db_connection(); cursor = conn.cursor()
    try:
        total = sum(i.price for i in cart)
        final = total - (total * (0.2 if student else cust.get_discount_rate())) - (points * 0.1)
        new_points = (cust.loyalty_points - points) + int(final // 10)
        cursor.execute("UPDATE users SET loyalty_points=%s WHERE user_id=%s", (new_points, cust._customer_id))
        cursor.execute("INSERT INTO sales (customer_id, sale_date, delivery_date, total_amount) VALUES (%s,%s,%s,%s)", (cust._customer_id, date.today(), date, final))
        sid = cursor.lastrowid
        for i in cart:
            cursor.execute("INSERT INTO sale_items (sale_id, product_id, quantity, price_at_sale) VALUES (%s,%s,1,%s)", (sid, i.product_id, i.price))
            cursor.execute("UPDATE products SET stock=stock-1 WHERE id=%s", (i.product_id,))
        conn.commit()
    finally: conn.close()

def get_all_users():
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users"); rows = cursor.fetchall(); conn.close()
    return [_create_user(r) for r in rows]

def delete_user_by_id(uid):
    conn = get_db_connection(); conn.cursor().execute("DELETE FROM users WHERE user_id=%s", (uid,))
    conn.commit(); conn.close(); return True

def update_customer_membership(uid, lvl):
    conn = get_db_connection(); conn.cursor().execute("UPDATE users SET membership_level=%s WHERE user_id=%s", (lvl, uid))
    conn.commit(); conn.close(); return True

def upgrade_to_student_membership(uid):
    conn = get_db_connection(); conn.cursor().execute("UPDATE users SET membership_level='Student' WHERE user_id=%s", (uid,))
    conn.commit(); conn.close(); return True

def get_sales_for_customer(uid):
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM sales WHERE customer_id=%s", (uid,)); rows = cursor.fetchall(); conn.close()
    return rows

def get_all_sales():
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT s.id, s.sale_date, s.total_amount, u.name FROM sales s JOIN users u ON s.customer_id=u.user_id")
    rows = cursor.fetchall(); conn.close(); return rows

def get_items_for_sale(sid):
    conn = get_db_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT p.name, si.price_at_sale FROM sale_items si JOIN products p ON si.product_id=p.id WHERE si.sale_id=%s", (sid,))
    rows = cursor.fetchall(); conn.close(); return rows

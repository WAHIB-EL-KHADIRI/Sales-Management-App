import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
import pandas as pd
from datetime import datetime
import io
import requests
from PIL import Image

def init_db():
    conn = sqlite3.connect('sales_management.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    name TEXT,
                    password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    price REAL,
                    quantity INTEGER,
                    category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY,
                    product_id INTEGER,
                    quantity INTEGER,
                    total_price REAL,
                    date TEXT,
                    FOREIGN KEY (product_id) REFERENCES products (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS credits (
                    id INTEGER PRIMARY KEY,
                    customer_name TEXT,
                    product_id INTEGER,
                    quantity INTEGER,
                    total_price REAL,
                    date TEXT,
                    paid INTEGER,
                    FOREIGN KEY (product_id) REFERENCES products (id))''')
    # إضافة مستخدم افتراضي إذا لم يكن موجوداً
    c.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if not c.fetchone():
        hashed_password = stauth.Hasher.hash("password123")
        c.execute("INSERT INTO users (username, name, password) VALUES (?, ?, ?)",
                  ("admin", "Administrator", hashed_password))
    conn.commit()
    conn.close()

init_db()

def load_users():
    conn = sqlite3.connect('sales_management.db')
    c = conn.cursor()
    c.execute("SELECT username, name, password FROM users")
    users_data = c.fetchall()
    conn.close()
    users = {}
    for username, name, password in users_data:
        users[username] = {"name": name, "password": password}
    return users

users = load_users()

authenticator = stauth.Authenticate(
    credentials={"usernames": users},
    cookie_name="sales_app",
    key="sales_key",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login("تسجيل الدخول", "main")

if authentication_status == False:
    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
elif authentication_status == None:
    st.warning("يرجى إدخال اسم المستخدم وكلمة المرور")
elif authentication_status:
    st.success(f"مرحبا {name}!")
    authenticator.logout("تسجيل خروج", "sidebar")

    # وظائف قاعدة البيانات
    def add_user(username, name, password):
        hashed_password = stauth.Hasher.hash(password)
        conn = sqlite3.connect('sales_management.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, name, password) VALUES (?, ?, ?)",
                      (username, name, hashed_password))
            conn.commit()
            st.success("تم إضافة المستخدم")
        except sqlite3.IntegrityError:
            st.error("اسم المستخدم موجود بالفعل")
        conn.close()

    def get_users():
        conn = sqlite3.connect('sales_management.db')
        df = pd.read_sql_query("SELECT id, username, name FROM users", conn)
        conn.close()
        return df
    def add_product(name, price, quantity, category):
        conn = sqlite3.connect('sales_management.db')
        c = conn.cursor()
        c.execute("INSERT INTO products (name, price, quantity, category) VALUES (?, ?, ?, ?)",
                  (name, price, quantity, category))
        conn.commit()
        conn.close()

    def get_products():
        conn = sqlite3.connect('sales_management.db')
        df = pd.read_sql_query("SELECT * FROM products", conn)
        conn.close()
        return df

    def add_sale(product_name, quantity, total_price):
        conn = sqlite3.connect('sales_management.db')
        c = conn.cursor()
        c.execute("SELECT id, quantity FROM products WHERE name = ?", (product_name,))
        product = c.fetchone()
        if product:
            product_id, available_qty = product
            if quantity <= available_qty:
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO sales (product_id, quantity, total_price, date) VALUES (?, ?, ?, ?)",
                          (product_id, quantity, total_price, date))
                c.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (quantity, product_id))
                conn.commit()
            else:
                st.error("الكمية غير متوفرة")
        else:
            # إضافة منتج جديد
            price = total_price / quantity if quantity > 0 else 0
            c.execute("INSERT INTO products (name, price, quantity, category) VALUES (?, ?, ?, ?)",
                      (product_name, price, 1000, "عام"))
            conn.commit()
            product_id = c.lastrowid
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO sales (product_id, quantity, total_price, date) VALUES (?, ?, ?, ?)",
                      (product_id, quantity, total_price, date))
            c.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (quantity, product_id))
            conn.commit()
        conn.close()

    def get_sales(product_filter=None):
        conn = sqlite3.connect('sales_management.db')
        query = """
            SELECT sales.id, products.name, sales.quantity, sales.total_price, sales.date
            FROM sales
            JOIN products ON sales.product_id = products.id
        """
        if product_filter:
            query += " WHERE products.name LIKE ?"
            df = pd.read_sql_query(query, conn, params=(f"%{product_filter}%",))
        else:
            df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def add_credit(customer_name, product_name, quantity, total_price, paid):
        conn = sqlite3.connect('sales_management.db')
        c = conn.cursor()
        c.execute("SELECT id FROM products WHERE name = ?", (product_name,))
        product = c.fetchone()
        if product:
            product_id = product[0]
        else:
            # إضافة منتج جديد
            price = total_price / quantity if quantity > 0 else 0
            c.execute("INSERT INTO products (name, price, quantity, category) VALUES (?, ?, ?, ?)",
                      (product_name, price, 1000, "عام"))
            conn.commit()
            product_id = c.lastrowid
        date = datetime.now().strftime("%Y-%m-%d")
        c.execute("INSERT INTO credits (customer_name, product_id, quantity, total_price, date, paid) VALUES (?, ?, ?, ?, ?, ?)",
                  (customer_name, product_id, quantity, total_price, date, paid))
        conn.commit()
        conn.close()

    def get_credits():
        conn = sqlite3.connect('sales_management.db')
        df = pd.read_sql_query("""
            SELECT credits.id, credits.customer_name, products.name, credits.quantity, credits.total_price, credits.date, credits.paid
            FROM credits
            LEFT JOIN products ON credits.product_id = products.id
            ORDER BY credits.date DESC
        """, conn)
        conn.close()
        return df

    # واجهة Streamlit
    st.set_page_config(page_title="إدارة المبيعات", layout="wide")

    st.title("نظام إدارة المبيعات")

    tab1, tab2, tab3, tab4 = st.tabs(["المنتجات", "المبيعات", "الائتمان", "المستخدمين"])

    with tab1:
        st.header("إدارة المنتجات")
        with st.form("add_product"):
            name = st.text_input("اسم المنتج")
            price = st.number_input("السعر", min_value=0.0)
            quantity = st.number_input("الكمية", min_value=0)
            category = st.text_input("الفئة")
            submitted = st.form_submit_button("إضافة منتج")
            if submitted:
                add_product(name, price, quantity, category)
                st.success("تم إضافة المنتج")

        st.subheader("قائمة المنتجات")
        products_df = get_products()
        st.dataframe(products_df)

    with tab2:
        st.header("إدارة المبيعات")
        with st.form("add_sale"):
            product_name = st.text_input("اسم المنتج")
            quantity = st.number_input("الكمية", min_value=1)
            total_price = st.number_input("السعر الإجمالي", min_value=0.0)
            submitted = st.form_submit_button("إضافة بيع")
            if submitted:
                add_sale(product_name, quantity, total_price)
                st.success("تم إضافة البيع")

        st.subheader("البحث في المبيعات")
        product_filter = st.text_input("ابحث عن منتج")
        if st.button("بحث"):
            sales_df = get_sales(product_filter)
        else:
            sales_df = get_sales()
        st.dataframe(sales_df)

    with tab4:
        st.header("إدارة المستخدمين")
        with st.form("add_user"):
            username = st.text_input("اسم المستخدم")
            name = st.text_input("الاسم الكامل")
            password = st.text_input("كلمة المرور", type="password")
            submitted = st.form_submit_button("إضافة مستخدم")
            if submitted:
                add_user(username, name, password)

        st.subheader("قائمة المستخدمين")
        users_df = get_users()
        st.dataframe(users_df)
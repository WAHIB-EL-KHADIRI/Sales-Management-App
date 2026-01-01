import streamlit as st
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
    conn.commit()
    conn.close()

init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    password = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if password == "T9!mA4#qL2@x":
            st.session_state.logged_in = True
            st.success("تم الدخول بنجاح!")
            st.rerun()
        else:
            st.error("كلمة مرور خاطئة")
else:

    # وظائف قاعدة البيانات
    def add_user(username, name, password):
        conn = sqlite3.connect('sales_management.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, name, password) VALUES (?, ?, ?)",
                      (username, name, password))
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

    def delete_user(user_id):
        conn = sqlite3.connect('sales_management.db')
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        conn = sqlite3.connect('sales_management.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, name, password) VALUES (?, ?, ?)",
                      (username, name, password))
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

    def delete_product(product_id):
        conn = sqlite3.connect('sales_management.db')
        c = conn.cursor()
        c.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()

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

    def delete_sale(sale_id):
        conn = sqlite3.connect('sales_management.db')
        c = conn.cursor()
        c.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
        conn.commit()
        conn.close()

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

    def delete_credit(credit_id):
        conn = sqlite3.connect('sales_management.db')
        c = conn.cursor()
        c.execute("DELETE FROM credits WHERE id = ?", (credit_id,))
        conn.commit()
        conn.close()

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
        with st.form("delete_product"):
            product_id = st.number_input("أدخل ID المنتج لحذفه", min_value=1)
            submitted = st.form_submit_button("حذف المنتج")
            if submitted:
                delete_product(product_id)
                st.success("تم حذف المنتج")

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
        with st.form("delete_sale"):
            sale_id = st.number_input("أدخل ID البيع لحذفه", min_value=1)
            submitted = st.form_submit_button("حذف البيع")
            if submitted:
                delete_sale(sale_id)
                st.success("تم حذف البيع")

    with tab3:
        st.header("إدارة الائتمان")
        with st.form("add_credit"):
            customer_name = st.text_input("اسم العميل")
            product_name = st.text_input("اسم المنتج")
            quantity = st.number_input("الكمية", min_value=1)
            total_price = st.number_input("السعر الإجمالي", min_value=0.0)
            paid = st.checkbox("مدفوع")
            submitted = st.form_submit_button("إضافة ائتمان")
            if submitted:
                add_credit(customer_name, product_name, quantity, total_price, paid)
                st.success("تم إضافة الائتمان")

        st.subheader("قائمة الائتمان")
        credits_df = get_credits()
        st.dataframe(credits_df)
        with st.form("delete_credit"):
            credit_id = st.number_input("أدخل ID الائتمان لحذفه", min_value=1)
            submitted = st.form_submit_button("حذف الائتمان")
            if submitted:
                delete_credit(credit_id)
                st.success("تم حذف الائتمان")

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
        with st.form("delete_user"):
            user_id = st.number_input("أدخل ID المستخدم لحذفه", min_value=1)
            submitted = st.form_submit_button("حذف المستخدم")
            if submitted:
                delete_user(user_id)
                st.success("تم حذف المستخدم")
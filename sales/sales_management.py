import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Querybox
from ttkbootstrap.widgets import ToastNotification
from PIL import Image, ImageTk
import io
import requests
import plotly.graph_objs as go
import plotly.io as pio
from plotly.subplots import make_subplots
import numpy as np
from sklearn.linear_model import LinearRegression
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SalesManagementSystem:
    def __init__(self, master):
        self.master = master
        self.style = ttk.Style(theme='superhero')
        self.master.title("نظام إدارة المبيعات")
        self.master.geometry("1200x700")

        self.conn = sqlite3.connect('sales_management.db')
        self.create_tables()
        self.create_indexes()

        self.load_icons()

        self.create_menu()

        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # علامة تبويب المنتجات
        self.products_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.products_frame, text="المنتجات", image=self.product_icon, compound=tk.LEFT)
        self.setup_products_tab()

        # علامة تبويب المبيعات
        self.sales_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sales_frame, text="المبيعات", image=self.sale_icon, compound=tk.LEFT)
        self.setup_sales_tab()

        # علامة تبويب التقارير
        # تقارير ولوحة المعلومات محذوفتان حسب الطلب

        # علامة تبويب إدارة المستخدمين
        self.users_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.users_frame, text="إدارة المستخدمين", image=self.user_icon, compound=tk.LEFT)
        self.setup_users_tab()

        # نافذة التنبيهات محذوفة حسب الطلب

        # لم يعد هناك تحديث لوحة معلومات (تمت إزالتها)

        # إضافة زر تبديل الموضوع
        self.theme_button = ttk.Button(self.master, text="تبديل الموضوع", command=self.toggle_theme, style='info.TButton')
        self.theme_button.pack(side="bottom", pady=10)

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # إنشاء جدول الفئات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            )
        ''')

        # إنشاء جدول المنتجات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

        # إنشاء جدول المبيعات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')

        # إنشاء جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')

        # جدول السجلات الائتمانية (زبائن أخذوا منتجات على كريدي)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credits (
                id INTEGER PRIMARY KEY,
                customer_name TEXT NOT NULL,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                date TEXT NOT NULL,
                paid INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')

        self.conn.commit()

    def create_indexes(self):
        cursor = self.conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_name ON products (name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales (date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_category ON products (category_id)")
        self.conn.commit()

    def toggle_theme(self):
        current_theme = self.style.theme.name
        new_theme = 'darkly' if current_theme == 'superhero' else 'superhero'
        self.style.theme_use(new_theme)

    def load_icons(self):
        icon_urls = {
            'product': 'https://img.icons8.com/color/48/000000/product.png',
            'sale': 'https://img.icons8.com/color/48/000000/sale.png',
            'report': 'https://img.icons8.com/color/48/000000/report-card.png',
            'dashboard': 'https://img.icons8.com/color/48/000000/dashboard.png',
            'user': 'https://img.icons8.com/color/48/000000/user.png'
        }

        self.icons = {}
        for name, url in icon_urls.items():
            try:
                response = requests.get(url)
                img_data = response.content
                img = Image.open(io.BytesIO(img_data))
                img = img.resize((24, 24), Image.LANCZOS)
                self.icons[name] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"فشل في تحميل الأيقونة {name}: {e}")
                self.icons[name] = None

        self.product_icon = self.icons.get('product')
        self.sale_icon = self.icons.get('sale')
        self.report_icon = self.icons.get('report')
        self.dashboard_icon = self.icons.get('dashboard')
        self.user_icon = self.icons.get('user')

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ملف", menu=file_menu)
        file_menu.add_command(label="تصدير قاعدة البيانات", command=self.export_database)
        file_menu.add_command(label="استيراد قاعدة البيانات", command=self.import_database)
        file_menu.add_separator()
        file_menu.add_command(label="خروج", command=self.master.quit)

        # قائمة التقارير محذوفة (تمت إزالة تبويب التقارير)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="أدوات", menu=tools_menu)
        tools_menu.add_command(label="التنبؤ بالمبيعات", command=self.sales_prediction)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="مساعدة", menu=help_menu)
        help_menu.add_command(label="دليل المستخدم", command=self.show_user_guide)
        help_menu.add_command(label="حول", command=self.show_about)

    def setup_products_tab(self):
        frame = ttk.Frame(self.products_frame)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # تحسين تصميم نموذج إضافة المنتج
        input_frame = ttk.Labelframe(frame, text="إضافة منتج جديد", padding=(20, 10))
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(input_frame, text="اسم المنتج:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.product_name = ttk.Entry(input_frame, width=30)
        self.product_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="السعر:").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.product_price = ttk.Entry(input_frame, width=15)
        self.product_price.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="الكمية:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.product_quantity = ttk.Entry(input_frame, width=15)
        self.product_quantity.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="الفئة:").grid(row=1, column=2, padx=5, pady=5, sticky='w')
        self.product_category = ttk.Combobox(input_frame, state="readonly", width=25)
        self.product_category.grid(row=1, column=3, padx=5, pady=5)
        self.update_category_list()

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=4, pady=10)

        ttk.Button(button_frame, text="إضافة منتج", command=self.add_product, style='success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="إضافة فئة", command=self.add_category, style='info.TButton').pack(side=tk.LEFT, padx=5)

        # تحسين تصميم البحث المتقدم
        search_frame = ttk.Labelframe(frame, text="بحث متقدم عن منتج", padding=(20, 10))
        search_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(search_frame, text="اسم المنتج:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.product_search = ttk.Entry(search_frame, width=30)
        self.product_search.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(search_frame, text="بحث", command=self.search_products, style='primary.TButton').grid(row=1, column=0, columnspan=2, pady=10)

        # تحسين عرض جدول المنتجات
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.product_tree = ttk.Treeview(tree_frame, columns=("ID", "الاسم", "السعر", "الكمية", "الفئة"), show="headings")
        self.product_tree.heading("ID", text="ID")
        self.product_tree.heading("الاسم", text="الاسم")
        self.product_tree.heading("السعر", text="السعر")
        self.product_tree.heading("الكمية", text="الكمية")
        self.product_tree.heading("الفئة", text="الفئة")
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.product_tree.configure(yscrollcommand=scrollbar.set)

        action_frame = ttk.Frame(frame)
        action_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Button(action_frame, text="تعديل المنتج", command=self.edit_product, style='warning.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="حذف المنتج", command=self.delete_product, style='danger.TButton').pack(side=tk.LEFT, padx=5)

        self.load_products()

    def setup_sales_tab(self):
        frame = ttk.Frame(self.sales_frame)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # تحسين تصميم نموذج إضافة المبيعات
        input_frame = ttk.Labelframe(frame, text="إضافة بيع جديد", padding=(20, 10))
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(input_frame, text="المنتج:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.sale_product = ttk.Entry(input_frame, width=30)
        self.sale_product.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="الكمية:").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.sale_quantity = ttk.Entry(input_frame, width=15)
        self.sale_quantity.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="الإجمالي (بدرهم):").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.sale_total = ttk.Entry(input_frame, width=20)
        self.sale_total.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(input_frame, text="إضافة بيع", command=self.add_sale, style='success.TButton').grid(row=2, column=0, columnspan=4, pady=10)

        # تحسين تصميم البحث المتقدم في المبيعات
        search_frame = ttk.Labelframe(frame, text="بحث متقدم في المبيعات", padding=(20, 10))
        search_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(search_frame, text="المنتج:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.sales_search_product = ttk.Entry(search_frame, width=30)
        self.sales_search_product.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(search_frame, text="بحث", command=self.search_sales, style='primary.TButton').grid(row=1, column=0, columnspan=2, pady=10)

        # تحسين عرض جدول المبيعات
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.sales_tree = ttk.Treeview(tree_frame, columns=("ID", "المنتج", "الكمية", "السعر الإجمالي", "التاريخ"), show="headings")
        self.sales_tree.heading("ID", text="ID")
        self.sales_tree.heading("المنتج", text="المنتج")
        self.sales_tree.heading("الكمية", text="الكمية")
        self.sales_tree.heading("السعر الإجمالي", text="السعر الإجمالي")
        self.sales_tree.heading("التاريخ", text="التاريخ")
        self.sales_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.sales_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sales_tree.configure(yscrollcommand=scrollbar.set)

        self.load_sales()
        self.update_product_list()

    def setup_reports_tab(self):
        # تم إزالة واجهة تبويب التقارير
        pass

    def setup_dashboard_tab(self):
        # تم إزالة تبويب لوحة المعلومات
        pass

    def setup_users_tab(self):
        frame = ttk.Frame(self.users_frame)
        frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # نموذج إضافة مستخدم جديد
        input_frame = ttk.Labelframe(frame, text="إضافة مستخدم جديد", padding=(20, 10))
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Label(input_frame, text="اسم الزبون:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.new_username = ttk.Entry(input_frame, width=30)
        self.new_username.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="المنتج:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.credit_product = ttk.Entry(input_frame, width=25)
        self.credit_product.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="الكمية:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.credit_quantity = ttk.Entry(input_frame, width=15)
        self.credit_quantity.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="التاريخ:").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.credit_date = ttk.DateEntry(input_frame, width=15)
        self.credit_date.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="الإجمالي (بدرهم):").grid(row=1, column=2, padx=5, pady=5, sticky='w')
        self.credit_total = ttk.Entry(input_frame, width=20)
        self.credit_total.grid(row=1, column=3, padx=5, pady=5)

        self.credit_paid_var = tk.IntVar(value=0)
        self.credit_paid_check = ttk.Checkbutton(input_frame, text="مدفوع؟", variable=self.credit_paid_var)
        self.credit_paid_check.grid(row=2, column=2, columnspan=2, padx=5, pady=5, sticky='w')

        # نموذج تسجيل ائتمان (زبون أخذ منتج على كريدي)
        ttk.Button(input_frame, text="إضافة ائتمان", command=self.add_user, style='success.TButton').grid(row=3, column=0, columnspan=2, pady=10)

        # جدول السجلات الائتمانية
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.users_tree = ttk.Treeview(tree_frame, columns=("ID", "اسم الزبون", "المنتج", "الكمية", "الإجمالي", "التاريخ", "حالة الدفع"), displaycolumns=("اسم الزبون", "المنتج", "الكمية", "الإجمالي", "التاريخ", "حالة الدفع"), show="headings")
        self.users_tree.heading("اسم الزبون", text="اسم الزبون")
        self.users_tree.heading("المنتج", text="المنتج")
        self.users_tree.heading("الكمية", text="الكمية")
        self.users_tree.heading("الإجمالي", text="الإجمالي")
        self.users_tree.heading("التاريخ", text="التاريخ")
        self.users_tree.heading("حالة الدفع", text="حالة الدفع")
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.users_tree.configure(yscrollcommand=scrollbar.set)

        action_frame = ttk.Frame(frame)
        action_frame.pack(padx=10, pady=10, fill=tk.X)

        ttk.Button(action_frame, text="تعديل السجل", command=self.edit_user, style='warning.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="حذف السجل", command=self.delete_user, style='danger.TButton').pack(side=tk.LEFT, padx=5)

        # جلب السجلات الحالية
        self.load_users()

    def add_user(self):
        # إضافة سجل ائتماني (كشف زبون أخذ منتجات ولم يدفع بعد أو دفع)
        customer = self.new_username.get()
        product = self.credit_product.get()
        quantity = self.credit_quantity.get()
        date = str(self.credit_date.get()) if hasattr(self.credit_date, 'get') else datetime.now().strftime('%Y-%m-%d')
        total_price = self.credit_total.get()
        paid = int(self.credit_paid_var.get())

        if not customer or not product or not quantity or not total_price:
            messagebox.showerror("خطأ", "يرجى ملء جميع الحقول الأساسية")
            return

        try:
            quantity = int(quantity)
            total_price = float(total_price)
        except ValueError:
            messagebox.showerror("خطأ", "الكمية والإجمالي يجب أن يكونا أرقاماً صحيحة")
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM products WHERE name = ?", (product,))
        prod = cursor.fetchone()
        if not prod:
            # إضافة منتج جديد إذا لم يكن موجوداً
            price = total_price / quantity if quantity > 0 else 0
            cursor.execute("INSERT INTO products (name, price, category) VALUES (?, ?, ?)", (product, price, "عام"))
            self.conn.commit()
            product_id = cursor.lastrowid
        else:
            product_id = prod[0]

        cursor.execute("INSERT INTO credits (customer_name, product_id, quantity, total_price, date, paid) VALUES (?, ?, ?, ?, ?, ?)",
                       (customer, product_id, quantity, total_price, date, paid))
        self.conn.commit()
        messagebox.showinfo("نجاح", "تمت إضافة سجل الائتمان بنجاح")
        self.load_users()
        self.clear_user_inputs()

    def load_users(self):
        self.users_tree.delete(*self.users_tree.get_children())
        cursor = self.conn.cursor()
        cursor.execute("SELECT credits.id, credits.customer_name, products.name, credits.quantity, credits.total_price, credits.date, credits.paid FROM credits LEFT JOIN products ON credits.product_id = products.id ORDER BY credits.date DESC")
        for row in cursor.fetchall():
            paid_text = 'مدفوع' if row[6] == 1 else 'غير مدفوع'
            self.users_tree.insert("", "end", values=(row[0], row[1], row[2], row[3], f"{row[4]:.2f}", row[5], paid_text))

    def clear_user_inputs(self):
        try:
            self.new_username.delete(0, tk.END)
        except Exception:
            pass
        try:
            self.credit_product.delete(0, tk.END)
        except Exception:
            pass
        try:
            self.credit_quantity.delete(0, tk.END)
        except Exception:
            pass
        try:
            self.credit_total.delete(0, tk.END)
        except Exception:
            pass
        try:
            self.credit_paid_var.set(0)
        except Exception:
            pass

    def edit_user(self):
        selected_item = self.users_tree.selection()
        if not selected_item:
            messagebox.showerror("خطأ", "يرجى تحديد مستخدم لتعديله")
            return
        credit_id = self.users_tree.item(selected_item)['values'][0]

        edit_window = tk.Toplevel(self.master)
        edit_window.title("تعديل سجل الائتمان")
        edit_window.geometry("400x250")

        ttk.Label(edit_window, text="العميل:").grid(row=0, column=0, padx=5, pady=5)
        customer_entry = ttk.Entry(edit_window)
        customer_entry.grid(row=0, column=1, padx=5, pady=5)
        customer_entry.insert(0, self.users_tree.item(selected_item)['values'][1])

        ttk.Label(edit_window, text="المنتج:").grid(row=1, column=0, padx=5, pady=5)
        product_entry = ttk.Entry(edit_window)
        product_entry.grid(row=1, column=1, padx=5, pady=5)
        product_entry.insert(0, self.users_tree.item(selected_item)['values'][2])

        ttk.Label(edit_window, text="الكمية:").grid(row=2, column=0, padx=5, pady=5)
        qty_entry = ttk.Entry(edit_window)
        qty_entry.grid(row=2, column=1, padx=5, pady=5)
        qty_entry.insert(0, self.users_tree.item(selected_item)['values'][3])

        ttk.Label(edit_window, text="الإجمالي (بدرهم):").grid(row=1, column=2, padx=5, pady=5)
        total_entry = ttk.Entry(edit_window, width=20)
        total_entry.grid(row=1, column=3, padx=5, pady=5)
        total_entry.insert(0, self.users_tree.item(selected_item)['values'][4])

        ttk.Label(edit_window, text="التاريخ:").grid(row=0, column=2, padx=5, pady=5)
        date_entry = ttk.DateEntry(edit_window, width=15)
        date_entry.grid(row=0, column=3, padx=5, pady=5)
        try:
            date_entry.set_date(self.users_tree.item(selected_item)['values'][5])
        except Exception:
            pass

        paid_var = tk.IntVar(value=1 if self.users_tree.item(selected_item)['values'][6] == 'مدفوع' else 0)
        paid_check = ttk.Checkbutton(edit_window, text="مدفوع؟", variable=paid_var)
        paid_check.grid(row=2, column=2, columnspan=2, padx=5, pady=5)

        def save_changes():
            customer = customer_entry.get()
            product = product_entry.get()
            try:
                qty = int(qty_entry.get())
                total = float(total_entry.get())
            except ValueError:
                messagebox.showerror("خطأ", "الكمية والإجمالي يجب أن يكونا أرقاماً")
                return
            date_val = str(date_entry.get()) if hasattr(date_entry, 'get') else datetime.now().strftime('%Y-%m-%d')
            paid = int(paid_var.get())

            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM products WHERE name = ?", (product,))
            p = cursor.fetchone()
            if not p:
                # إضافة منتج جديد إذا لم يكن موجوداً
                price = total / qty if qty > 0 else 0
                cursor.execute("INSERT INTO products (name, price, category) VALUES (?, ?, ?)", (product, price, "عام"))
                self.conn.commit()
                product_id = cursor.lastrowid
            else:
                product_id = p[0]

            cursor.execute("UPDATE credits SET customer_name = ?, product_id = ?, quantity = ?, total_price = ?, date = ?, paid = ? WHERE id = ?",
                           (customer, product_id, qty, total, date_val, paid, credit_id))
            self.conn.commit()
            messagebox.showinfo("نجاح", "تم تحديث السجل")
            self.load_users()
            edit_window.destroy()

        ttk.Button(edit_window, text="حفظ التغييرات", command=save_changes).grid(row=3, column=0, columnspan=4, pady=10)

    def delete_user(self):
        selected_item = self.users_tree.selection()
        if not selected_item:
            messagebox.showerror("خطأ", "يرجى تحديد مستخدم لحذفه")
            return
        credit_id = self.users_tree.item(selected_item)['values'][0]

        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذا السجل الائتماني؟"):
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM credits WHERE id = ?", (credit_id,))
            self.conn.commit()
            self.load_users()

    def update_dashboard(self):
        # تمت إزالة لوحة المعلومات؛ لم يعد هناك تحديث دوري للوحة
        return

    # تم إزالة دوال التقارير المتعلقة بعرض وطباعة التقارير

    def sales_prediction(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DATE(date) as sale_date, SUM(total_price) as daily_sales
            FROM sales
            GROUP BY sale_date
            ORDER BY sale_date
        """)
        sales_data = cursor.fetchall()

        if len(sales_data) < 2:
            messagebox.showwarning("تنبيه", "لا توجد بيانات كافية للتنبؤ")
            return

        dates = [datetime.strptime(row[0], '%Y-%m-%d').toordinal() for row in sales_data]
        sales = [row[1] for row in sales_data]

        X = np.array(dates).reshape(-1, 1)
        y = np.array(sales)

        model = LinearRegression()
        model.fit(X, y)

        future_dates = [max(dates) + i for i in range(1, 31)]
        future_sales = model.predict(np.array(future_dates).reshape(-1, 1))

        prediction_window = tk.Toplevel(self.master)
        prediction_window.title("التنبؤ بالمبيعات")
        prediction_window.geometry("800x600")

        text_widget = tk.Text(prediction_window)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        text_widget.insert(tk.END, "التنبؤ بالمبيعات للـ 30 يومًا القادمة\n\n")
        for i, (date, sale) in enumerate(zip(future_dates, future_sales)):
            date_str = datetime.fromordinal(int(date)).strftime("%Y-%m-%d")
            text_widget.insert(tk.END, f"{date_str}: {sale:.2f} ريال\n")

    # تم إزالة إعدادات التنبيهات

    def show_user_guide(self):
        guide_window = tk.Toplevel(self.master)
        guide_window.title("دليل المستخدم")
        guide_window.geometry("800x600")

        guide_text = tk.Text(guide_window, wrap=tk.WORD, padx=10, pady=10)
        guide_text.pack(fill=tk.BOTH, expand=True)

        guide_content = """دليل المستخدم لنظام إدارة المبيعات

1. المنتجات:
   - إضافة منتج جديد: املأ النموذج وانقر على "إضافة منتج"
   - تعديل منتج: حدد المنتج من القائمة وانقر على "تعديل المنتج"
   - حذف منتج: حدد المنتج وانقر على "حذف المنتج"

2. المبيعات:
   - تسجيل بيع جديد: اختر المنتج والكمية وانقر على "إضافة بيع"
   - البحث في المبيعات: استخدم نموذج البحث المتقدم

3. التقارير:
   - إنشاء تقرير: اختر نوع التقرير والفترة الزمنية ثم انقر على "إنشاء التقرير"
   - تصدير التقرير: انقر على "تصدير إلى Excel" أو "طباعة التقرير"

4. لوحة المعلومات:
   - عرض إحصائيات المبيعات والمخزون بشكل مرئي

5. إدارة المستخدمين:
   - إضافة مستخدم جديد: املأ النموذج وانقر على "إضافة مستخدم"
   - تعديل مستخدم: حدد المستخدم وانقر على "تعديل المستخدم"
   - حذف مستخدم: حدد المستخدم وانقر على "حذف المستخدم"

للمزيد من المساعدة، يرجى الاتصال بفريق الدعم الفني.
"""

        guide_text.insert(tk.END, guide_content)
        guide_text.config(state=tk.DISABLED)

    def show_about(self):
        about_window = tk.Toplevel(self.master)
        about_window.title("حول البرنامج")
        about_window.geometry("400x300")

        ttk.Label(about_window, text="نظام إدارة المبيعات", font=("Arial", 16, "bold")).pack(pady=10)
        ttk.Label(about_window, text="الإصدار 2.0").pack(pady=5)
        ttk.Label(about_window, text="تم تطويره بواسطة فريق البرمجة").pack(pady=5)
        ttk.Label(about_window, text="جميع الحقوق محفوظة © 2023").pack(pady=5)

        ttk.Button(about_window, text="موافق", command=about_window.destroy).pack(pady=20)

    def print_report(self):
        # طباعة التقارير محذوفة مع تبويب التقارير
        return

    # تم إزالة نافذة التنبيهات

    # تم إزالة فحص المخزون المنخفض والتحديث الدوري للتنبيهات

    def export_database(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite Database", "*.db")])
        if file_path:
            import shutil
            shutil.copy2('sales_management.db', file_path)
            messagebox.showinfo("تم", f"تم تصدير قاعدة البيانات إلى {file_path}")

    def import_database(self):
        file_path = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db")])
        if file_path:
            import shutil
            shutil.copy2(file_path, 'sales_management.db')
            messagebox.showinfo("تم", f"تم استيراد قاعدة البيانات من {file_path}")
            self.conn.close()
            self.conn = sqlite3.connect('sales_management.db')
            self.load_products()
            self.load_sales()
            self.load_users()
            # تم إزالة لوحة المعلومات؛ لا حاجة لتحديثها

    def add_product(self):
        name = self.product_name.get()
        price = self.product_price.get()
        quantity = self.product_quantity.get()
        category = self.product_category.get()

        if not name or not price or not quantity or not category:
            messagebox.showerror("خطأ", "يرجى ملء جميع الحقول")
            return

        try:
            price = float(price)
            quantity = int(quantity)
        except ValueError:
            messagebox.showerror("خطأ", "يرجى إدخال قيم صحيحة للسعر والكمية")
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
        category_id = cursor.fetchone()

        if category_id:
            category_id = category_id[0]
        else:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (category,))
            category_id = cursor.lastrowid

        cursor.execute("INSERT INTO products (name, price, quantity, category_id) VALUES (?, ?, ?, ?)",
                       (name, price, quantity, category_id))
        self.conn.commit()

        self.load_products()
        self.clear_product_inputs()
        messagebox.showinfo("نجاح", "تمت إضافة المنتج بنجاح")

    def edit_product(self):
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showerror("خطأ", "يرجى تحديد منتج لتعديله")
            return

        product_id = self.product_tree.item(selected_item)['values'][0]
        
        edit_window = tk.Toplevel(self.master)
        edit_window.title("تعديل المنتج")
        edit_window.geometry("300x250")

        ttk.Label(edit_window, text="اسم المنتج:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(edit_window)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.insert(0, self.product_tree.item(selected_item)['values'][1])

        ttk.Label(edit_window, text="السعر:").grid(row=1, column=0, padx=5, pady=5)
        price_entry = ttk.Entry(edit_window)
        price_entry.grid(row=1, column=1, padx=5, pady=5)
        price_entry.insert(0, self.product_tree.item(selected_item)['values'][2])

        ttk.Label(edit_window, text="الكمية:").grid(row=2, column=0, padx=5, pady=5)
        quantity_entry = ttk.Entry(edit_window)
        quantity_entry.grid(row=2, column=1, padx=5, pady=5)
        quantity_entry.insert(0, self.product_tree.item(selected_item)['values'][3])

        ttk.Label(edit_window, text="الفئة:").grid(row=3, column=0, padx=5, pady=5)
        category_combobox = ttk.Combobox(edit_window, values=self.get_categories(), state="readonly")
        category_combobox.grid(row=3, column=1, padx=5, pady=5)
        category_combobox.set(self.product_tree.item(selected_item)['values'][4])

        def save_changes():
            name = name_entry.get()
            price = price_entry.get()
            quantity = quantity_entry.get()
            category = category_combobox.get()

            if not name or not price or not quantity or not category:
                messagebox.showerror("خطأ", "يرجى ملء جميع الحقول")
                return

            try:
                price = float(price)
                quantity = int(quantity)
            except ValueError:
                messagebox.showerror("خطأ", "يرجى إدخال قيم صحيحة للسعر والكمية")
                return

            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
            category_id = cursor.fetchone()[0]

            cursor.execute("UPDATE products SET name = ?, price = ?, quantity = ?, category_id = ? WHERE id = ?",
                           (name, price, quantity, category_id, product_id))
            self.conn.commit()

            self.load_products()
            messagebox.showinfo("نجاح", "تم تحديث المنتج بنجاح")
            edit_window.destroy()

        ttk.Button(edit_window, text="حفظ التغييرات", command=save_changes).grid(row=4, column=0, columnspan=2, pady=10)

    def delete_product(self):
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showerror("خطأ", "يرجى تحديد منتج لحذفه")
            return

        product_id = self.product_tree.item(selected_item)['values'][0]
        
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذا المنتج؟"):
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
            self.conn.commit()
            self.load_products()

    def load_products(self):
        self.product_tree.delete(*self.product_tree.get_children())
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT products.id, products.name, products.price, products.quantity, categories.name
            FROM products
            LEFT JOIN categories ON products.category_id = categories.id
        """)
        for row in cursor.fetchall():
            self.product_tree.insert("", "end", values=row)

    def clear_product_inputs(self):
        self.product_name.delete(0, tk.END)
        self.product_price.delete(0, tk.END)
        self.product_quantity.delete(0, tk.END)
        self.product_category.set("")

    def add_category(self):
        category_name = simpledialog.askstring("إضافة فئة", "أدخل اسم الفئة الجديدة:")
        if category_name:
            cursor = self.conn.cursor()
            try:
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
                self.conn.commit()
                self.update_category_list()
                messagebox.showinfo("نجاح", "تمت إضافة الفئة بنجاح")
            except sqlite3.IntegrityError:
                messagebox.showerror("خطأ", "هذه الفئة موجودة بالفعل")

    def update_category_list(self, combobox=None):
        if combobox is None:
            combobox = self.product_category

        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM categories")
        categories = [row[0] for row in cursor.fetchall()]
        combobox['values'] = categories

    def get_categories(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM categories")
        return [row[0] for row in cursor.fetchall()]

    def search_products(self):
        name = self.product_search.get()

        query = """
            SELECT products.id, products.name, products.price, products.quantity, categories.name
            FROM products
            LEFT JOIN categories ON products.category_id = categories.id
            WHERE 1=1
        """
        params = []

        if name:
            query += " AND products.name LIKE ?"
            params.append(f"%{name}%")

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()

        self.product_tree.delete(*self.product_tree.get_children())
        for row in results:
            self.product_tree.insert("", "end", values=row)

    def add_sale(self):
        product = self.sale_product.get()
        quantity = self.sale_quantity.get()
        total_price = self.sale_total.get()

        if not product or not quantity or not total_price:
            messagebox.showerror("خطأ", "يرجى ملء جميع الحقول")
            return

        try:
            quantity = int(quantity)
            total_price = float(total_price)
        except ValueError:
            messagebox.showerror("خطأ", "يرجى إدخال قيم صحيحة للكمية والإجمالي")
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, price, quantity FROM products WHERE name = ?", (product,))
        product_info = cursor.fetchone()

        if not product_info:
            # إضافة منتج جديد إذا لم يكن موجوداً
            price = total_price / quantity if quantity > 0 else 0
            cursor.execute("INSERT INTO products (name, price, quantity, category) VALUES (?, ?, ?, ?)", (product, price, 1000, "عام"))  # افتراض كمية كبيرة
            self.conn.commit()
            product_id = cursor.lastrowid
            available_quantity = 1000
        else:
            product_id, price, available_quantity = product_info

        if quantity > available_quantity:
            messagebox.showerror("خطأ", "الكمية المطلوبة غير متوفرة في المخزون")
            return

        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("INSERT INTO sales (product_id, quantity, total_price, date) VALUES (?, ?, ?, ?)",
                       (product_id, quantity, total_price, date))
        cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (quantity, product_id))
        self.conn.commit()

        self.load_sales()
        self.load_products()
        self.clear_sale_inputs()
        messagebox.showinfo("نجاح", "تمت إضافة البيع بنجاح")

    def load_sales(self):
        self.sales_tree.delete(*self.sales_tree.get_children())
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT sales.id, products.name, sales.quantity, sales.total_price, sales.date
            FROM sales
            JOIN products ON sales.product_id = products.id
            ORDER BY sales.date DESC
        """)
        for row in cursor.fetchall():
            self.sales_tree.insert("", "end", values=row)

    def clear_sale_inputs(self):
        self.sale_product.delete(0, tk.END)
        self.sale_quantity.delete(0, tk.END)
        self.sale_total.delete(0, tk.END)

    def update_product_list(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM products")
        products = [row[0] for row in cursor.fetchall()]
        try:
            self.credit_product['values'] = products
        except Exception:
            pass

    def search_sales(self):
        product = self.sales_search_product.get()
        query = """
            SELECT sales.id, products.name, sales.quantity, sales.total_price, sales.date
            FROM sales
            JOIN products ON sales.product_id = products.id
            WHERE 1=1
        """
        params = []

        if product:
            query += " AND products.name = ?"
            params.append(product)

        query += " ORDER BY sales.date DESC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()

        self.sales_tree.delete(*self.sales_tree.get_children())
        for row in results:
            self.sales_tree.insert("", "end", values=row)

    # تمت إزالة دوال إنشاء/تصدير التقارير لغياب تبويب التقارير


if __name__ == "__main__":
    root = tk.Tk()
    app = SalesManagementSystem(root)
    root.mainloop()

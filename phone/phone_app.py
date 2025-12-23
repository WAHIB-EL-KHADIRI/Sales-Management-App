import os
import json
import tempfile
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from gtts import gTTS, lang
from langdetect import detect
from pydub import AudioSegment
import threading
import queue
from googletrans import Translator
import speech_recognition as sr
from fpdf import FPDF
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.probability import FreqDist
import language_tool_python
import warnings
import requests
from bs4 import BeautifulSoup
import pygame
import time
import io
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from textblob import TextBlob
import pronouncing

warnings.filterwarnings("ignore", category=RuntimeWarning)

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

ctk.set_default_color_theme("blue")

class AdvancedTextToSpeechConverterApp(ctk.CTk):
    def __init__(self, root):
        self.root = root
        self.root.title("تطبيق تحديد موقع رقم الهاتف")
        self.root.geometry("700x600")
        self.root.configure(bg="#f5f5f5")
        
        # Default region code
        self.default_region = "SA"  # Saudi Arabia as default
        
        # Set theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f5f5f5')
        self.style.configure('TLabel', background='#f5f5f5', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10, 'bold'))
        self.style.configure('Header.TLabel', font=('Arial', 16, 'bold'))
        self.style.configure('Result.TLabel', font=('Arial', 11))
        
        # History of lookups
        self.history = []
        self.history_file = "phone_lookup_history.json"
        self.load_history()
        
        # Create main container
        main_container = ttk.Frame(root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.lookup_tab = ttk.Frame(self.notebook)
        self.history_tab = ttk.Frame(self.notebook)
        self.about_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.lookup_tab, text="البحث")
        self.notebook.add(self.history_tab, text="السجل")
        self.notebook.add(self.about_tab, text="حول")
        
        # Setup lookup tab
        self.setup_lookup_tab()
        
        # Setup history tab
        self.setup_history_tab()
        
        # Setup about tab
        self.setup_about_tab()
    
    def setup_lookup_tab(self):
        # Title
        title_label = ttk.Label(self.lookup_tab, text="معلومات رقم الهاتف", style='Header.TLabel')
        title_label.pack(pady=10)
        
        # Input frame
        input_frame = ttk.Frame(self.lookup_tab)
        input_frame.pack(fill=tk.X, pady=10)
        
        # Country code selection
        country_frame = ttk.Frame(input_frame)
        country_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(country_frame, text=":اختر البلد الافتراضي").pack(side=tk.RIGHT, padx=5)
        
        # Country codes dictionary (ISO code to country name in Arabic)
        self.country_codes = {
            "SA": "السعودية",
            "EG": "مصر",
            "AE": "الإمارات",
            "QA": "قطر",
            "KW": "الكويت",
            "BH": "البحرين",
            "OM": "عمان",
            "JO": "الأردن",
            "LB": "لبنان",
            "IQ": "العراق",
            "YE": "اليمن",
            "SY": "سوريا",
            "PS": "فلسطين",
            "LY": "ليبيا",
            "MA": "المغرب",
            "TN": "تونس",
            "DZ": "الجزائر",
            "SD": "السودان",
            "US": "الولايات المتحدة"
        }
        
        # Create a combobox for country selection
        self.country_var = tk.StringVar(value=f"SA - {self.country_codes['SA']}")
        country_combobox = ttk.Combobox(country_frame, textvariable=self.country_var, state="readonly", width=20)
        country_combobox['values'] = [f"{code} - {name}" for code, name in self.country_codes.items()]
        country_combobox.pack(side=tk.RIGHT, padx=5)
        country_combobox.bind("<<ComboboxSelected>>", self.update_default_region)
        
        # Phone number entry with label
        entry_frame = ttk.Frame(input_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(entry_frame, text=":أدخل رقم الهاتف").pack(side=tk.RIGHT)
        self.phone_entry = ttk.Entry(entry_frame, width=30, font=('Arial', 11), justify='right')
        self.phone_entry.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
        
        # Format hint
        format_hint = ttk.Label(input_frame, text="أدخل الرقم بصيغة: +966XXXXXXXX أو بدون + للاستخدام مع البلد المحدد", 
                               font=('Arial', 9), foreground='gray')
        format_hint.pack(anchor=tk.E, pady=2)
        
        # Buttons frame
        buttons_frame = ttk.Frame(input_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        # Lookup button
        lookup_button = ttk.Button(buttons_frame, text="بحث عن الرقم", command=self.lookup_number)
        lookup_button.pack(side=tk.RIGHT, padx=5)
        
        # Clear button
        clear_button = ttk.Button(buttons_frame, text="مسح", command=self.clear_results)
        clear_button.pack(side=tk.RIGHT, padx=5)
        
        # Save button
        save_button = ttk.Button(buttons_frame, text="حفظ النتائج", command=self.save_results)
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # Results frame
        self.results_frame = ttk.LabelFrame(self.lookup_tab, text="النتائج", padding=15)
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create two columns for results
        right_column = ttk.Frame(self.results_frame)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        left_column = ttk.Frame(self.results_frame)
        left_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        # Results labels - Right column (for RTL layout)
        self.valid_label = ttk.Label(right_column, text=":رقم صالح", style='Result.TLabel', justify='right')
        self.valid_label.pack(anchor=tk.E, pady=5)
        
        self.country_label = ttk.Label(right_column, text=":البلد", style='Result.TLabel', justify='right')
        self.country_label.pack(anchor=tk.E, pady=5)
        
        self.region_label = ttk.Label(right_column, text=":المنطقة", style='Result.TLabel', justify='right')
        self.region_label.pack(anchor=tk.E, pady=5)
        
        self.carrier_label = ttk.Label(right_column, text=":شركة الاتصالات", style='Result.TLabel', justify='right')
        self.carrier_label.pack(anchor=tk.E, pady=5)
        
        # Results labels - Left column (for RTL layout)
        self.number_type_label = ttk.Label(left_column, text=":نوع الرقم", style='Result.TLabel', justify='right')
        self.number_type_label.pack(anchor=tk.E, pady=5)
        
        self.timezone_label = ttk.Label(left_column, text=":المنطقة الزمنية", style='Result.TLabel', justify='right')
        self.timezone_label.pack(anchor=tk.E, pady=5)
        
        self.format_label = ttk.Label(left_column, text=":الرقم المنسق", style='Result.TLabel', justify='right')
        self.format_label.pack(anchor=tk.E, pady=5)
        
        self.lookup_time_label = ttk.Label(left_column, text=":وقت البحث", style='Result.TLabel', justify='right')
        self.lookup_time_label.pack(anchor=tk.E, pady=5)
        
        # Map placeholder (in a real app, this would be an actual map)
        map_frame = ttk.LabelFrame(self.lookup_tab, text="خريطة الموقع", padding=10)
        map_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        map_placeholder = ttk.Label(map_frame, text="ستظهر هنا خريطة توضيحية\n(تتطلب مكتبات خرائط إضافية)", 
                                   anchor=tk.CENTER, background="#e0e0e0")
        map_placeholder.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def update_default_region(self, event=None):
        selected = self.country_var.get()
        if selected:
            # Extract the country code from the selection (e.g., "SA - السعودية" -> "SA")
            self.default_region = selected.split(" - ")[0]
    
    def setup_history_tab(self):
        # Title
        title_label = ttk.Label(self.history_tab, text="سجل البحث", style='Header.TLabel')
        title_label.pack(pady=10)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.history_tab)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        # Clear history button
        clear_history_button = ttk.Button(buttons_frame, text="مسح السجل", command=self.clear_history)
        clear_history_button.pack(side=tk.RIGHT, padx=5)
        
        # Export history button
        export_history_button = ttk.Button(buttons_frame, text="تصدير السجل", command=self.export_history)
        export_history_button.pack(side=tk.RIGHT, padx=5)
        
        # History treeview
        columns = ("phone", "country", "valid", "time")
        self.history_tree = ttk.Treeview(self.history_tab, columns=columns, show="headings")
        
        # Define headings
        self.history_tree.heading("phone", text="رقم الهاتف")
        self.history_tree.heading("country", text="البلد")
        self.history_tree.heading("valid", text="صالح")
        self.history_tree.heading("time", text="وقت البحث")
        
        # Define columns
        self.history_tree.column("phone", width=150)
        self.history_tree.column("country", width=100)
        self.history_tree.column("valid", width=50)
        self.history_tree.column("time", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.history_tab, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.history_tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=10)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y, pady=10)
        
        # Bind double-click to load history item
        self.history_tree.bind("<Double-1>", self.load_history_item)
        
        # Populate history
        self.update_history_display()
    
    def setup_about_tab(self):
        # Title
        title_label = ttk.Label(self.about_tab, text="حول تطبيق تحديد موقع رقم الهاتف", style='Header.TLabel')
        title_label.pack(pady=10)
        
        # About text
        about_text = """
        تطبيق تحديد موقع رقم الهاتف الإصدار 2.0
        
        يتيح لك هذا التطبيق البحث عن معلومات حول أرقام الهواتف
        بما في ذلك البلد والمنطقة وشركة الاتصالات والمنطقة الزمنية.
        
        الميزات:
        - التحقق من صحة أرقام الهواتف
        - تحديد البلد والمنطقة
        - عرض معلومات شركة الاتصالات
        - عرض المنطقة الزمنية
        - حفظ سجل البحث
        - تصدير النتائج
        
        يستخدم مكتبة phonenumbers، وهي نسخة بايثون من مكتبة
        libphonenumber من جوجل.
        
        تم إنشاؤه لأغراض تعليمية.
        """
        
        about_label = ttk.Label(self.about_tab, text=about_text, justify=tk.RIGHT, wraplength=500)
        about_label.pack(padx=20, pady=10, anchor=tk.E)
    
    def lookup_number(self):
        phone_number = self.phone_entry.get().strip()
        
        if not phone_number:
            messagebox.showerror("خطأ", "الرجاء إدخال رقم هاتف")
            return
        
        try:
            # Parse the phone number
            if phone_number.startswith('+'):
                # If the number has a country code (starts with +)
                parsed_number = phonenumbers.parse(phone_number)
            else:
                # If the number doesn't have a country code, use the default region
                parsed_number = phonenumbers.parse(phone_number, self.default_region)
            
            # Get current time
            lookup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Get information
            country = geocoder.description_for_number(parsed_number, "ar")  # Use Arabic if available
            carrier_name = carrier.name_for_number(parsed_number, "ar")  # Use Arabic if available
            time_zones = timezone.time_zones_for_number(parsed_number)
            is_valid = phonenumbers.is_valid_number(parsed_number)
            region = geocoder.description_for_number(parsed_number, "ar")  # Use Arabic if available
            formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            
            # Get number type - تصحيح استدعاء وظيفة number_type
            num_type = phonenumberutil.number_type(parsed_number)
            type_dict = {
                0: "خط ثابت",
                1: "جوال",
                2: "خط ثابت أو جوال",
                3: "رقم مجاني",
                4: "رقم مميز",
                5: "تكلفة مشتركة",
                6: "VOIP",
                7: "رقم شخصي",
                8: "جهاز نداء",
                9: "UAN",
                10: "بريد صوتي",
                27: "طوارئ",
                28: "معدل قياسي",
                29: "خاص بشركة الاتصالات",
                30: "رمز قصير"
            }
            number_type_str = type_dict.get(num_type, "غير معروف")
            
            # Update labels
            self.valid_label.config(text=f":رقم صالح {'نعم' if is_valid else 'لا'}")
            self.country_label.config(text=f":البلد {country or 'غير معروف'}")
            self.region_label.config(text=f":المنطقة {region or 'غير معروف'}")
            self.carrier_label.config(text=f":شركة الاتصالات {carrier_name or 'غير معروف'}")
            self.timezone_label.config(text=f":المنطقة الزمنية {', '.join(time_zones) or 'غير معروف'}")
            self.number_type_label.config(text=f":نوع الرقم {number_type_str}")
            self.format_label.config(text=f":الرقم المنسق {formatted_number}")
            self.lookup_time_label.config(text=f":وقت البحث {lookup_time}")
            
            # Add to history
            history_item = {
                "phone": phone_number,
                "formatted": formatted_number,
                "country": country or "غير معروف",
                "region": region or "غير معروف",
                "carrier": carrier_name or "غير معروف",
                "timezone": ', '.join(time_zones) or "غير معروف",
                "valid": "نعم" if is_valid else "لا",
                "number_type": number_type_str,
                "time": lookup_time
            }
            
            self.history.append(history_item)
            self.save_history()
            self.update_history_display()
            
        except phonenumbers.NumberParseException as e:
            if "Missing or invalid default region" in str(e):
                messagebox.showerror("خطأ", "يرجى إدخال رقم هاتف مع رمز البلد (مثل +966XXXXXXXX) أو اختيار البلد المناسب")
            else:
                messagebox.showerror("خطأ", f"خطأ في تنسيق الرقم: {str(e)}")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {str(e)}")
    
    def clear_results(self):
        self.phone_entry.delete(0, tk.END)
        self.valid_label.config(text=":رقم صالح ")
        self.country_label.config(text=":البلد ")
        self.region_label.config(text=":المنطقة ")
        self.carrier_label.config(text=":شركة الاتصالات ")
        self.timezone_label.config(text=":المنطقة الزمنية ")
        self.number_type_label.config(text=":نوع الرقم ")
        self.format_label.config(text=":الرقم المنسق ")
        self.lookup_time_label.config(text=":وقت البحث ")
    
    def save_results(self):
        # Check if we have results to save
        if self.format_label.cget('text') == ":الرقم المنسق ":
            messagebox.showinfo("معلومات", "لا توجد نتائج للحفظ. الرجاء البحث عن رقم أولاً.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("ملفات نصية", "*.txt"), ("جميع الملفات", "*.*")],
            title="حفظ النتائج"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write("نتائج البحث عن رقم الهاتف\n")
                file.write("==========================\n\n")
                file.write(f"رقم الهاتف: {self.phone_entry.get().strip()}\n")
                file.write(f"الرقم المنسق: {self.format_label.cget('text').replace(':الرقم المنسق ', '')}\n")
                file.write(f"صالح: {self.valid_label.cget('text').replace(':رقم صالح ', '')}\n")
                file.write(f"البلد: {self.country_label.cget('text').replace(':البلد ', '')}\n")
                file.write(f"المنطقة: {self.region_label.cget('text').replace(':المنطقة ', '')}\n")
                file.write(f"شركة الاتصالات: {self.carrier_label.cget('text').replace(':شركة الاتصالات ', '')}\n")
                file.write(f"نوع الرقم: {self.number_type_label.cget('text').replace(':نوع الرقم ', '')}\n")
                file.write(f"المنطقة الزمنية: {self.timezone_label.cget('text').replace(':المنطقة الزمنية ', '')}\n")
                file.write(f"وقت البحث: {self.lookup_time_label.cget('text').replace(':وقت البحث ', '')}\n")
            
            messagebox.showinfo("نجاح", f"تم حفظ النتائج في {file_path}")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في حفظ النتائج: {str(e)}")
    
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as file:
                    self.history = json.load(file)
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تحميل السجل: {str(e)}")
            self.history = []
    
    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as file:
                json.dump(self.history, file, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في حفظ السجل: {str(e)}")
    
    def update_history_display(self):
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Add history items
        for item in reversed(self.history):  # Show newest first
            self.history_tree.insert("", tk.END, values=(
                item["phone"],
                item["country"],
                item["valid"],
                item["time"]
            ))
    
    def load_history_item(self, event):
        selected_item = self.history_tree.selection()
        if not selected_item:
            return
        
        item_index = self.history_tree.index(selected_item[0])
        history_item = self.history[len(self.history) - 1 - item_index]  # Adjust for reversed display
        
        # Switch to lookup tab
        self.notebook.select(0)
        
        # Set phone number
        self.phone_entry.delete(0, tk.END)
        self.phone_entry.insert(0, history_item["phone"])
        
        # Update labels
        self.valid_label.config(text=f":رقم صالح {history_item['valid']}")
        self.country_label.config(text=f":البلد {history_item['country']}")
        self.region_label.config(text=f":المنطقة {history_item['region']}")
        self.carrier_label.config(text=f":شركة الاتصالات {history_item['carrier']}")
        self.timezone_label.config(text=f":المنطقة الزمنية {history_item['timezone']}")
        self.number_type_label.config(text=f":نوع الرقم {history_item['number_type']}")
        self.format_label.config(text=f":الرقم المنسق {history_item['formatted']}")
        self.lookup_time_label.config(text=f":وقت البحث {history_item['time']}")
    
    def clear_history(self):
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من رغبتك في مسح كل السجل؟"):
            self.history = []
            self.save_history()
            self.update_history_display()
    
    def export_history(self):
        if not self.history:
            messagebox.showinfo("معلومات", "لا يوجد سجل للتصدير.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("ملفات CSV", "*.csv"), ("جميع الملفات", "*.*")],
            title="تصدير السجل"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                # Write header
                file.write("رقم الهاتف,الرقم المنسق,البلد,المنطقة,شركة الاتصالات,المنطقة الزمنية,صالح,نوع الرقم,وقت البحث\n")
                
                # Write data
                for item in self.history:
                    file.write(f"{item['phone']},{item['formatted']},{item['country']},{item['region']},"
                              f"{item['carrier']},{item['timezone']},{item['valid']},{item['number_type']},{item['time']}\n")
            
            messagebox.showinfo("نجاح", f"تم تصدير السجل إلى {file_path}")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تصدير السجل: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PhoneNumberApp(root)
    root.mainloop()

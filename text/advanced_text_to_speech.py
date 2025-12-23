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
    def __init__(self):
        super().__init__()

        self.title("المحول المتقدم للنص إلى كلام")
        self.geometry("1200x800")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.languages = {lang: lang.capitalize() for lang in lang.tts_langs()}
        self.current_language = "ar"
        self.speech_speed = 1.0
        self.voice_gender = "female"
        self.settings = self.load_settings()
        self.translator = Translator()
        self.language_tool = language_tool_python.LanguageTool('ar')
        self.history = []

        self.setup_ui()
        pygame.mixer.init()

    def setup_ui(self):
        # Set up the color scheme
        bg_color = "#f0f0f0"
        fg_color = "#333333"
        accent_color = "#007bff"
        secondary_color = "#6c757d"
        
        self.configure(fg_color=bg_color)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#2c3e50")
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(13, weight=1)

        logo_label = ctk.CTkLabel(self.sidebar, text="النص إلى كلام", font=ctk.CTkFont(size=24, weight="bold"), text_color="white")
        logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        buttons = [
            ("الرئيسية", self.show_main_tab, "🏠"),
            ("الترجمة", self.show_translation_tab, "🌐"),
            ("الكلام إلى نص", self.show_stt_tab, "🎤"),
            ("استخراج النص", self.show_web_scraping_tab, "🌍"),
            ("الصورة إلى نص", self.show_image_to_text_tab, "🖼️"),
            ("تحليل النص", self.show_text_analysis_tab, "📊"),
            ("سحابة الكلمات", self.show_word_cloud_tab, "☁️"),
            ("دليل النطق", self.show_pronunciation_tab, "📖"),
            ("الإعدادات", self.show_settings_tab, "⚙️"),
        ]

        for i, (text, command, icon) in enumerate(buttons, start=1):
            button = ctk.CTkButton(self.sidebar, text=f"{icon} {text}", command=command, fg_color="transparent", text_color="white", hover_color="#34495e", height=40, anchor="w")
            button.grid(row=i, column=0, padx=20, pady=10, sticky="ew")

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar, text="وضع المظهر:", anchor="w", text_color="white")
        self.appearance_mode_label.grid(row=11, column=0, padx=20, pady=(20, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark", "System"],
                                                             command=self.change_appearance_mode_event, fg_color="#34495e", button_color="#2c3e50", button_hover_color="#2c3e50", dropdown_hover_color="#34495e")
        self.appearance_mode_optionemenu.grid(row=12, column=0, padx=20, pady=(10, 20))

        # Main content area
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=bg_color)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Tabview
        self.tabview = ctk.CTkTabview(self.main_frame, corner_radius=10, fg_color=bg_color, segmented_button_fg_color=accent_color, segmented_button_selected_color=accent_color, segmented_button_selected_hover_color="#0056b3")
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Create tabs
        self.main_tab = self.tabview.add("الرئيسية")
        self.translation_tab = self.tabview.add("الترجمة")
        self.stt_tab = self.tabview.add("الكلام إلى نص")
        self.web_scraping_tab = self.tabview.add("استخراج النص")
        self.image_to_text_tab = self.tabview.add("الصورة إلى نص")
        self.text_analysis_tab = self.tabview.add("تحليل النص")
        self.word_cloud_tab = self.tabview.add("سحابة الكلمات")
        self.pronunciation_tab = self.tabview.add("دليل النطق")
        self.settings_tab = self.tabview.add("الإعدادات")

        self.setup_main_tab()
        self.setup_translation_tab()
        self.setup_stt_tab()
        self.setup_web_scraping_tab()
        self.setup_image_to_text_tab()
        self.setup_text_analysis_tab()
        self.setup_word_cloud_tab()
        self.setup_pronunciation_tab()
        self.setup_settings_tab()

        # Status bar
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color="#ecf0f1")
        self.status_bar.grid(row=1, column=1, sticky="ew")
        self.status_label = ctk.CTkLabel(self.status_bar, text="جاهز", text_color=fg_color)
        self.status_label.grid(row=0, column=0, padx=10)

    def setup_main_tab(self):
        self.main_tab.grid_columnconfigure(0, weight=1)
        self.main_tab.grid_rowconfigure(1, weight=1)

        # Language and speed frame
        controls_frame = ctk.CTkFrame(self.main_tab)
        controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        language_label = ctk.CTkLabel(controls_frame, text="اللغة:")
        language_label.grid(row=0, column=0, padx=10, pady=10)

        self.language_optionemenu = ctk.CTkOptionMenu(controls_frame, values=list(self.languages.values()),
                                                      command=self.change_language_event)
        self.language_optionemenu.grid(row=0, column=1, padx=10, pady=10)
        self.language_optionemenu.set(self.languages[self.current_language])

        speed_label = ctk.CTkLabel(controls_frame, text="السرعة:")
        speed_label.grid(row=0, column=2, padx=10, pady=10)

        self.speed_slider = ctk.CTkSlider(controls_frame, from_=0.5, to=2.0, number_of_steps=30,
                                          command=self.change_speed_event)
        self.speed_slider.grid(row=0, column=3, padx=10, pady=10)
        self.speed_slider.set(self.speech_speed)

        self.speed_value_label = ctk.CTkLabel(controls_frame, text=f"{self.speech_speed:.1f}x")
        self.speed_value_label.grid(row=0, column=4, padx=10, pady=10)

        # Text input
        self.text_box = ctk.CTkTextbox(self.main_tab, width=800, height=300)
        self.text_box.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Buttons
        button_frame = ctk.CTkFrame(self.main_tab)
        button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        buttons = [
            ("تحويل إلى كلام", self.speak_text, "▶️"),
            ("حفظ كملف صوتي", self.save_audio, "💾"),
            ("استيراد نص", self.import_text, "📁"),
            ("نسخ النص", self.copy_text, "📋"),
            ("مسح النص", self.clear_text, "🗑️"),
            ("تصدير PDF", self.export_to_pdf, "📄"),
            ("تلخيص النص", self.summarize_text, "📝"),
            ("تدقيق إملائي", self.spell_check, "🔎"),
            ("سجل التحويلات", self.show_history, "⏰")
        ]

        for i, (text, command, icon) in enumerate(buttons):
            button = ctk.CTkButton(button_frame, text=f"{icon} {text}", command=command)
            button.grid(row=i//5, column=i%5, padx=5, pady=5)

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.main_tab)
        self.progress_bar.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.progress_bar.set(0)

    def setup_translation_tab(self):
        self.translation_tab.grid_columnconfigure(0, weight=1)
        self.translation_tab.grid_rowconfigure(1, weight=1)
        self.translation_tab.grid_rowconfigure(3, weight=1)

        controls_frame = ctk.CTkFrame(self.translation_tab)
        controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        from_lang_label = ctk.CTkLabel(controls_frame, text="من:")
        from_lang_label.grid(row=0, column=0, padx=10, pady=10)

        self.from_lang_optionemenu = ctk.CTkOptionMenu(controls_frame, values=list(self.languages.values()))
        self.from_lang_optionemenu.grid(row=0, column=1, padx=10, pady=10)

        to_lang_label = ctk.CTkLabel(controls_frame, text="إلى:")
        to_lang_label.grid(row=0, column=2, padx=10, pady=10)

        self.to_lang_optionemenu = ctk.CTkOptionMenu(controls_frame, values=list(self.languages.values()))
        self.to_lang_optionemenu.grid(row=0, column=3, padx=10, pady=10)

        self.source_text_box = ctk.CTkTextbox(self.translation_tab, width=800, height=200)
        self.source_text_box.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        translate_button = ctk.CTkButton(self.translation_tab, text="🌐 ترجمة", command=self.translate_text)
        translate_button.grid(row=2, column=0, padx=10, pady=10)

        self.translated_text_box = ctk.CTkTextbox(self.translation_tab, width=800, height=200)
        self.translated_text_box.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

    def setup_stt_tab(self):
        self.stt_tab.grid_columnconfigure(0, weight=1)
        self.stt_tab.grid_rowconfigure(1, weight=1)

        control_frame = ctk.CTkFrame(self.stt_tab)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.record_button = ctk.CTkButton(control_frame, text="🎤 بدء التسجيل", command=self.toggle_recording)
        self.record_button.grid(row=0, column=0, padx=10, pady=10)

        self.stt_text_box = ctk.CTkTextbox(self.stt_tab, width=800, height=400)
        self.stt_text_box.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.is_recording = False

    def setup_web_scraping_tab(self):
        self.web_scraping_tab.grid_columnconfigure(0, weight=1)
        self.web_scraping_tab.grid_rowconfigure(1, weight=1)

        url_frame = ctk.CTkFrame(self.web_scraping_tab)
        url_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        url_label = ctk.CTkLabel(url_frame, text="رابط الموقع:")
        url_label.grid(row=0, column=0, padx=10, pady=10)

        self.url_entry = ctk.CTkEntry(url_frame, width=400)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)

        scrape_button = ctk.CTkButton(url_frame, text="🌍 استخراج النص", command=self.scrape_website)
        scrape_button.grid(row=0, column=2, padx=10, pady=10)

        self.scraped_text_box = ctk.CTkTextbox(self.web_scraping_tab, width=800, height=400)
        self.scraped_text_box.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def setup_image_to_text_tab(self):
        self.image_to_text_tab.grid_columnconfigure(0, weight=1)
        self.image_to_text_tab.grid_rowconfigure(1, weight=1)

        upload_frame = ctk.CTkFrame(self.image_to_text_tab)
        upload_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        upload_button = ctk.CTkButton(upload_frame, text="🖼️ تحميل صورة", command=self.upload_image)
        upload_button.grid(row=0, column=0, padx=10, pady=10)

        self.image_label = ctk.CTkLabel(upload_frame, text="لم يتم تحميل صورة بعد")
        self.image_label.grid(row=0, column=1, padx=10, pady=10)

        self.image_to_text_box = ctk.CTkTextbox(self.image_to_text_tab, width=800, height=400)
        self.image_to_text_box.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    def setup_text_analysis_tab(self):
        self.text_analysis_tab.grid_columnconfigure(0, weight=1)
        self.text_analysis_tab.grid_rowconfigure(1, weight=1)

        self.analysis_text_box = ctk.CTkTextbox(self.text_analysis_tab, width=800, height=300)
        self.analysis_text_box.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        analyze_button = ctk.CTkButton(self.text_analysis_tab, text="📊 تحليل النص", command=self.analyze_text)
        analyze_button.grid(row=1, column=0, padx=10, pady=10)

        self.analysis_result_box = ctk.CTkTextbox(self.text_analysis_tab, width=800, height=300)
        self.analysis_result_box.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    def setup_word_cloud_tab(self):
        self.word_cloud_tab.grid_columnconfigure(0, weight=1)
        self.word_cloud_tab.grid_rowconfigure(1, weight=1)

        self.word_cloud_text_box = ctk.CTkTextbox(self.word_cloud_tab, width=800, height=300)
        self.word_cloud_text_box.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        generate_button = ctk.CTkButton(self.word_cloud_tab, text="☁️ إنشاء سحابة الكلمات", command=self.generate_word_cloud)
        generate_button.grid(row=1, column=0, padx=10, pady=10)

        self.word_cloud_image = ctk.CTkLabel(self.word_cloud_tab, text="")
        self.word_cloud_image.grid(row=2, column=0, padx=10, pady=10)

    def setup_pronunciation_tab(self):
        self.pronunciation_tab.grid_columnconfigure(0, weight=1)
        self.pronunciation_tab.grid_rowconfigure(1, weight=1)

        self.pronunciation_text_box = ctk.CTkTextbox(self.pronunciation_tab, width=800, height=100)
        self.pronunciation_text_box.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        pronounce_button = ctk.CTkButton(self.pronunciation_tab, text="📖 عرض دليل النطق", command=self.show_pronunciation)
        pronounce_button.grid(row=1, column=0, padx=10, pady=10)

        self.pronunciation_result_box = ctk.CTkTextbox(self.pronunciation_tab, width=800, height=400)
        self.pronunciation_result_box.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    def setup_settings_tab(self):
        self.settings_tab.grid_columnconfigure(0, weight=1)

        voice_frame = ctk.CTkFrame(self.settings_tab)
        voice_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        voice_label = ctk.CTkLabel(voice_frame, text="نوع الصوت:")
        voice_label.grid(row=0, column=0, padx=10, pady=10)

        self.voice_var = tk.StringVar(value=self.voice_gender)
        male_radio = ctk.CTkRadioButton(voice_frame, text="ذكر", variable=self.voice_var, value="male")
        male_radio.grid(row=0, column=1, padx=10, pady=10)
        female_radio = ctk.CTkRadioButton(voice_frame, text="أنثى", variable=self.voice_var, value="female")
        female_radio.grid(row=0, column=2, padx=10, pady=10)

        auto_detect_frame = ctk.CTkFrame(self.settings_tab)
        auto_detect_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.auto_detect_var = tk.BooleanVar(value=self.settings.get('auto_detect', True))
        auto_detect_checkbox = ctk.CTkCheckBox(auto_detect_frame, text="التعرف التلقائي على اللغة", variable=self.auto_detect_var)
        auto_detect_checkbox.grid(row=0, column=0, padx=10, pady=10)

        save_settings_button = ctk.CTkButton(self.settings_tab, text="💾 حفظ الإعدادات", command=self.save_settings)
        save_settings_button.grid(row=2, column=0, padx=10, pady=10)

    def load_settings(self):
        try:
            with open('settings.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def show_main_tab(self):
        self.tabview.set("الرئيسية")

    def show_translation_tab(self):
        self.tabview.set("الترجمة")

    def show_stt_tab(self):
        self.tabview.set("الكلام إلى نص")

    def show_web_scraping_tab(self):
        self.tabview.set("استخراج النص")

    def show_image_to_text_tab(self):
        self.tabview.set("الصورة إلى نص")

    def show_text_analysis_tab(self):
        self.tabview.set("تحليل النص")

    def show_word_cloud_tab(self):
        self.tabview.set("سحابة الكلمات")

    def show_pronunciation_tab(self):
        self.tabview.set("دليل النطق")

    def show_settings_tab(self):
        self.tabview.set("الإعدادات")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def change_language_event(self, new_language: str):
        for code, name in self.languages.items():
            if name == new_language:
                self.current_language = code
                break
        self.update_status(f"تم تغيير اللغة إلى: {new_language}")

    def change_speed_event(self, new_speed: float):
        self.speech_speed = new_speed
        self.speed_value_label.configure(text=f"{new_speed:.1f}x")
        self.update_status(f"تم تغيير سرعة الكلام إلى: {new_speed:.1f}x")

    def update_status(self, message: str):
        self.status_label.configure(text=message)

    def speak_text(self):
        text = self.text_box.get("1.0", "end-1c")
        if not text:
            self.update_status("الرجاء إدخال نص")
            return
        
        self.update_status("جاري تحويل النص إلى كلام...")
        self.progress_bar.set(0.5)
        
        try:
            tts = gTTS(text=text, lang=self.current_language, slow=False)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tts.save(tmp_file.name)
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                self.update_status("جاري تشغيل الصوت...")
                self.progress_bar.set(1.0)
        except Exception as e:
            self.update_status(f"خطأ: {str(e)}")
            self.progress_bar.set(0)

    def save_audio(self):
        text = self.text_box.get("1.0", "end-1c")
        if not text:
            self.update_status("الرجاء إدخال نص")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 files", "*.mp3")])
        if file_path:
            try:
                tts = gTTS(text=text, lang=self.current_language, slow=False)
                tts.save(file_path)
                self.update_status(f"تم حفظ الملف: {file_path}")
            except Exception as e:
                self.update_status(f"خطأ: {str(e)}")

    def import_text(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                self.text_box.delete("1.0", "end")
                self.text_box.insert("1.0", text)
                self.update_status(f"تم استيراد: {file_path}")
            except Exception as e:
                self.update_status(f"خطأ: {str(e)}")

    def copy_text(self):
        self.clipboard_clear()
        self.clipboard_append(self.text_box.get("1.0", "end-1c"))
        self.update_status("تم نسخ النص")

    def clear_text(self):
        self.text_box.delete("1.0", "end")
        self.update_status("تم مسح النص")

    def export_to_pdf(self):
        text = self.text_box.get("1.0", "end-1c")
        if not text:
            self.update_status("الرجاء إدخال نص")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            try:
                pdf = FPDF(orient='P', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, text)
                pdf.output(file_path)
                self.update_status(f"تم حفظ PDF: {file_path}")
            except Exception as e:
                self.update_status(f"خطأ: {str(e)}")

    def summarize_text(self):
        text = self.text_box.get("1.0", "end-1c")
        if not text:
            self.update_status("الرجاء إدخال نص")
            return
        
        try:
            sentences = sent_tokenize(text)
            words = word_tokenize(text)
            freq_dist = FreqDist(words)
            
            scored_sentences = {}
            for sentence in sentences:
                for word in word_tokenize(sentence.lower()):
                    if word in freq_dist:
                        scored_sentences[sentence] = scored_sentences.get(sentence, 0) + freq_dist[word]
            
            summary_sentences = sorted(scored_sentences, key=scored_sentences.get, reverse=True)[:len(sentences)//3]
            summary = ' '.join(summary_sentences)
            
            self.text_box.delete("1.0", "end")
            self.text_box.insert("1.0", summary)
            self.update_status("تم تلخيص النص")
        except Exception as e:
            self.update_status(f"خطأ: {str(e)}")

    def spell_check(self):
        text = self.text_box.get("1.0", "end-1c")
        if not text:
            self.update_status("الرجاء إدخال نص")
            return
        
        try:
            matches = self.language_tool.check(text)
            if matches:
                errors = "\n".join([f"الخطأ: {match.message} - الاقتراح: {match.replacements}" for match in matches])
                result_window = tk.Toplevel(self)
                result_window.title("نتائج التدقيق الإملائي")
                result_text = tk.Text(result_window, wrap=tk.WORD)
                result_text.pack(fill=tk.BOTH, expand=True)
                result_text.insert("1.0", errors)
            else:
                self.update_status("لا توجد أخطاء إملائية")
        except Exception as e:
            self.update_status(f"خطأ: {str(e)}")

    def show_history(self):
        history_window = tk.Toplevel(self)
        history_window.title("سجل التحويلات")
        history_text = tk.Text(history_window, wrap=tk.WORD)
        history_text.pack(fill=tk.BOTH, expand=True)
        history_text.insert("1.0", "\n".join(self.history) if self.history else "لا يوجد سجل")

    def translate_text(self):
        text = self.source_text_box.get("1.0", "end-1c")
        if not text:
            self.update_status("الرجاء إدخال نص")
            return
        
        try:
            self.update_status("جاري الترجمة...")
            result = self.translator.translate(text)
            self.translated_text_box.delete("1.0", "end")
            self.translated_text_box.insert("1.0", result['text'])
            self.update_status("تمت الترجمة بنجاح")
        except Exception as e:
            self.update_status(f"خطأ: {str(e)}")

    def toggle_recording(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.record_button.configure(text="🎤 إيقاف التسجيل")
            self.update_status("جاري التسجيل...")
            threading.Thread(target=self.record_audio).start()
        else:
            self.record_button.configure(text="🎤 بدء التسجيل")

    def record_audio(self):
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                audio = recognizer.listen(source)
                text = recognizer.recognize_google(audio, language=self.current_language)
                self.stt_text_box.delete("1.0", "end")
                self.stt_text_box.insert("1.0", text)
                self.update_status("تم التعرف على الكلام")
        except Exception as e:
            self.update_status(f"خطأ: {str(e)}")

    def scrape_website(self):
        url = self.url_entry.get()
        if not url:
            self.update_status("الرجاء إدخال رابط الموقع")
            return
        
        try:
            self.update_status("جاري استخراج النص...")
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            self.scraped_text_box.delete("1.0", "end")
            self.scraped_text_box.insert("1.0", text)
            self.update_status("تم استخراج النص بنجاح")
        except Exception as e:
            self.update_status(f"خطأ: {str(e)}")

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if file_path:
            self.image_label.configure(text=f"تم تحميل: {file_path}")
            # في حالة إضافة OCR يمكن معالجة الصورة هنا
            self.update_status(f"تم تحميل الصورة: {file_path}")

    def analyze_text(self):
        text = self.analysis_text_box.get("1.0", "end-1c")
        if not text:
            self.update_status("الرجاء إدخال نص")
            return
        
        try:
            blob = TextBlob(text)
            analysis = {
                "عدد الكلمات": len(text.split()),
                "عدد الأحرف": len(text),
                "عدد الجمل": len(sent_tokenize(text)),
                "الشعور": blob.sentiment.polarity
            }
            
            result = "\n".join([f"{key}: {value}" for key, value in analysis.items()])
            self.analysis_result_box.delete("1.0", "end")
            self.analysis_result_box.insert("1.0", result)
            self.update_status("تم تحليل النص")
        except Exception as e:
            self.update_status(f"خطأ: {str(e)}")

    def generate_word_cloud(self):
        text = self.word_cloud_text_box.get("1.0", "end-1c")
        if not text:
            self.update_status("الرجاء إدخال نص")
            return
        
        try:
            wordcloud = WordCloud(width=800, height=400).generate(text)
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.show()
            self.update_status("تم إنشاء سحابة الكلمات")
        except Exception as e:
            self.update_status(f"خطأ: {str(e)}")

    def show_pronunciation(self):
        word = self.pronunciation_text_box.get("1.0", "end-1c").strip()
        if not word:
            self.update_status("الرجاء إدخال كلمة")
            return
        
        try:
            pronunciations = pronouncing.search(word)
            if pronunciations:
                result = "\n".join([p.pronunciation() for p in pronunciations[:10]])
            else:
                result = "لم يتم العثور على نطق للكلمة"
            
            self.pronunciation_result_box.delete("1.0", "end")
            self.pronunciation_result_box.insert("1.0", result)
            self.update_status("تم عرض دليل النطق")
        except Exception as e:
            self.update_status(f"خطأ: {str(e)}")

    def save_settings(self):
        settings = {
            'voice_gender': self.voice_var.get(),
            'auto_detect': self.auto_detect_var.get()
        }
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
        self.update_status("تم حفظ الإعدادات")


if __name__ == "__main__":
    app = AdvancedTextToSpeechConverterApp()
    app.mainloop()

print("تم تحسين تصميم التطبيق المتقدم للتحويل من النص إلى الكلام مع واجهة مستخدم أكثر جاذبية.")
print("تم إضافة أيقونات للأزرار وتحسين تنسيق العناصر لتوفير تجربة مستخدم أفضل.")
print("تم الحفاظ على جميع الوظائف السابقة مع تحسين المظهر العام للتطبيق.")

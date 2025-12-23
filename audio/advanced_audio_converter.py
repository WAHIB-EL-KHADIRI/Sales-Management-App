import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk
import customtkinter as ctk
import speech_recognition as sr
from pydub import AudioSegment
from pydub.silence import split_on_silence
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
from deep_translator import GoogleTranslator
from gtts import gTTS
import tempfile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from docx import Document
import wave
import pyaudio
import time

def check_ffmpeg():
    import shutil
    if shutil.which('ffmpeg') is None:
        print("تحذير: لم يتم العثور على FFmpeg. يرجى التأكد من تثبيته وإضافته إلى متغير PATH.")
        print("يمكنك تحميل FFmpeg من: https://ffmpeg.org/download.html")
    else:
        print("تم العثور على FFmpeg بنجاح.")

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class Project:
    def __init__(self, name):
        self.name = name
        self.transcriptions = []
        self.timestamps = []

class AdvancedAudioTextConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("المحول المتقدم للصوت إلى نص")
        self.geometry("1200x800")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.file_path = ""
        self.projects = [Project("مشروع افتراضي")]
        self.current_project = self.projects[0]
        self.recording = False

        self.languages = {
            "ar": "العربية",
            "en": "English",
            "fr": "Français",
            "es": "Español",
            "de": "Deutsch"
        }
        self.current_language = "ar"

        self.setup_sidebar()
        self.setup_main_area()
        self.setup_status_bar()

    def setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="لوحة التحكم", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.project_label = ctk.CTkLabel(self.sidebar_frame, text="المشاريع:", anchor="w")
        self.project_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        self.project_listbox = tk.Listbox(self.sidebar_frame, bg='#2b2b2b', fg="white", selectbackground="#4a4a4a", selectforeground="white")
        self.project_listbox.grid(row=2, column=0, padx=20, pady=(5, 10), sticky="nsew")
        for project in self.projects:
            self.project_listbox.insert(tk.END, project.name)

        self.new_project_button = ctk.CTkButton(self.sidebar_frame, text="مشروع جديد", command=self.create_new_project)
        self.new_project_button.grid(row=3, column=0, padx=20, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="مظهر التطبيق:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))

        self.scaling_label = ctk.CTkLabel(self.sidebar_frame, text="حجم الواجهة:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        self.language_label = ctk.CTkLabel(self.sidebar_frame, text="لغة الإدخال:", anchor="w")
        self.language_label.grid(row=9, column=0, padx=20, pady=(10, 0))
        self.language_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=list(self.languages.values()),
                                                      command=self.change_language_event)
        self.language_optionemenu.grid(row=10, column=0, padx=20, pady=(10, 20))

    def setup_main_area(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=1, column=0, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.tabview.add("التحويل")
        self.tabview.add("التحرير")
        self.tabview.add("التحليل")

        self.setup_conversion_tab()
        self.setup_editing_tab()
        self.setup_analysis_tab()

    def setup_conversion_tab(self):
        conversion_frame = self.tabview.tab("التحويل")
        conversion_frame.grid_columnconfigure(0, weight=1)
        conversion_frame.grid_rowconfigure(3, weight=1)

        self.upload_button = ctk.CTkButton(conversion_frame, text="تحميل ملف صوتي", command=self.upload_file)
        self.upload_button.grid(row=0, column=0, padx=20, pady=10)

        self.record_button = ctk.CTkButton(conversion_frame, text="تسجيل من الميكروفون", command=self.record_audio)
        self.record_button.grid(row=0, column=1, padx=20, pady=10)

        self.progress_bar = ctk.CTkProgressBar(conversion_frame)
        self.progress_bar.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)

        self.text_box = ctk.CTkTextbox(conversion_frame, width=200, height=200)
        self.text_box.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")

        self.setup_button_frame(conversion_frame)

    def setup_editing_tab(self):
        editing_frame = self.tabview.tab("التحرير")
        editing_frame.grid_columnconfigure(0, weight=1)
        editing_frame.grid_rowconfigure(0, weight=1)

        self.edit_text_box = ctk.CTkTextbox(editing_frame, width=200, height=200)
        self.edit_text_box.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        button_frame = ctk.CTkFrame(editing_frame)
        button_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.copy_button = ctk.CTkButton(button_frame, text="نسخ", command=self.copy_text)
        self.copy_button.grid(row=0, column=0, padx=5, pady=5)

        self.paste_button = ctk.CTkButton(button_frame, text="لصق", command=self.paste_text)
        self.paste_button.grid(row=0, column=1, padx=5, pady=5)

        self.undo_button = ctk.CTkButton(button_frame, text="تراجع", command=self.undo_text)
        self.undo_button.grid(row=0, column=2, padx=5, pady=5)

        self.redo_button = ctk.CTkButton(button_frame, text="إعادة", command=self.redo_text)
        self.redo_button.grid(row=0, column=3, padx=5, pady=5)

    def setup_analysis_tab(self):
        analysis_frame = self.tabview.tab("التحليل")
        analysis_frame.grid_columnconfigure(0, weight=1)
        analysis_frame.grid_rowconfigure(1, weight=1)

        self.analyze_button = ctk.CTkButton(analysis_frame, text="تحليل النص", command=self.analyze_text)
        self.analyze_button.grid(row=0, column=0, padx=20, pady=10)

        self.analysis_result = ctk.CTkTextbox(analysis_frame, width=200, height=200)
        self.analysis_result.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

    def setup_button_frame(self, parent_frame):
        self.button_frame = ctk.CTkFrame(parent_frame)
        self.button_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

        buttons = [
            ("ترجمة", self.translate_text),
            ("نطق النص", self.speak_text),
            ("مسح", self.clear_text),
            ("حفظ", self.save_text),
            ("تصدير PDF", self.export_to_pdf),
            ("تصدير Word", self.export_to_word),
            ("السجل", self.show_history),
            ("تحليل تكرار الكلمات", self.analyze_word_frequency)
        ]

        for i, (text, command) in enumerate(buttons):
            button = ctk.CTkButton(self.button_frame, text=text, command=command)
            button.grid(row=i // 4, column=i % 4, padx=5, pady=5)

    def setup_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=30)
        self.status_bar.grid(row=1, column=1, sticky="ew")
        self.status_label = ctk.CTkLabel(self.status_bar, text="جاهز")
        self.status_label.pack(side=tk.LEFT, padx=10)

    def create_new_project(self):
        dialog = ctk.CTkInputDialog(text="أدخل اسم المشروع الجديد:", title="مشروع جديد")
        project_name = dialog.get_input()
        if project_name:
            new_project = Project(project_name)
            self.projects.append(new_project)
            self.project_listbox.insert(tk.END, project_name)
            self.current_project = new_project
            self.update_status(f"تم إنشاء مشروع جديد: {project_name}")

    def upload_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg")])
        if self.file_path:
            self.update_status("جاري معالجة الملف...")
            threading.Thread(target=self.process_audio, daemon=True).start()

    def record_audio(self):
        self.update_status("جاري التسجيل... انقر على الزر مرة أخرى للتوقف")
        self.record_button.configure(text="إيقاف التسجيل", command=self.stop_recording)
        self.recording = True
        threading.Thread(target=self.record_audio_thread, daemon=True).start()

    def stop_recording(self):
        self.recording = False
        self.record_button.configure(text="تسجيل من الميكروفون", command=self.record_audio)
        self.update_status("تم التسجيل. جاري المعالجة...")
        threading.Thread(target=self.process_audio, daemon=True).start()

    def record_audio_thread(self):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        WAVE_OUTPUT_FILENAME = "output.wav"

        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        frames = []

        while self.recording:
            data = stream.read(CHUNK)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        self.file_path = WAVE_OUTPUT_FILENAME

    def process_audio(self):
        try:
            self.progress_bar.set(0.2)
            
            # Handle different audio formats
            if self.file_path.endswith('.wav'):
                audio = AudioSegment.from_wav(self.file_path)
            elif self.file_path.endswith('.mp3'):
                audio = AudioSegment.from_mp3(self.file_path)
            elif self.file_path.endswith('.ogg'):
                audio = AudioSegment.from_ogg(self.file_path)
            else:
                audio = AudioSegment.from_file(self.file_path)
            
            chunks = split_on_silence(audio, min_silence_len=1000, silence_thresh=-40)
            
            full_text = ""
            timestamps = []
            current_time = 0

            for i, chunk in enumerate(chunks):
                self.progress_bar.set(0.2 + (0.6 * (i / len(chunks))))
                self.update_status(f"معالجة الجزء {i+1} من {len(chunks)}...")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tf:
                    chunk.export(tf.name, format="wav")
                    r = sr.Recognizer()
                    with sr.AudioFile(tf.name) as source:
                        audio_data = r.record(source)
                    try:
                        text = r.recognize_google(audio_data, language=self.current_language)
                        full_text += text + " "
                        timestamps.append((current_time, current_time + len(chunk) / 1000, text))
                        current_time += len(chunk) / 1000
                    except sr.UnknownValueError:
                        print("لم يتمكن Google Speech Recognition من فهم الصوت")
                    except sr.RequestError as e:
                        print(f"خطأ في طلب خدمة Google Speech Recognition: {e}")
                    
                    os.unlink(tf.name)

            self.text_box.delete("1.0", tk.END)
            self.text_box.insert(tk.END, full_text)
            self.current_project.transcriptions.append(full_text)
            self.current_project.timestamps = timestamps
            
            self.progress_bar.set(1.0)
            self.update_status("تم التحويل بنجاح!")

        except Exception as e:
            self.update_status(f"حدث خطأ: {str(e)}")
        finally:
            self.progress_bar.set(0)

    def translate_text(self):
        text = self.text_box.get("1.0", tk.END).strip()
        if text:
            try:
                self.update_status("جاري الترجمة...")
                translator = GoogleTranslator(source='auto', target='en')
                translated = translator.translate(text)
                self.edit_text_box.delete("1.0", tk.END)
                self.edit_text_box.insert(tk.END, translated)
                self.update_status("تمت الترجمة!")
            except Exception as e:
                self.update_status(f"خطأ في الترجمة: {str(e)}")

    def speak_text(self):
        text = self.text_box.get("1.0", tk.END).strip()
        if text:
            try:
                self.update_status("جاري إنشاء الملف الصوتي...")
                tts = gTTS(text=text, lang=self.current_language)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tf:
                    tts.save(tf.name)
                    if os.name == 'nt':  # Windows
                        os.startfile(tf.name)
                    elif os.name == 'posix':  # macOS and Linux
                        os.system(f"open {tf.name}")
                    self.update_status("جاري تشغيل النص...")
            except Exception as e:
                self.update_status(f"خطأ في النطق: {str(e)}")

    def clear_text(self):
        self.text_box.delete("1.0", tk.END)
        self.update_status("تم مسح النص!")

    def save_text(self):
        text = self.text_box.get("1.0", tk.END).strip()
        if text:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(text)
                    self.update_status("تم حفظ النص!")
                except Exception as e:
                    self.update_status(f"خطأ في الحفظ: {str(e)}")

    def export_to_pdf(self):
        text = self.text_box.get("1.0", tk.END).strip()
        if text:
            file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
            if file_path:
                try:
                    c = canvas.Canvas(file_path, pagesize=letter)
                    width, height = letter
                    c.setFont("Helvetica", 12)
                    lines = text.split('\n')
                    y = height - 50
                    for line in lines:
                        if y < 50:
                            c.showPage()
                            y = height - 50
                        c.drawString(50, y, line[:80])
                        y -= 20
                    c.save()
                    self.update_status("تم تصدير النص كملف PDF!")
                except Exception as e:
                    self.update_status(f"خطأ في التصدير: {str(e)}")

    def export_to_word(self):
        text = self.text_box.get("1.0", tk.END).strip()
        if text:
            file_path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word Files", "*.docx")])
            if file_path:
                try:
                    doc = Document()
                    doc.add_paragraph(text)
                    doc.save(file_path)
                    self.update_status("تم تصدير النص كملف Word!")
                except Exception as e:
                    self.update_status(f"خطأ في التصدير: {str(e)}")

    def show_history(self):
        history_window = ctk.CTkToplevel(self)
        history_window.title("سجل النصوص المحولة")
        history_window.geometry("600x400")

        history_text = ctk.CTkTextbox(history_window, width=550, height=350)
        history_text.pack(padx=20, pady=20)

        for i, text in enumerate(self.current_project.transcriptions, 1):
            history_text.insert(tk.END, f"{i}. {text}\n\n")

    def analyze_word_frequency(self):
        text = self.text_box.get("1.0", tk.END).strip()
        if text:
            try:
                words = text.split()
                word_freq = Counter(words)
                
                plt.figure(figsize=(10, 5))
                plt.bar(word_freq.keys(), word_freq.values())
                plt.title("تحليل تكرار الكلمات")
                plt.xlabel("الكلمات")
                plt.ylabel("التكرار")
                plt.xticks(rotation=90)
                plt.tight_layout()
                plt.show()
                self.update_status("تم إنشاء رسم بياني لتكرار الكلمات")
            except Exception as e:
                self.update_status(f"خطأ في التحليل: {str(e)}")

    def copy_text(self):
        try:
            selected_text = self.edit_text_box.selection_get()
            if selected_text:
                self.clipboard_clear()
                self.clipboard_append(selected_text)
                self.update_status("تم نسخ النص المحدد")
        except tk.TclError:
            self.update_status("لم يتم تحديد نص")

    def paste_text(self):
        try:
            clipboard_text = self.clipboard_get()
            self.edit_text_box.insert(tk.INSERT, clipboard_text)
            self.update_status("تم لصق النص")
        except tk.TclError:
            self.update_status("فشل في الحصول على نص الحافظة")

    def undo_text(self):
        try:
            self.edit_text_box.edit_undo()
            self.update_status("تم التراجع عن آخر تعديل")
        except tk.TclError:
            self.update_status("لا يوجد تعديلات للتراجع عنها")

    def redo_text(self):
        try:
            self.edit_text_box.edit_redo()
            self.update_status("تم إعادة آخر تعديل")
        except tk.TclError:
            self.update_status("لا يوجد تعديلات لإعادتها")

    def analyze_text(self):
        text = self.edit_text_box.get("1.0", tk.END).strip()
        if text:
            word_count = len(text.split())
            char_count = len(text)
            sentence_count = text.count('.') + text.count('!') + text.count('?')
            avg_word_length = char_count / word_count if word_count > 0 else 0
            
            analysis_result = f"عدد الكلمات: {word_count}\n"
            analysis_result += f"عدد الأحرف: {char_count}\n"
            analysis_result += f"عدد الجمل: {sentence_count}\n"
            analysis_result += f"متوسط طول الكلمة: {avg_word_length:.2f}\n"
            
            self.analysis_result.delete("1.0", tk.END)
            self.analysis_result.insert(tk.END, analysis_result)
            self.update_status("تم تحليل النص")
        else:
            self.update_status("الرجاء إدخال نص في صندوق التحرير")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self.update_status(f"تم تغيير المظهر إلى: {new_appearance_mode}")

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
        self.update_status(f"تم تغيير حجم الواجهة إلى: {new_scaling}")

    def change_language_event(self, new_language: str):
        for code, name in self.languages.items():
            if name == new_language:
                self.current_language = code
                break
        self.update_status(f"تم تغيير لغة الإدخال إلى: {new_language}")

    def update_status(self, message):
        self.status_label.configure(text=message)
        self.update_idletasks()

if __name__ == "__main__":
    app = AdvancedAudioTextConverterApp()
    app.mainloop()

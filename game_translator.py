# Game Translator - Subtitle Bar Edition
# แปลภาษาเกมแบบแถบ subtitle ด้านล่างจอ

import cv2
import numpy as np
import pyautogui
import pytesseract
from googletrans import Translator
import keyboard
import time
import json
import os
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont

# ============ TESSERACT CONFIG ============
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ============ CONFIG ============
CONFIG_FILE = 'translator_config.json'

class GameTranslator:
    def __init__(self):
        self.translator = Translator()
        self.running = False
        
        # Regions
        self.source_region = None
        
        # Subtitle bar settings
        self.bar_height = 60  # ความสูงแถบ subtitle
        self.bar_bg_color = (0, 0, 0)  # พื้นหลังสีดำ
        self.bar_text_color = (255, 255, 255)  # ตัวอักษรสีขาว
        self.bar_opacity = 0.85
        
        # Tkinter subtitle window
        self.subtitle_window = None
        self.subtitle_text = tk.StringVar()
        
        # Load config
        self.load_config()
        
        # Hotkeys
        self.capture_key = 'f9'
        self.setup_key = 'f8'
        self.toggle_key = 'f10'
        self.quit_key = 'esc'
        
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.source_region = config.get('source_region')
                    self.bar_height = config.get('bar_height', 60)
                    self.bar_bg_color = tuple(config.get('bar_bg_color', [0, 0, 0]))
                    self.bar_text_color = tuple(config.get('bar_text_color', [255, 255, 255]))
                    self.bar_opacity = config.get('bar_opacity', 0.85)
            except:
                pass
    
    def save_config(self):
        config = {
            'source_region': self.source_region,
            'bar_height': self.bar_height,
            'bar_bg_color': list(self.bar_bg_color),
            'bar_text_color': list(self.bar_text_color),
            'bar_opacity': self.bar_opacity
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def capture_screen(self, region):
        if not region:
            return None
        x, y, w, h = region
        try:
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except:
            return None
    
    def extract_text(self, image):
        """OCR พร้อม preprocessing"""
        if image is None:
            return ""
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Resize ใหญ่ขึ้น 2x
        height, width = gray.shape
        gray = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
        
        # Denoise
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Threshold
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        text = pytesseract.image_to_string(gray, lang='eng', config='--psm 6')
        return text.strip()
    
    def translate(self, text):
        if not text or len(text) < 2:
            return ""
        try:
            # แบ่งข้อความยาวเป็นช่วงๆ
            max_chunk = 500
            if len(text) > max_chunk:
                chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
                translated = ""
                for chunk in chunks:
                    result = self.translator.translate(chunk, src='en', dest='th')
                    translated += result.text + " "
                return translated.strip()
            else:
                return self.translator.translate(text, src='en', dest='th').text
        except Exception as e:
            print(f"[ERROR] {e}")
            return "(แปลไม่สำเร็จ)"
    
    def create_subtitle_bar(self):
        """สร้างหน้าต่าง subtitle bar ด้านล่างจอ"""
        if self.subtitle_window:
            try:
                self.subtitle_window.destroy()
            except:
                pass
        
        # หาขนาดหน้าจอ
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # สร้าง window
        self.subtitle_window = tk.Toplevel()
        self.subtitle_window.overrideredirect(True)  # ไม่มี title bar
        self.subtitle_window.attributes('-topmost', True)
        self.subtitle_window.attributes('-alpha', self.bar_opacity)
        
        # ตำแหน่งด้านล่างสุดของจอ
        bar_y = screen_height - self.bar_height - 40  # -40 เผื่อ taskbar
        self.subtitle_window.geometry(f"{screen_width}x{self.bar_height}+0+{bar_y}")
        
        # พื้นหลังสีดำ
        bg_color = f'#{self.bar_bg_color[0]:02x}{self.bar_bg_color[1]:02x}{self.bar_bg_color[2]:02x}'
        text_color = f'#{self.bar_text_color[0]:02x}{self.bar_text_color[1]:02x}{self.bar_text_color[2]:02x}'
        
        # Frame หลัก
        main_frame = tk.Frame(self.subtitle_window, bg=bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # แถบปุ่มควบคุมด้านบน (เล็กๆ)
        btn_frame = tk.Frame(main_frame, bg=bg_color, height=20)
        btn_frame.pack(fill=tk.X, side=tk.TOP)
        btn_frame.pack_propagate(False)
        
        # ปุ่มเล็กๆ
        btn_style = {'bg': '#333333', 'fg': 'white', 'font': ('Arial', 7), 
                     'bd': 0, 'padx': 5, 'pady': 0}
        
        tk.Button(btn_frame, text="▶", **btn_style, 
                 command=lambda: self.translate_and_show()).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="👁", **btn_style,
                 command=lambda: self.toggle_subtitle()).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="⚙", **btn_style,
                 command=lambda: self.setup_mode()).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="✕", **btn_style,
                 command=lambda: self.hide_subtitle()).pack(side=tk.RIGHT, padx=5)
        
        # Label แสดงข้อความ (ตรงกลาง)
        self.subtitle_label = tk.Label(main_frame, textvariable=self.subtitle_text,
                                       font=('TH Sarabun New', 16, 'bold'),
                                       bg=bg_color, fg=text_color,
                                       wraplength=screen_width - 100)
        self.subtitle_label.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # ลากย้ายได้
        def start_move(event):
            self.subtitle_window._drag_start_x = event.x
            self.subtitle_window._drag_start_y = event.y
        
        def on_move(event):
            x = self.subtitle_window.winfo_x() + event.x - self.subtitle_window._drag_start_x
            y = self.subtitle_window.winfo_y() + event.y - self.subtitle_window._drag_start_y
            self.subtitle_window.geometry(f"+{x}+{y}")
        
        main_frame.bind('<Button-1>', start_move)
        main_frame.bind('<B1-Motion>', on_move)
        self.subtitle_label.bind('<Button-1>', start_move)
        self.subtitle_label.bind('<B1-Motion>', on_move)
        
        self.subtitle_window.update()
    
    def update_subtitle_text(self, text):
        """อัปเดตข้อความ subtitle"""
        if not self.subtitle_window:
            self.create_subtitle_bar()
        
        self.subtitle_text.set(text)
        
        # ปรับขนาด font ตามความยาวข้อความ
        text_len = len(text)
        if text_len > 200:
            font_size = 12
        elif text_len > 100:
            font_size = 14
        else:
            font_size = 16
        
        self.subtitle_label.config(font=('TH Sarabun New', font_size, 'bold'))
    
    def hide_subtitle(self):
        """ซ่อน subtitle bar"""
        if self.subtitle_window:
            try:
                self.subtitle_window.destroy()
                self.subtitle_window = None
            except:
                pass
    
    def toggle_subtitle(self):
        """สลับแสดง/ซ่อน subtitle"""
        if self.subtitle_window:
            self.hide_subtitle()
        else:
            self.create_subtitle_bar()
            self.subtitle_text.set("พร้อมแปล... กด F9 เพื่อแปล")
    
    def translate_and_show(self):
        """แปลและแสดงผล"""
        if not self.source_region:
            print("⚠️ ยังไม่ได้ตั้งค่ากรอบแปล (กด F8)")
            self.subtitle_text.set("⚠️ กด F8 เพื่อตั้งค่ากรอบแปล")
            return
        
        self.subtitle_text.set("📸 กำลังแคป...")
        
        image = self.capture_screen(self.source_region)
        if image is None:
            self.subtitle_text.set("❌ แคปไม่สำเร็จ")
            return
        
        text = self.extract_text(image)
        if not text:
            self.subtitle_text.set("❌ ไม่พบข้อความ")
            return
        
        print(f"📝 พบ: {text[:60]}...")
        self.subtitle_text.set("🌐 กำลังแปล...")
        
        translated = self.translate(text)
        
        if translated:
            print(f"🌐 แปล: {translated[:60]}...")
            self.update_subtitle_text(translated)
    
    def setup_drag_mode(self):
        """โหมดลากเลือกพื้นที่"""
        print("\n🖱️ ตั้งค่ากรอบแปล")
        print("   คลิกซ้ายค้างแล้วลากเพื่อเลือกพื้นที่")
        print("   ปล่อยเมาส์ = ยืนยัน | ESC = ยกเลิก")
        
        screenshot = pyautogui.screenshot()
        bg = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        cv2.namedWindow('Setup', cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty('Setup', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        drag_start = None
        drag_end = None
        is_dragging = False
        selection = None
        
        def mouse_handler(event, x, y, flags, param):
            nonlocal drag_start, drag_end, is_dragging, selection
            if event == cv2.EVENT_LBUTTONDOWN:
                drag_start = (x, y)
                is_dragging = True
            elif event == cv2.EVENT_MOUSEMOVE and is_dragging:
                drag_end = (x, y)
            elif event == cv2.EVENT_LBUTTONUP and is_dragging:
                is_dragging = False
                if drag_start and drag_end:
                    x1, y1 = drag_start
                    x2, y2 = drag_end
                    x, y = min(x1, x2), min(y1, y2)
                    w, h = abs(x2 - x1), abs(y2 - y1)
                    if w > 30 and h > 20:
                        selection = (x, y, w, h)
        
        cv2.setMouseCallback('Setup', mouse_handler)
        
        while True:
            display = bg.copy()
            
            if is_dragging and drag_start and drag_end:
                x1, y1 = drag_start
                x2, y2 = drag_end
                overlay = display.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 255), -1)
                display = cv2.addWeighted(display, 0.6, overlay, 0.4, 0)
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 255), 2)
                w, h = abs(x2 - x1), abs(y2 - y1)
                cv2.putText(display, f"{w} x {h}", (x1 + 5, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            cv2.putText(display, "ลากเลือกกรอบแปล | ESC = ยกเลิก", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Setup', display)
            
            key = cv2.waitKey(30) & 0xFF
            if key == 27:
                break
            if selection:
                break
        
        cv2.destroyWindow('Setup')
        
        if selection:
            self.source_region = selection
            self.save_config()
            print(f"✅ บันทึกกรอบแปล: {selection}")
            self.subtitle_text.set("✅ ตั้งค่ากรอบแปลเรียบร้อย กด F9 เพื่อแปล")
            return True
        return False
    
    def setup_mode(self):
        """โหมดตั้งค่า"""
        print("\n" + "="*50)
        print("🔧 โหมดตั้งค่า")
        print("="*50)
        print("1 = ตั้งค่ากรอบแปล (ลากเมาส์)")
        print("2 = ปรับความสูงแถบ subtitle")
        print("3 = ปรับความโปร่งใส")
        print("0 = เสร็จสิ้น")
        
        while True:
            choice = input("\nเลือก: ").strip()
            
            if choice == '1':
                self.setup_drag_mode()
            
            elif choice == '2':
                heights = [50, 60, 70, 80, 100]
                idx = heights.index(self.bar_height) if self.bar_height in heights else 1
                self.bar_height = heights[(idx + 1) % len(heights)]
                print(f"📐 ความสูงแถบ: {self.bar_height}px")
                self.save_config()
                if self.subtitle_window:
                    self.create_subtitle_bar()
            
            elif choice == '3':
                self.bar_opacity = 0.7 if self.bar_opacity > 0.8 else (0.85 if self.bar_opacity > 0.7 else 0.95)
                print(f"👁️ โปร่งใส: {self.bar_opacity}")
                self.save_config()
                if self.subtitle_window:
                    self.subtitle_window.attributes('-alpha', self.bar_opacity)
            
            elif choice == '0':
                print("✅ เสร็จสิ้น")
                break
    
    def run(self):
        print("="*50)
        print("🎮 Game Translator - Subtitle Bar Edition")
        print("="*50)
        print("F8=ตั้งค่า | F9=แปล | F10=ซ่อน/แสดง | ESC=ออก")
        
        if self.source_region:
            print(f"📍 กรอบแปล: {self.source_region}")
        
        self.running = True
        
        # สร้าง tkinter root
        self.root = tk.Tk()
        self.root.withdraw()
        
        # สร้าง subtitle bar เริ่มต้น
        self.create_subtitle_bar()
        self.subtitle_text.set("🎮 พร้อมใช้งาน - กด F9 เพื่อแปล | F8 เพื่อตั้งค่า")
        
        while self.running:
            try:
                self.root.update()
            except:
                pass
            
            if keyboard.is_pressed(self.setup_key):
                self.setup_mode()
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.capture_key):
                self.translate_and_show()
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.toggle_key):
                self.toggle_subtitle()
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.quit_key):
                print("👋 ออก...")
                self.hide_subtitle()
                self.running = False
                break
            
            time.sleep(0.05)
        
        cv2.destroyAllWindows()
        try:
            self.root.destroy()
        except:
            pass
        print("✅ ปิดโปรแกรม")


if __name__ == "__main__":
    try:
        print(f"✅ Tesseract v{pytesseract.get_tesseract_version()}")
    except:
        print("⚠️ ติดตั้ง Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        input("กด Enter เพื่อออก...")
        exit(1)
    
    GameTranslator().run()

# Game Translator - Borderless Overlay Edition
# แปลภาษาเกมแบบลากเมาส์ได้ พร้อมหน้าต่างไร้ขอบ

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
from tkinter import font as tkfont
from PIL import Image, ImageDraw, ImageFont, ImageTk

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
        self.display_pos = None
        
        # Colors
        self.bg_color = (20, 20, 20)
        self.text_color = (255, 255, 255)
        self.accent_color = (0, 200, 255)
        self.opacity = 0.85
        
        # Tkinter overlay window
        self.overlay_window = None
        
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
                    self.display_pos = config.get('display_pos')
                    self.bg_color = tuple(config.get('bg_color', [20, 20, 20]))
                    self.text_color = tuple(config.get('text_color', [255, 255, 255]))
                    self.accent_color = tuple(config.get('accent_color', [0, 200, 255]))
                    self.opacity = config.get('opacity', 0.85)
            except:
                pass
    
    def save_config(self):
        config = {
            'source_region': self.source_region,
            'display_pos': self.display_pos,
            'bg_color': list(self.bg_color),
            'text_color': list(self.text_color),
            'accent_color': list(self.accent_color),
            'opacity': self.opacity
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
        """OCR พร้อม preprocessing ให้ผลลัพธ์ดีขึ้น"""
        if image is None:
            return ""
        
        # Preprocessing ให้ OCR แม่นยำขึ้น
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Resize ใหญ่ขึ้น 2x เพื่อ OCR ได้ดีขึ้น
        height, width = gray.shape
        gray = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
        
        # Denoise
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Threshold แบบ adaptive
        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        text = pytesseract.image_to_string(gray, lang='eng', config='--psm 6')
        return text.strip()
    
    def translate(self, text):
        if not text or len(text) < 2:
            return ""
        try:
            # แบ่งข้อความยาวเป็นช่วงๆ ละ 500 ตัวอักษร
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
    
    def create_overlay_window(self, text):
        """สร้างหน้าต่างลอยแบบไร้ขอบ (borderless)"""
        if self.overlay_window:
            try:
                self.overlay_window.destroy()
            except:
                pass
        
        if not self.display_pos or not text:
            return
        
        # สร้าง Tkinter window
        self.overlay_window = tk.Toplevel()
        self.overlay_window.overrideredirect(True)  # เอา title bar ออก
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.attributes('-alpha', self.opacity)
        
        # คำนวณขนาดตามข้อความ
        lines = text.split('\n')
        max_chars = max(len(line) for line in lines) if lines else 20
        num_lines = len(lines)
        
        # ขนาดพื้นฐาน
        char_width = 12
        line_height = 24
        padding = 15
        
        width = min(max(max_chars * char_width + padding * 2, 250), 500)
        height = min(num_lines * line_height + padding * 2 + 20, 400)
        
        x, y = self.display_pos
        self.overlay_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # พื้นหลัง
        bg_color = f'#{self.bg_color[0]:02x}{self.bg_color[1]:02x}{self.bg_color[2]:02x}'
        accent_color = f'#{self.accent_color[0]:02x}{self.accent_color[1]:02x}{self.accent_color[2]:02x}'
        text_color = f'#{self.text_color[0]:02x}{self.text_color[1]:02x}{self.text_color[2]:02x}'
        
        # Frame หลัก
        frame = tk.Frame(self.overlay_window, bg=bg_color, highlightbackground=accent_color, 
                         highlightthickness=2)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas สำหรับเส้นขอบ accent
        canvas = tk.Canvas(frame, bg=bg_color, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # เส้น accent ด้านซ้าย
        canvas.create_line(4, 0, 4, height, fill=accent_color, width=4)
        
        # Text widget สำหรับแสดงข้อความ (รองรับมากกว่า 1 บรรทัด + scroll ได้)
        text_widget = tk.Text(frame, wrap=tk.WORD, font=('Tahoma', 12), 
                              bg=bg_color, fg=text_color,
                              padx=10, pady=10, relief=tk.FLAT,
                              selectbackground=accent_color)
        text_widget.place(x=10, y=5, width=width-20, height=height-30)
        text_widget.insert(tk.END, text)
        text_widget.config(state=tk.DISABLED)
        
        # Label ด้านล่าง
        hint = tk.Label(frame, text="F9=แปล | F10=ซ่อน", font=('Tahoma', 9),
                       bg=bg_color, fg='#999999')
        hint.place(x=10, y=height-22)
        
        # ทำให้ลากย้ายได้
        def start_move(event):
            self.overlay_window._drag_start_x = event.x
            self.overlay_window._drag_start_y = event.y
        
        def on_move(event):
            x = self.overlay_window.winfo_x() + event.x - self.overlay_window._drag_start_x
            y = self.overlay_window.winfo_y() + event.y - self.overlay_window._drag_start_y
            self.overlay_window.geometry(f"+{x}+{y}")
            self.display_pos = (x, y)
        
        frame.bind('<Button-1>', start_move)
        frame.bind('<B1-Motion>', on_move)
        
        # ปิดเมื่อคลิกขวา
        def close_overlay(event):
            self.hide_overlay()
        
        frame.bind('<Button-3>', close_overlay)
        
        self.overlay_window.update()
    
    def hide_overlay(self):
        if self.overlay_window:
            try:
                self.overlay_window.destroy()
                self.overlay_window = None
            except:
                pass
    
    def translate_and_show(self):
        if not self.source_region:
            print("⚠️ ยังไม่ได้ตั้งค่ากรอบแปล (กด F8)")
            return
        
        print("📸 กำลังแคป...")
        image = self.capture_screen(self.source_region)
        if image is None:
            return
        
        text = self.extract_text(image)
        if not text:
            print("❌ ไม่พบข้อความ")
            return
        
        print(f"📝 พบ: {text[:80]}...")
        print(f"   (ความยาว: {len(text)} ตัวอักษร)")
        
        translated = self.translate(text)
        
        if translated:
            print(f"🌐 แปล: {translated[:80]}...")
            self.create_overlay_window(translated)
    
    def setup_drag_mode(self, mode_name, save_callback):
        """โหมดลากเลือกพื้นที่"""
        print(f"\n🖱️ ตั้งค่า{mode_name}")
        print("   คลิกซ้ายค้างแล้วลากเพื่อเลือกพื้นที่")
        print("   ปล่อยเมาส์ = ยืนยัน | ESC = ยกเลิก")
        
        # แคปหน้าจอ
        screenshot = pyautogui.screenshot()
        bg = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # สร้าง fullscreen window
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
            
            # วาดกรอบขณะลาก
            if is_dragging and drag_start and drag_end:
                x1, y1 = drag_start
                x2, y2 = drag_end
                
                # กรอบโปร่งใส
                overlay = display.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 255), -1)
                display = cv2.addWeighted(display, 0.6, overlay, 0.4, 0)
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 255), 2)
                
                # ขนาด
                w, h = abs(x2 - x1), abs(y2 - y1)
                cv2.putText(display, f"{w} x {h}", (x1 + 5, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # คำแนะนำ
            cv2.putText(display, f"{mode_name}: ลากเลือก | ESC = ยกเลิก", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Setup', display)
            
            key = cv2.waitKey(30) & 0xFF
            if key == 27:  # ESC
                break
            if selection:
                break
        
        cv2.destroyWindow('Setup')
        
        if selection:
            save_callback(selection)
            print(f"✅ บันทึก: {selection}")
            return selection
        return None
    
    def setup_mode(self):
        """โหมดตั้งค่า"""
        print("\n" + "="*50)
        print("🔧 โหมดตั้งค่า")
        print("="*50)
        print("1 = ตั้งค่ากรอบแปล (ลากเมาส์)")
        print("2 = ตั้งค่าตำแหน่งแสดงผล")
        print("3 = ปรับสีพื้นหลัง")
        print("4 = ปรับสีตัวอักษร")
        print("5 = ปรับความโปร่งใส")
        print("0 = เสร็จสิ้น")
        
        while True:
            choice = input("\nเลือก: ").strip()
            
            if choice == '1':
                result = self.setup_drag_mode("กรอบแปล", 
                    lambda r: setattr(self, 'source_region', r))
                if result:
                    self.save_config()
            
            elif choice == '2':
                result = self.setup_drag_mode("ตำแหน่งแสดงผล",
                    lambda r: setattr(self, 'display_pos', (r[0], r[1])))
                if result:
                    self.save_config()
            
            elif choice == '3':
                colors = [(0,0,0), (20,20,20), (40,0,0), (0,40,0), (0,0,40)]
                idx = colors.index(self.bg_color) if self.bg_color in colors else -1
                self.bg_color = colors[(idx + 1) % len(colors)]
                print(f"🎨 พื้นหลัง: {self.bg_color}")
                self.save_config()
            
            elif choice == '4':
                colors = [(255,255,255), (255,255,200), (200,255,200), (255,200,200)]
                idx = colors.index(self.text_color) if self.text_color in colors else -1
                self.text_color = colors[(idx + 1) % len(colors)]
                print(f"🎨 ตัวอักษร: {self.text_color}")
                self.save_config()
            
            elif choice == '5':
                self.opacity = 0.7 if self.opacity > 0.8 else (0.85 if self.opacity > 0.7 else 0.95)
                print(f"👁️ โปร่งใส: {self.opacity}")
                self.save_config()
            
            elif choice == '0':
                print("✅ เสร็จสิ้น")
                break
    
    def run(self):
        print("="*50)
        print("🎮 Game Translator - Borderless Overlay")
        print("="*50)
        print("F8=ตั้งค่า | F9=แปล | F10=ซ่อน/แสดง | ESC=ออก")
        
        if self.source_region:
            print(f"📍 กรอบแปล: {self.source_region}")
        if self.display_pos:
            print(f"📍 แสดงผล: {self.display_pos}")
        
        self.running = True
        showing = True
        
        # สร้าง tkinter root (hidden)
        self.root = tk.Tk()
        self.root.withdraw()
        
        while self.running:
            if keyboard.is_pressed(self.setup_key):
                self.setup_mode()
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.capture_key):
                if showing:
                    self.translate_and_show()
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.toggle_key):
                showing = not showing
                if not showing:
                    self.hide_overlay()
                else:
                    print("👁️ แสดงผล - กด F9 เพื่อแปล")
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.quit_key):
                print("👋 ออก...")
                self.hide_overlay()
                self.running = False
                break
            
            try:
                self.root.update()
            except:
                pass
            
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

# Game Translator - Modern Overlay with Mouse Drag Selection
# แปลภาษาเกมแบบลากเมาส์ได้ พร้อมหน้าต่างลอยสวยงาม

import cv2
import numpy as np
import pyautogui
import pytesseract
from googletrans import Translator
import keyboard
import time
import json
import os
import threading
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
        self.display_pos = None
        
        # Colors
        self.bg_color = (0, 0, 0)
        self.text_color = (255, 255, 255)
        self.accent_color = (0, 255, 255)
        self.opacity = 0.75
        
        # Drag state
        self.is_dragging = False
        self.drag_start = None
        self.drag_end = None
        
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
                    self.bg_color = tuple(config.get('bg_color', [0, 0, 0]))
                    self.text_color = tuple(config.get('text_color', [255, 255, 255]))
                    self.accent_color = tuple(config.get('accent_color', [0, 255, 255]))
                    self.opacity = config.get('opacity', 0.75)
                print(f"📂 โหลดการตั้งค่าเรียบร้อย")
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
            print("💾 บันทึกการตั้งค่า")
        except:
            pass
    
    def get_font(self, size=18):
        thai_fonts = [
            'C:/Windows/Fonts/THSarabunNew.ttf',
            'C:/Windows/Fonts/tahoma.ttf',
            'C:/Windows/Fonts/segoeui.ttf',
        ]
        for path in thai_fonts:
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
        return ImageFont.load_default()
    
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
        if image is None:
            return ""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, lang='eng')
        return text.strip()
    
    def translate(self, text):
        if not text or len(text) < 2:
            return ""
        try:
            return self.translator.translate(text, src='en', dest='th').text
        except:
            return "(แปลไม่สำเร็จ)"
    
    def create_modern_overlay(self, text, max_width=350):
        """สร้าง overlay แบบ modern"""
        font = self.get_font(18)
        font_small = self.get_font(12)
        
        # ตัดข้อความให้พอดีความกว้าง
        words = text.split()
        lines = []
        current = ""
        
        dummy = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy)
        
        for word in words:
            test = current + word + " "
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width - 30:
                lines.append(current)
                current = word + " "
            else:
                current = test
        lines.append(current)
        
        # คำนวณขนาด
        line_h = draw.textbbox((0, 0), "Ay", font=font)[3] - draw.textbbox((0, 0), "Ay", font=font)[1]
        height = 15 + len(lines) * (line_h + 5) + 25
        width = max_width
        
        # สร้างภาพ
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # พื้นหลังแบบ modern (มีความโปร่งใส)
        bg = self.bg_color + (int(255 * self.opacity),)
        draw.rounded_rectangle([0, 0, width, height], radius=10, fill=bg)
        
        # เส้นขอบด้านซ้าย (accent)
        draw.rectangle([0, 0, 4, height], fill=self.accent_color + (255,))
        
        # ข้อความ
        y = 12
        for line in lines:
            draw.text((15, y), line, fill=self.text_color + (255,), font=font)
            y += line_h + 5
        
        # hint
        hint = "F9=แปล | F10=ซ่อน/แสดง"
        draw.text((15, height - 18), hint, fill=(150, 150, 150, 200), font=font_small)
        
        return img
    
    def show_translation(self, text):
        if not self.display_pos or not text:
            return
        
        overlay = self.create_modern_overlay(text)
        arr = np.array(overlay)
        cv2.imshow('Translation', cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR))
        cv2.moveWindow('Translation', self.display_pos[0], self.display_pos[1])
        cv2.setWindowProperty('Translation', cv2.WND_PROP_TOPMOST, 1)
        cv2.waitKey(1)
    
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
        
        print(f"📝 พบ: {text[:60]}...")
        translated = self.translate(text)
        
        if translated:
            print(f"🌐 แปล: {translated[:60]}...")
            self.show_translation(translated)
    
    def setup_with_drag(self, mode_name, save_callback):
        """ตั้งค่าด้วยการลากเมาส์พร้อมกรอบแสดงผล"""
        print(f"\n🖱️ ตั้งค่า{mode_name}")
        print("   คลิกซ้ายค้างแล้วลากเพื่อเลือกพื้นที่")
        print("   ปล่อยเมาส์เพื่อยืนยัน")
        print("   กด ESC เพื่อยกเลิก")
        
        # สร้างหน้าต่างโปร่งใสสำหรับลาก
        cv2.namedWindow('DragSetup', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('DragSetup', cv2.WND_PROP_FULLSCREEN, 1)
        cv2.setWindowProperty('DragSetup', cv2.WND_PROP_TOPMOST, 1)
        
        selection = None
        
        def mouse_handler(event, x, y, flags, param):
            nonlocal selection
            if event == cv2.EVENT_LBUTTONDOWN:
                self.drag_start = (x, y)
                self.is_dragging = True
            elif event == cv2.EVENT_MOUSEMOVE and self.is_dragging:
                self.drag_end = (x, y)
            elif event == cv2.EVENT_LBUTTONUP and self.is_dragging:
                self.is_dragging = False
                if self.drag_start and self.drag_end:
                    x1, y1 = self.drag_start
                    x2, y2 = self.drag_end
                    x, y = min(x1, x2), min(y1, y2)
                    w, h = abs(x2 - x1), abs(y2 - y1)
                    if w > 30 and h > 20:
                        selection = (x, y, w, h)
        
        cv2.setMouseCallback('DragSetup', mouse_handler)
        
        # แคปหน้าจอปัจจุบันเป็น background
        screenshot = pyautogui.screenshot()
        bg = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        while True:
            # แสดงภาพพร้อมกรอบลาก
            display = bg.copy()
            
            if self.is_dragging and self.drag_start and self.drag_end:
                x1, y1 = self.drag_start
                x2, y2 = self.drag_end
                
                # วาดกรอบแบบโปร่งใส
                overlay = display.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 255), -1)
                display = cv2.addWeighted(display, 0.7, overlay, 0.3, 0)
                
                # แสดงขนาด
                w, h = abs(x2 - x1), abs(y2 - y1)
                cv2.putText(display, f"{w}x{h}", (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # แสดงคำแนะนำ
            cv2.putText(display, f"{mode_name}: ลากเพื่อเลือก | ESC = ยกเลิก", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('DragSetup', display)
            
            key = cv2.waitKey(30) & 0xFF
            if key == 27:  # ESC
                break
            if selection:
                break
        
        cv2.destroyWindow('DragSetup')
        
        if selection:
            save_callback(selection)
            return selection
        return None
    
    def setup_mode(self):
        """โหมดตั้งค่า"""
        print("\n" + "="*50)
        print("🔧 โหมดตั้งค่า")
        print("="*50)
        print("1 = ตั้งค่ากรอบแปล (ลากเมาส์)")
        print("2 = ตั้งค่าตำแหน่งแสดงผล (ลากเมาส์)")
        print("3 = ปรับสีพื้นหลัง")
        print("4 = ปรับสีตัวอักษร")
        print("5 = ปรับความโปร่งใส")
        print("0 = เสร็จสิ้น")
        
        while True:
            choice = input("\nเลือก: ").strip()
            
            if choice == '1':
                result = self.setup_with_drag("กรอบแปล", 
                    lambda r: setattr(self, 'source_region', r))
                if result:
                    print(f"✅ กรอบแปล: {result}")
                    self.save_config()
            
            elif choice == '2':
                result = self.setup_with_drag("ตำแหน่งแสดงผล",
                    lambda r: setattr(self, 'display_pos', (r[0], r[1])))
                if result:
                    print(f"✅ ตำแหน่งแสดงผล: {self.display_pos}")
                    self.save_config()
            
            elif choice == '3':
                colors = [(0,0,0), (30,30,30), (50,0,0), (0,50,0), (0,0,50), (50,50,0)]
                idx = colors.index(self.bg_color) if self.bg_color in colors else -1
                self.bg_color = colors[(idx + 1) % len(colors)]
                print(f"🎨 พื้นหลัง: {self.bg_color}")
                self.save_config()
            
            elif choice == '4':
                colors = [(255,255,255), (255,255,200), (200,255,200), (200,200,255), (255,255,0)]
                idx = colors.index(self.text_color) if self.text_color in colors else -1
                self.text_color = colors[(idx + 1) % len(colors)]
                print(f"🎨 ตัวอักษร: {self.text_color}")
                self.save_config()
            
            elif choice == '5':
                self.opacity = 0.5 if self.opacity > 0.7 else (0.65 if self.opacity > 0.5 else 0.8)
                print(f"👁️ โปร่งใส: {self.opacity}")
                self.save_config()
            
            elif choice == '0':
                print("✅ เสร็จสิ้น")
                break
    
    def run(self):
        print("="*50)
        print("🎮 Game Translator - แปลเกมแบบลากเมาส์")
        print("="*50)
        print("F8 = ตั้งค่า | F9 = แปล | F10 = ซ่อน/แสดง | ESC = ออก")
        
        if self.source_region:
            print(f"📍 กรอบแปล: {self.source_region}")
        if self.display_pos:
            print(f"📍 แสดงผล: {self.display_pos}")
        
        self.running = True
        showing = True
        
        cv2.namedWindow('Translation', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Translation', 350, 100)
        
        while self.running:
            if keyboard.is_pressed(self.setup_key):
                self.setup_mode()
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.capture_key):
                self.translate_and_show()
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.toggle_key):
                showing = not showing
                if not showing:
                    try:
                        cv2.destroyWindow('Translation')
                    except:
                        pass
                print(f"👁️ {'แสดง' if showing else 'ซ่อน'}ผล")
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.quit_key):
                print("👋 ออก...")
                self.running = False
                break
            
            time.sleep(0.1)
        
        cv2.destroyAllWindows()
        print("✅ ปิดโปรแกรม")


if __name__ == "__main__":
    try:
        import pytesseract
        print(f"✅ Tesseract v{pytesseract.get_tesseract_version()}")
    except:
        print("⚠️ ติดตั้ง Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
        input("กด Enter เพื่อออก...")
        exit(1)
    
    GameTranslator().run()

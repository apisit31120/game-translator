# Game Translator - Visual Overlay with Draggable Regions
# แปลภาษาเกมแบบลากกรอบเองได้ พร้อมปรับสีและตำแหน่งได้

import cv2
import numpy as np
import pyautogui
import pytesseract
from googletrans import Translator
import keyboard
import time
import json
import os
from PIL import Image, ImageDraw, ImageFont

# ============ CONFIG ============
CONFIG_FILE = 'translator_config.json'

class GameTranslator:
    def __init__(self):
        self.translator = Translator()
        self.running = False
        
        # Regions (x, y, w, h)
        self.source_region = None      # กรอบที่จะ OCR
        self.display_region = None     # ตำแหน่งแสดงผล
        
        # Colors (BGR format for OpenCV)
        self.bg_color = (30, 30, 30)           # พื้นหลัง (เทาเข้ม)
        self.text_color = (255, 255, 200)      # ตัวอักษร (ขาวเหลือง)
        self.border_color = (100, 200, 255)    # กรอบ (ฟ้า)
        self.header_color = (100, 255, 100)    # หัวข้อ (เขียว)
        
        # Display settings
        self.font_size = 20
        self.opacity = 0.9           # ความโปร่งใส (0-1)
        self.show_original = True    # แสดงข้อความต้นฉบับ
        
        # State
        self.last_text = ""
        self.last_translated = ""
        self.is_selecting = False
        self.drag_start = None
        self.current_drag = None
        self.drag_mode = None  # 'source' or 'display'
        
        # Load saved config
        self.load_config()
        
        # Hotkeys
        self.capture_key = 'f9'
        self.setup_key = 'f8'        # เปิดโหมดตั้งค่า
        self.toggle_display = 'f10'  # เปิด/ปิดการแสดงผล
        self.quit_key = 'esc'
        
    def get_font(self, size=20):
        """หา font ที่รองรับภาษาไทย"""
        thai_fonts = [
            'C:/Windows/Fonts/THSarabunNew.ttf',
            'C:/Windows/Fonts/tahoma.ttf',
            'C:/Windows/Fonts/segoeui.ttf',
            'C:/Windows/Fonts/arial.ttf',
            '/usr/share/fonts/truetype/thai/TlwgTypist.ttf',
            '/System/Library/Fonts/Supplemental/Tahoma.ttf',
        ]
        
        for font_path in thai_fonts:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        
        return ImageFont.load_default()
    
    def load_config(self):
        """โหลดการตั้งค่าที่บันทึกไว้"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.source_region = config.get('source_region')
                    self.display_region = config.get('display_region')
                    self.bg_color = tuple(config.get('bg_color', [30, 30, 30]))
                    self.text_color = tuple(config.get('text_color', [255, 255, 200]))
                    self.border_color = tuple(config.get('border_color', [100, 200, 255]))
                    self.header_color = tuple(config.get('header_color', [100, 255, 100]))
                    self.font_size = config.get('font_size', 20)
                    self.opacity = config.get('opacity', 0.9)
                    self.show_original = config.get('show_original', True)
                print(f"📂 โหลดการตั้งค่าจาก {CONFIG_FILE}")
            except Exception as e:
                print(f"⚠️  ไม่สามารถโหลด config: {e}")
    
    def save_config(self):
        """บันทึกการตั้งค่า"""
        config = {
            'source_region': self.source_region,
            'display_region': self.display_region,
            'bg_color': list(self.bg_color),
            'text_color': list(self.text_color),
            'border_color': list(self.border_color),
            'header_color': list(self.header_color),
            'font_size': self.font_size,
            'opacity': self.opacity,
            'show_original': self.show_original
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"💾 บันทึกการตั้งค่าไปที่ {CONFIG_FILE}")
        except Exception as e:
            print(f"❌ ไม่สามารถบันทึก config: {e}")
    
    def capture_region(self, region):
        """แคปเฉพาะพื้นที่ที่กำหนด"""
        if not region:
            return None
        x, y, w, h = region
        try:
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except:
            return None
    
    def extract_text(self, image):
        """OCR ดึงข้อความ"""
        if image is None:
            return ""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        text = pytesseract.image_to_string(gray, lang='eng')
        return text.strip()
    
    def translate_text(self, text):
        """แปลเป็นไทย"""
        if not text or len(text) < 2:
            return ""
        try:
            result = self.translator.translate(text, src='en', dest='th')
            return result.text
        except Exception as e:
            print(f"[ERROR] Translation: {e}")
            return "(แปลไม่สำเร็จ)"
    
    def draw_rounded_rect(self, draw, xy, radius, fill, outline=None, width=1):
        """วาดสี่เหลี่ยมมุมมน"""
        x1, y1, x2, y2 = xy
        r = radius
        
        # วาดสี่เหลี่ยมหลัก
        draw.rectangle([x1+r, y1, x2-r, y2], fill=fill)
        draw.rectangle([x1, y1+r, x2, y2-r], fill=fill)
        
        # วาดมุม (4 วงกลม)
        draw.ellipse([x1, y1, x1+r*2, y1+r*2], fill=fill)
        draw.ellipse([x2-r*2, y1, x2, y1+r*2], fill=fill)
        draw.ellipse([x1, y2-r*2, x1+r*2, y2], fill=fill)
        draw.ellipse([x2-r*2, y2-r*2, x2, y2], fill=fill)
        
        if outline:
            # วาดเส้นขอบ
            draw.arc([x1, y1, x1+r*2, y1+r*2], 180, 270, fill=outline, width=width)
            draw.arc([x2-r*2, y1, x2, y1+r*2], 270, 360, fill=outline, width=width)
            draw.arc([x1, y2-r*2, x1+r*2, y2], 90, 180, fill=outline, width=width)
            draw.arc([x2-r*2, y2-r*2, x2, y2], 0, 90, fill=outline, width=width)
            draw.line([x1+r, y1, x2-r, y1], fill=outline, width=width)
            draw.line([x1+r, y2, x2-r, y2], fill=outline, width=width)
            draw.line([x1, y1+r, x1, y2-r], fill=outline, width=width)
            draw.line([x2, y1+r, x2, y2-r], fill=outline, width=width)
    
    def create_overlay(self, original, translated, width=400, max_height=300):
        """สร้างภาพ overlay แบบสวยงาม"""
        # โหลด font
        font_header = self.get_font(self.font_size + 4)
        font_text = self.get_font(self.font_size)
        font_small = self.get_font(self.font_size - 4)
        
        # คำนวณความสูงที่ต้องการ
        lines = []
        if self.show_original and original:
            lines.append(("EN:", original, self.header_color))
        if translated:
            lines.append(("TH:", translated, self.border_color))
        
        # สร้าง dummy image เพื่อคำนวณขนาด
        dummy = Image.new('RGB', (1, 1))
        draw_dummy = ImageDraw.Draw(dummy)
        
        total_height = 20  # padding top
        line_heights = []
        
        for header, text, color in lines:
            # คำนวณความสูง header
            bbox = draw_dummy.textbbox((0, 0), header, font=font_header)
            header_h = bbox[3] - bbox[1]
            
            # ตัดข้อความให้พอดีความกว้าง
            words = text.split()
            wrapped_lines = []
            current_line = ""
            for word in words:
                test = current_line + word + " "
                bbox = draw_dummy.textbbox((0, 0), test, font=font_text)
                if bbox[2] - bbox[0] > width - 40:
                    wrapped_lines.append(current_line)
                    current_line = word + " "
                else:
                    current_line = test
            wrapped_lines.append(current_line)
            
            bbox = draw_dummy.textbbox((0, 0), "A", font=font_text)
            text_h = (bbox[3] - bbox[1]) * len(wrapped_lines)
            
            line_height = header_h + text_h + 15
            line_heights.append((header, wrapped_lines, color, line_height))
            total_height += line_height
        
        total_height += 20  # padding bottom
        
        # สร้างภาพจริง
        img = Image.new('RGBA', (width, total_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # วาดพื้นหลังแบบโปร่งใส
        bg_rgba = self.bg_color + (int(255 * self.opacity),)
        self.draw_rounded_rect(draw, [0, 0, width, total_height], 15, bg_rgba, self.border_color, 2)
        
        # วาดข้อความ
        y = 20
        for header, wrapped_lines, header_color, line_h in line_heights:
            # Header
            draw.text((20, y), header, fill=header_color, font=font_header)
            y += 25
            
            # Text
            for line in wrapped_lines:
                draw.text((20, y), line, fill=self.text_color, font=font_text)
                bbox = draw_dummy.textbbox((0, 0), line, font=font_text)
                y += (bbox[3] - bbox[1]) + 5
            y += 10
        
        # วาด hint ด้านล่าง
        hint = "F9=แปล | F8=ตั้งค่า | ESC=ออก"
        draw.text((width//2 - 100, total_height - 25), hint, 
                  fill=(150, 150, 150), font=font_small)
        
        return img, total_height
    
    def show_translation(self, original, translated):
        """แสดงผลการแปลบนหน้าจอ"""
        if not self.display_region:
            print("⚠️  ยังไม่ได้ตั้งค่าตำแหน่งแสดงผล (กด F8)")
            return
        
        overlay_img, height = self.create_overlay(original, translated)
        
        # แปลงเป็น numpy array สำหรับ OpenCV
        overlay_array = np.array(overlay_img)
        overlay_cv = cv2.cvtColor(overlay_array, cv2.COLOR_RGBA2BGRA)
        
        # แสดงผล
        cv2.imshow('Translation', overlay_cv[:, :, :3])
        
        # ย้ายหน้าต่างไปตำแหน่งที่กำหนด
        x, y, w, h = self.display_region
        cv2.moveWindow('Translation', x, y)
        cv2.setWindowProperty('Translation', cv2.WND_PROP_TOPMOST, 1)
        cv2.waitKey(1)
    
    def translate_and_show(self):
        """แปลและแสดงผล"""
        if not self.source_region:
            print("⚠️  ยังไม่ได้ตั้งค่ากรอบแปล (กด F8)")
            return
        
        print("📸 กำลังแคป...")
        image = self.capture_region(self.source_region)
        if image is None:
            return
        
        text = self.extract_text(image)
        if not text:
            print("❌ ไม่พบข้อความ")
            return
        
        if text == self.last_text:
            print("(ข้อความซ้ำ ข้าม)")
            return
        
        print(f"📝 พบ: {text[:80]}...")
        
        translated = self.translate_text(text)
        if translated:
            print(f"🌐 แปล: {translated}")
            self.last_text = text
            self.last_translated = translated
            self.show_translation(text, translated)
    
    def mouse_callback(self, event, x, y, flags, param):
        """จัดการ mouse events สำหรับลากกรอบ"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.is_selecting = True
            self.drag_start = (x, y)
        
        elif event == cv2.EVENT_MOUSEMOVE and self.is_selecting:
            self.current_drag = (x, y)
        
        elif event == cv2.EVENT_LBUTTONUP and self.is_selecting:
            self.is_selecting = False
            if self.drag_start and self.current_drag:
                x1, y1 = self.drag_start
                x2, y2 = self.current_drag
                
                # ปรับให้ x1 < x2, y1 < y2
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                
                w, h = x2 - x1, y2 - y1
                
                if w > 50 and h > 30:  # ขนาดขั้นต่ำ
                    if self.drag_mode == 'source':
                        self.source_region = (x1, y1, w, h)
                        print(f"✅ ตั้งค่ากรอบแปล: ({x1}, {y1}, {w}, {h})")
                    elif self.drag_mode == 'display':
                        self.display_region = (x1, y1, 400, 200)  # ขนาดคงที่
                        print(f"✅ ตั้งค่าตำแหน่งแสดงผล: ({x1}, {y1})")
                    self.save_config()
    
    def setup_mode(self):
        """โหมดตั้งค่า - ลากกรอบและปรับสี"""
        print("\n" + "="*50)
        print("🔧 โหมดตั้งค่า")
        print("="*50)
        print("1. ลากกรอบแปล (Source) - กด 'S'")
        print("2. ลากตำแหน่งแสดงผล (Display) - กด 'D'")
        print("3. ปรับสีพื้นหลัง - กด 'B'")
        print("4. ปรับสีตัวอักษร - กด 'T'")
        print("5. ปรับความโปร่งใส - กด 'O'")
        print("6. เสร็จสิ้น - กด 'Q'")
        print("="*50)
        
        # สร้างหน้าต่างสำหรับตั้งค่า
        cv2.namedWindow('Setup')
        cv2.setMouseCallback('Setup', self.mouse_callback)
        
        while True:
            # แคปหน้าจอปัจจุบัน
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # วาดกรอบที่ตั้งค่าไว้
            if self.source_region:
                x, y, w, h = self.source_region
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "SOURCE", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            if self.display_region:
                x, y, w, h = self.display_region
                cv2.rectangle(frame, (x, y), (x+400, y+200), (255, 100, 100), 2)
                cv2.putText(frame, "DISPLAY", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 100), 2)
            
            # วาดกรอบที่กำลังลาก
            if self.is_selecting and self.drag_start and self.current_drag:
                x1, y1 = self.drag_start
                x2, y2 = self.current_drag
                color = (0, 255, 255) if self.drag_mode == 'source' else (255, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # แสดงสถานะ
            status_text = f"BG: {self.bg_color} | Text: {self.text_color} | Opacity: {self.opacity:.1f}"
            cv2.putText(frame, status_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            cv2.imshow('Setup', frame)
            
            key = cv2.waitKey(50) & 0xFF
            
            if key == ord('s'):
                self.drag_mode = 'source'
                print("🖱️  โหมด: ลากกรอบแปล (Source)")
            
            elif key == ord('d'):
                self.drag_mode = 'display'
                print("🖱️  โหมด: ลากตำแหน่งแสดงผล (Display)")
            
            elif key == ord('b'):
                # ปรับสีพื้นหลัง (cycle ไปเรื่อยๆ)
                presets = [
                    (30, 30, 30),      # เทาเข้ม
                    (0, 0, 0),         # ดำ
                    (50, 0, 0),        # แดงเข้ม
                    (0, 50, 0),        # เขียวเข้ม
                    (0, 0, 50),        # น้ำเงินเข้ม
                    (50, 50, 0),       # น้ำตาล
                    (25, 25, 50),      # ม่วงเข้ม
                ]
                idx = presets.index(self.bg_color) if self.bg_color in presets else 0
                self.bg_color = presets[(idx + 1) % len(presets)]
                print(f"🎨 พื้นหลัง: {self.bg_color}")
                self.save_config()
            
            elif key == ord('t'):
                # ปรับสีตัวอักษร
                presets = [
                    (255, 255, 200),   # ขาวเหลือง
                    (255, 255, 255),   # ขาว
                    (200, 255, 200),   # เขียวอ่อน
                    (200, 200, 255),   # ฟ้าอ่อน
                    (255, 200, 200),   # ชมพูอ่อน
                    (255, 255, 0),     # เหลือง
                    (0, 255, 255),     # ฟ้า cyan
                ]
                idx = presets.index(self.text_color) if self.text_color in presets else 0
                self.text_color = presets[(idx + 1) % len(presets)]
                print(f"🎨 ตัวอักษร: {self.text_color}")
                self.save_config()
            
            elif key == ord('o'):
                # ปรับความโปร่งใส
                self.opacity = 0.5 if self.opacity > 0.8 else (0.7 if self.opacity > 0.6 else 0.9)
                print(f"👁️ ความโปร่งใส: {self.opacity}")
                self.save_config()
            
            elif key == ord('q') or key == 27:  # Q or ESC
                break
        
        cv2.destroyWindow('Setup')
        print("✅ เสร็จสิ้นการตั้งค่า\n")
    
    def run(self):
        """รันโปรแกรมหลัก"""
        print("="*60)
        print("🎮 Game Translator - แปลภาษาเกมแบบลากกรอบได้")
        print("="*60)
        print("\n⌨️  คำสั่ง:")
        print("   F8     = เปิดโหมดตั้งค่า (ลากกรอบ, ปรับสี)")
        print("   F9     = แปลทันที")
        print("   F10    = เปิด/ปิดการแสดงผล")
        print("   ESC    = ออกจากโปรแกรม")
        print("\n⚠️  ต้องติดตั้ง Tesseract OCR ก่อน!")
        print("="*60)
        
        # แสดงการตั้งค่าปัจจุบัน
        if self.source_region:
            print(f"📍 กรอบแปล: {self.source_region}")
        if self.display_region:
            print(f"📍 ตำแหน่งแสดงผล: {self.display_region}")
        
        self.running = True
        display_enabled = True
        
        # สร้างหน้าต่างแสดงผล (ซ่อนไว้ก่อน)
        cv2.namedWindow('Translation', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Translation', 400, 200)
        
        while self.running:
            if keyboard.is_pressed(self.setup_key):
                self.setup_mode()
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.capture_key):
                self.translate_and_show()
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.toggle_display):
                display_enabled = not display_enabled
                if not display_enabled:
                    try:
                        cv2.destroyWindow('Translation')
                    except:
                        pass  # หน้าต่างอาจยังไม่ถูกสร้าง
                print(f"👁️  แสดงผล: {'เปิด ✅' if display_enabled else 'ปิด ❌'}")
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.quit_key):
                print("👋 กำลังปิดโปรแกรม...")
                self.running = False
                break
            
            time.sleep(0.1)
        
        cv2.destroyAllWindows()
        print("✅ ปิดโปรแกรมเรียบร้อย")


if __name__ == "__main__":
    # ตรวจสอบ Tesseract path (Windows)
    import sys
    if sys.platform == 'win32':
        tesseract_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"✅ พบ Tesseract: {path}")
                break
        else:
            print("⚠️  ไม่พบ Tesseract! กรุณาติดตั้งก่อน")
            print("   Download: https://github.com/UB-Mannheim/tesseract/wiki")
    
    app = GameTranslator()
    app.run()

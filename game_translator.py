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
        
        # Default settings for display region (black bg, transparent, white text)
        self.default_display_bg = (0, 0, 0)        # ดำ
        self.default_display_opacity = 0.6         # โปร่งใสนิดหน่อย
        self.default_display_text = (255, 255, 255) # ขาว
        
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
        """แสดงผลการแปลบนหน้าจอแบบ GUI overlay"""
        if not self.display_region:
            print("⚠️  ยังไม่ได้ตั้งค่าตำแหน่งแสดงผล (กด F8)")
            return
        
        # ใช้สี default สำหรับ display (ดำ โปร่งใส ขาว)
        old_bg = self.bg_color
        old_opacity = self.opacity
        old_text = self.text_color
        
        self.bg_color = self.default_display_bg
        self.opacity = self.default_display_opacity
        self.text_color = self.default_display_text
        
        overlay_img, height = self.create_overlay(original, translated)
        
        # คืนค่าเดิม
        self.bg_color = old_bg
        self.opacity = old_opacity
        self.text_color = old_text
        
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
        
        print(f"🖥️  แสดงผลที่ตำแหน่ง ({x}, {y}) - กด F10 เพื่อซ่อน/แสดง")
    
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
    
    def setup_mode_simple(self):
        """โหมดตั้งค่าแบบง่าย - ใช้ CLI + F1 สำหรับเลือกจุด"""
        print("\n" + "="*60)
        print("🔧 โหมดตั้งค่า (แบบง่าย)")
        print("="*60)
        print("\n📋 คำสั่ง:")
        print("   1 = ตั้งค่ากรอบแปล (กด F1 สองครั้ง)")
        print("   2 = ตั้งค่าตำแหน่งแสดงผล (กด F1 สองครั้ง)")
        print("   3 = ปรับสีพื้นหลัง")
        print("   4 = ปรับสีตัวอักษร")
        print("   5 = ปรับความโปร่งใส")
        print("   6 = ดูการตั้งค่าปัจจุบัน")
        print("   0 = เสร็จสิ้น")
        print("\n💡 วิธีใช้ F1: เลื่อนเมาส์ไปที่มุมแรก → กด F1")
        print("               เลื่อนเมาส์ไปที่มุมตรงข้าม → กด F1 อีกครั้ง")
        print("="*60)
        
        while True:
            choice = input("\nเลือกคำสั่ง (0-6): ").strip()
            
            if choice == '1':
                self.set_region_by_points("แปล (Source)", 'source')
            
            elif choice == '2':
                self.set_region_by_points("แสดงผล (Display)", 'display')
            
            elif choice == '3':
                self.cycle_color('bg')
            
            elif choice == '4':
                self.cycle_color('text')
            
            elif choice == '5':
                self.cycle_opacity()
            
            elif choice == '6':
                self.show_current_settings()
            
            elif choice == '0':
                print("✅ เสร็จสิ้นการตั้งค่า\n")
                break
            
            else:
                print("❌ ไม่รู้จำคำสั่งนี้")
    
    def set_region_by_points(self, name, mode):
        """ตั้งค่าพื้นที่แบบกด F1 สองครั้ง พร้อมแสดง preview"""
        print(f"\n🖱️  ตั้งค่าพื้นที่{name}")
        print("   1. เลื่อนเมาส์ไปที่มุมแรก (ซ้ายบน) → กด F1")
        print("   2. เลื่อนเมาส์ไปที่มุมตรงข้าม (ขวาล่าง) → กด F1")
        print("   3. ดู preview กรอบ → กด Enter เพื่อยืนยัน หรือ ESC เพื่อยกเลิก")
        print("\n   รอการกด F1 ครั้งที่ 1...")
        
        point1 = None
        point2 = None
        
        # รอจุดที่ 1
        while point1 is None:
            if keyboard.is_pressed('f1'):
                point1 = pyautogui.position()
                print(f"   ✅ จุดที่ 1: ({point1.x}, {point1.y})")
                time.sleep(0.5)
                break
            time.sleep(0.05)
        
        print("   รอการกด F1 ครั้งที่ 2...")
        
        # รอจุดที่ 2
        while point2 is None:
            if keyboard.is_pressed('f1'):
                point2 = pyautogui.position()
                print(f"   ✅ จุดที่ 2: ({point2.x}, {point2.y})")
                time.sleep(0.5)
                break
            time.sleep(0.05)
        
        # คำนวณสี่เหลี่ยม
        x1, y1 = point1.x, point1.y
        x2, y2 = point2.x, point2.y
        
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        
        if w < 50 or h < 30:
            print(f"   ❌ พื้นที่เล็กเกินไป ({w}x{h}) ต้อง > 50x30")
            return
        
        # แสดง preview กรอบบนหน้าจอ
        print(f"\n📐 Preview: ขนาด {w}x{h} pixels ที่ตำแหน่ง ({x}, {y})")
        print("   กด Enter เพื่อยืนยัน หรือ ESC เพื่อยกเลิก")
        
        # สร้างหน้าต่าง preview แบบ transparent overlay
        preview_img = np.zeros((h, w, 4), dtype=np.uint8)
        preview_img[:, :, 0] = 0      # B
        preview_img[:, :, 1] = 255    # G (เขียว)
        preview_img[:, :, 2] = 0      # R
        preview_img[:, :, 3] = 80     # Alpha (โปร่ง)
        
        # วาดกรอบ
        cv2.rectangle(preview_img, (0, 0), (w-1, h-1), (0, 255, 0, 255), 3)
        
        # แสดง preview
        cv2.namedWindow('Preview', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('Preview', cv2.WND_PROP_TOPMOST, 1)
        cv2.moveWindow('Preview', x, y)
        cv2.imshow('Preview', preview_img)
        cv2.waitKey(1)
        
        # รอการยืนยัน
        confirmed = False
        while True:
            if keyboard.is_pressed('return') or keyboard.is_pressed('enter'):
                confirmed = True
                break
            elif keyboard.is_pressed('esc'):
                confirmed = False
                break
            time.sleep(0.05)
        
        cv2.destroyWindow('Preview')
        time.sleep(0.3)
        
        if not confirmed:
            print("   ❌ ยกเลิก")
            return
        
        # บันทึก
        if mode == 'source':
            self.source_region = (x, y, w, h)
            print(f"   ✅ บันทึกกรอบแปล: ({x}, {y}, {w}, {h})")
        else:
            # ตำแหน่งแสดงผล: ใช้ค่า default (ดำ โปร่งใส ตัวอักษรขาว)
            self.display_region = (x, y, 400, 200)
            self.bg_color = self.default_display_bg
            self.opacity = self.default_display_opacity
            self.text_color = self.default_display_text
            print(f"   ✅ บันทึกตำแหน่งแสดงผล: ({x}, {y})")
            print(f"   🎨 ตั้งค่า: พื้นหลังดำ โปร่งใส ตัวอักษรขาว")
        
        self.save_config()
    
    def cycle_color(self, color_type):
        """เปลี่ยนสีแบบ cycle"""
        if color_type == 'bg':
            presets = [
                (30, 30, 30), (0, 0, 0), (50, 0, 0), (0, 50, 0),
                (0, 0, 50), (50, 50, 0), (25, 25, 50)
            ]
            idx = presets.index(self.bg_color) if self.bg_color in presets else -1
            self.bg_color = presets[(idx + 1) % len(presets)]
            print(f"🎨 พื้นหลัง: {self.bg_color}")
        else:
            presets = [
                (255, 255, 200), (255, 255, 255), (200, 255, 200),
                (200, 200, 255), (255, 200, 200), (255, 255, 0), (0, 255, 255)
            ]
            idx = presets.index(self.text_color) if self.text_color in presets else -1
            self.text_color = presets[(idx + 1) % len(presets)]
            print(f"🎨 ตัวอักษร: {self.text_color}")
        
        self.save_config()
    
    def cycle_opacity(self):
        """เปลี่ยนความโปร่งใส"""
        values = [0.9, 0.7, 0.5, 0.3]
        idx = values.index(self.opacity) if self.opacity in values else -1
        self.opacity = values[(idx + 1) % len(values)]
        print(f"👁️ ความโปร่งใส: {self.opacity}")
        self.save_config()
    
    def show_current_settings(self):
        """แสดงการตั้งค่าปัจจุบัน"""
        print("\n📊 การตั้งค่าปัจจุบัน:")
        print(f"   กรอบแปล: {self.source_region or 'ยังไม่ตั้ง'}")
        print(f"   ตำแหน่งแสดงผล: {self.display_region or 'ยังไม่ตั้ง'}")
        print(f"   สีพื้นหลัง: {self.bg_color}")
        print(f"   สีตัวอักษร: {self.text_color}")
        print(f"   ความโปร่งใส: {self.opacity}")
    
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
                self.setup_mode_simple()
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

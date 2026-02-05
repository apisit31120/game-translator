# Game Translator - Real-time Screen Translation for PC Games
# แปลภาษาเกม PC แบบ Real-time พร้อมเสียงพากย์

import cv2
import numpy as np
import pyautogui
import pytesseract
from googletrans import Translator
import pyttsx3
import keyboard
import time
import threading
from PIL import Image, ImageDraw, ImageFont
import win32gui
import win32con

class GameTranslator:
    def __init__(self):
        self.translator = Translator()
        self.tts_engine = pyttsx3.init()
        
        # ตั้งค่า TTS (เสียงภาษาไทย)
        self.tts_engine.setProperty('rate', 150)  # ความเร็วเสียง
        voices = self.tts_engine.getProperty('voices')
        # หาเสียงภาษาไทย ถ้ามี
        for voice in voices:
            if 'thai' in voice.name.lower() or 'th' in voice.id.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
        
        self.running = False
        self.last_text = ""
        self.cooldown = 3  # วินาทีระหว่างการแปล (กันซ้ำ)
        self.last_capture_time = 0
        
        # ตั้งค่า hotkey
        self.capture_key = 'f9'      # กด F9 เพื่อแปล
        self.toggle_key = 'f10'      # กด F10 เพื่อเปิด/ปิด auto mode
        self.quit_key = 'esc'        # กด ESC เพื่อออก
        
    def capture_screen(self, region=None):
        """แคปหน้าจอ ถ้าไม่ใส่ region จะแคปทั้งจอ"""
        screenshot = pyautogui.screenshot(region=region)
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def extract_text(self, image):
        """ดึงข้อความจากภาพด้วย OCR"""
        # แปลงเป็น grayscale สำหรับ OCR ที่ดีขึ้น
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # ปรับ contrast เพื่อให้อ่านง่ายขึ้น
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # OCR ด้วย Tesseract
        # lang='eng' สำหรับภาษาอังกฤษ
        text = pytesseract.image_to_string(gray, lang='eng')
        return text.strip()
    
    def translate_text(self, text):
        """แปลข้อความเป็นไทย"""
        if not text or len(text) < 3:
            return None
        try:
            result = self.translator.translate(text, src='en', dest='th')
            return result.text
        except Exception as e:
            print(f"[ERROR] Translation failed: {e}")
            return None
    
    def speak_text(self, text):
        """ใช้ TTS อ่านข้อความ"""
        if text and text != self.last_text:
            print(f"🔊 พูด: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            self.last_text = text
    
    def get_font(self, size=20):
        """หา font ที่รองรับภาษาไทย"""
        # ลองหา font ภาษาไทยจากระบบ
        thai_fonts = [
            'C:/Windows/Fonts/THSarabunNew.ttf',  # Thai Sarabun (Windows)
            'C:/Windows/Fonts/tahoma.ttf',         # Tahoma (มี Thai glyph)
            'C:/Windows/Fonts/segoeui.ttf',        # Segoe UI
            'C:/Windows/Fonts/arial.ttf',          # Arial
            '/usr/share/fonts/truetype/thai/TlwgTypist.ttf',  # Linux
            '/System/Library/Fonts/Supplemental/Tahoma.ttf',  # macOS
        ]
        
        for font_path in thai_fonts:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        
        # ถ้าไม่เจอ ใช้ default font
        return ImageFont.load_default()
    
    def show_overlay(self, original, translated):
        """แสดงข้อความแปลบนหน้าจอ (overlay) - รองรับภาษาไทยด้วย PIL"""
        # สร้างภาพด้วย PIL
        width, height = 800, 200
        img_pil = Image.new('RGB', (width, height), (30, 30, 30))  # พื้นหลังสีเทาเข้ม
        draw = ImageDraw.Draw(img_pil)
        
        # โหลด fonts
        font_header = self.get_font(22)
        font_text = self.get_font(18)
        font_small = self.get_font(14)
        
        # วาดข้อความ EN
        draw.text((10, 10), "EN:", fill=(100, 255, 100), font=font_header)
        en_text = original[:80] if len(original) > 80 else original
        draw.text((60, 12), en_text, fill=(255, 255, 255), font=font_text)
        
        # วาดข้อความ TH
        draw.text((10, 50), "TH:", fill=(100, 200, 255), font=font_header)
        th_text = translated[:80] if len(translated) > 80 else translated
        draw.text((60, 52), th_text, fill=(255, 255, 200), font=font_text)
        
        # วาดคำแนะนำ
        draw.text((10, 170), "กด F9 แปล | F10 Auto | ESC ออก", fill=(150, 150, 150), font=font_small)
        
        # แปลง PIL Image เป็น OpenCV format
        img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
        cv2.imshow('Game Translator', img_cv)
        cv2.setWindowProperty('Game Translator', cv2.WND_PROP_TOPMOST, 1)
        cv2.waitKey(1)
    
    def process_frame(self):
        """ประมวลผล 1 frame"""
        current_time = time.time()
        if current_time - self.last_capture_time < self.cooldown:
            return
        
        self.last_capture_time = current_time
        
        # แคปหน้าจอ
        print("📸 กำลังแคปหน้าจอ...")
        image = self.capture_screen()
        
        # OCR ดึงข้อความ
        text = self.extract_text(image)
        if not text:
            print("❌ ไม่พบข้อความ")
            return
        
        print(f"📝 พบข้อความ: {text[:100]}...")
        
        # แปลภาษา
        translated = self.translate_text(text)
        if not translated:
            return
        
        print(f"🌐 แปล: {translated}")
        
        # แสดง overlay
        self.show_overlay(text, translated)
        
        # อ่านออกเสียง
        self.speak_text(translated)
    
    def run(self):
        """รันโปรแกรมหลัก"""
        print("="*50)
        print("🎮 Game Translator - แปลเกมแบบ Real-time")
        print("="*50)
        print("\n⌨️  คำสั่ง:")
        print(f"   {self.capture_key.upper():8} = แปลทันที (manual)")
        print(f"   {self.toggle_key.upper():8} = เปิด/ปิด Auto mode")
        print(f"   {self.quit_key.upper():8} = ออกจากโปรแกรม")
        print("\n⚠️  ต้องติดตั้ง Tesseract OCR ก่อน!")
        print("   Download: https://github.com/UB-Mannheim/tesseract/wiki")
        print("="*50)
        
        auto_mode = False
        self.running = True
        
        # สร้างหน้าต่าง overlay
        cv2.namedWindow('Game Translator', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Game Translator', 800, 200)
        
        # แสดงหน้าต่างเริ่มต้น
        self.show_overlay("Press F9 to translate", "กด F9 เพื่อแปล")
        
        last_auto_time = 0
        
        while self.running:
            # ตรวจจับ hotkey
            if keyboard.is_pressed(self.capture_key):
                self.process_frame()
                time.sleep(0.5)  # กันการกดซ้ำ
            
            elif keyboard.is_pressed(self.toggle_key):
                auto_mode = not auto_mode
                status = "เปิด ✅" if auto_mode else "ปิด ❌"
                print(f"🔄 Auto mode: {status}")
                time.sleep(0.5)
            
            elif keyboard.is_pressed(self.quit_key):
                print("👋 กำลังปิดโปรแกรม...")
                self.running = False
                break
            
            # Auto mode: แปลทุก 5 วินาที
            if auto_mode and time.time() - last_auto_time > 5:
                self.process_frame()
                last_auto_time = time.time()
            
            # อัปเดตหน้าต่าง
            cv2.waitKey(100)
        
        cv2.destroyAllWindows()
        print("✅ ปิดโปรแกรมเรียบร้อย")


def quick_translate():
    """โหมดแปลเร็ว (แคปจอเดียว)"""
    print("📸 แคปหน้าจอ...")
    image = pyautogui.screenshot()
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    print("🔍 กำลังอ่านข้อความ...")
    text = pytesseract.image_to_string(image, lang='eng')
    
    if text.strip():
        print(f"📝 พบ: {text[:200]}...")
        translator = Translator()
        translated = translator.translate(text, src='en', dest='th').text
        print(f"\n🌐 แปล:\n{translated}\n")
        
        # อ่านให้ฟัง
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.say(translated)
        engine.runAndWait()
    else:
        print("❌ ไม่พบข้อความในภาพ")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_translate()
    else:
        app = GameTranslator()
        app.run()

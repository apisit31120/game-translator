# 🎮 Game Translator

**แปลภาษาเกม PC แบบ Real-time พร้อมเสียงพากย์**

โปรแกรม Python สำหรับแคปหน้าจอเกม → OCR ดึงข้อความ → แปลเป็นไทย → อ่านออกเสียง (TTS)

---

## ✨ Features

- 📸 **แคปหน้าจอ** อัตโนมัติด้วย hotkey
- 🔍 **OCR ดึงข้อความ** จากภาพ (รองรับภาษาอังกฤษ)
- 🌐 **แปลเป็นไทย** ด้วย Google Translate
- 🔊 **อ่านออกเสียง** ด้วย Windows TTS (ฟรี!)
- 🖥️ **Overlay แสดงผล** บนหน้าจอแบบ always-on-top
- ⚡ **Auto Mode** แปลอัตโนมัติทุก 5 วินาที
- ⌨️ **Hotkeys** ใช้งานง่ายขณะเล่นเกม

---

## 📋 สิ่งที่ต้องติดตั้งก่อน

### 1. Python 3.8 ขึ้นไป
Download: https://www.python.org/downloads/

### 2. Tesseract OCR (สำคัญ!)
Download: https://github.com/UB-Mannheim/tesseract/wiki
- Windows: โหลดไฟล์ `.exe` แล้วติดตั้ง
- **จด path ไว้** เช่น `C:\Program Files\Tesseract-OCR\tesseract.exe`

---

## 🚀 วิธีติดตั้ง

### Step 1: Clone หรือ Download โปรเจค

```bash
git clone https://github.com/yourusername/game-translator.git
cd game-translator
```

หรือ download ZIP แล้วแตกไฟล์

### Step 2: ติดตั้ง Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: ตั้งค่า Tesseract Path

แก้ไขไฟล์ `game_translator.py` บรรทัดแรก ๆ (ถ้าจำเป็น):

```python
# Windows: ระบุ path ของ tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

---

## 🎮 วิธีใช้งาน

### รันโปรแกรม

```bash
python game_translator.py
```

### Hotkeys

| ปุ่ม | ฟังก์ชัน |
|-----|----------|
| `F9` | แปลทันที (manual) |
| `F10` | เปิด/ปิด Auto Mode |
| `ESC` | ออกจากโปรแกรม |

### โหมดทำงาน

1. **Manual Mode (F9)** - กดเมื่อต้องการแปล
2. **Auto Mode (F10)** - แปลอัตโนมัติทุก 5 วินาที

### โหมดแปลเร็ว (แคปครั้งเดียว)

```bash
python game_translator.py --quick
```

---

## ⚠️ หมายเหตุ

- โปรแกรมใช้ **Google Translate** อาจมี delay บ้างถ้าเน็ตช้า
- OCR อาจไม่แม่นยำ 100% กับฟอนต์แปลก ๆ ในเกม
- แนะนำให้เล่นเกม **Windowed Mode** หรือ **Borderless Window** จะใช้ง่ายกว่า Fullscreen
- TTS ภาษาไทยบน Windows อาจไม่สมบูรณ์ ถ้าไม่มี Thai voice pack

---

## 🔧 แก้ไขปัญหา

### "TesseractNotFoundError"
ติดตั้ง Tesseract ไม่สำเร็จ หรือ path ไม่ถูกต้อง

### "No module named 'xxx'"
```bash
pip install -r requirements.txt
```

### TTS ไม่ออกเสียง
- ตรวจสอบว่าเปิดเสียงคอมไว้
- ลองเปลี่ยน voice ในโค้ด

---

## 📄 License

MIT License - ใช้ฟรี แก้ไขได้ แชร์ได้!

---

## 🙏 Credits

- OCR: [Tesseract](https://github.com/tesseract-ocr/tesseract)
- Translation: [Google Translate](https://translate.google.com)
- TTS: [pyttsx3](https://github.com/nateshmbhat/pyttsx3)

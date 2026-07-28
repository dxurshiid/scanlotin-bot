import ssl
import asyncio
import logging
import os
import sys
import time
from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
import aiogram.enums
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from deep_translator import GoogleTranslator
import dotenv
import pypdf
import requests

# SSL sertifikat xatolarini to'liq chetlab o'tish
ssl._create_default_https_context = ssl._create_unverified_context

# .env fayldan token va admin id ni o'qish
dotenv.load_dotenv()
TOKEN = os.getenv("TOKEN") or os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

dp = Dispatcher()

last_request_time = {}
SPAM_DELAY = 2

def translate_to_uzbek(text: str) -> str:
    try:
        translator = GoogleTranslator(source='auto', target='uz')
        result = translator.translate(text)
        return result if result else text
    except Exception as e:
        logging.error(f"Tarjima qilishda xatolik: {e}")
        return text

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_name = message.from_user.first_name
    await message.answer(
        f"Assalomu alaykum, {user_name}! 👋\n\n"
        "Men ScanLotin botiman. 📄\n"
        "PDF hujjat yoki matn yuboring – ularni o'qib, o'zbek tiliga tarjima qilib va Lotin alifbosida taqdim etaman.\n\n"
        "📖 /help - Qo'llanma"
    )

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    await message.answer(
        "📊 **Bot Statistikasi:**\n\n"
        "✅ Holati: Faol va barqaror ishlayapti (Server: Render Free)\n"
        "🛡️ Xavfsizlik: Anti-Flood yoqilgan\n"
        "🌐 Tarjima tizimi: Ulangan (Deep-Translator)"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 **Qo'llanma:**\n\n"
        "1. Botga istalgan matnni yuboring — u avtomatik ravishda o'zbek tiliga tarjima qilinib, Lotin alifbosida qaytariladi.\n"
        "2. PDF formatidagi hujjatni yuborsangiz, bot uning ichidagi matnni o'qib tarjima qiladi."
    )

@dp.message(F.document)
async def handle_document(message: Message):
    user_id = message.from_user.id
    current_time = time.time()
    if user_id in last_request_time and current_time - last_request_time[user_id] < SPAM_DELAY:
        return
    last_request_time[user_id] = current_time

    document = message.document
    if not document.file_name.endswith('.pdf'):
        await message.answer("Iltimos, faqat PDF formatidagi hujjat yuboring.")
        return

    waiting_msg = await message.answer("📄 Hujjat qabul qilindi, o'qilmoqda...")
    
    try:
        file_info = await message.bot.get_file(document.file_id)
        file_path = file_info.file_path
        downloaded_file = await message.bot.download_file(file_path)
        
        reader = pypdf.PdfReader(downloaded_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        
        if not text.strip():
            await waiting_msg.edit_text("PDF fayl ichidan matn topib bo'lmadi.")
            return

        await waiting_msg.edit_text("🔄 Matn tarjima qilinmoqda...")
        
        # Matn uzun bo'lsa bo'laklab tarjima qilish
        max_chunk = 4000
        translated_full = ""
        for i in range(0, len(text), max_chunk):
            chunk = text[i:i + max_chunk]
            translated_full += translate_to_uzbek(chunk) + "\n"

        if len(translated_full) > 4000:
            translated_full = translated_full[:4000] + "\n...(davomi qisqartirildi)"

        await waiting_msg.edit_text(f"✅ **Natija (Lotin alifbosida):**\n\n{translated_full}")

    except Exception as e:
        logging.error(f"PDF o'qishda xatolik: {e}")
        await waiting_msg.edit_text("Hujjatni qayta ishlashda xatolik yuz berdi.")

@dp.message(F.text)
async def handle_text(message: Message):
    user_id = message.from_user.id
    current_time = time.time()
    if user_id in last_request_time and current_time - last_request_time[user_id] < SPAM_DELAY:
        return
    last_request_time[user_id] = current_time

    text = message.text
    translated = translate_to_uzbek(text)
    await message.answer(f"✅ **Tarjima:**\n\n{translated}")

async def main():
    if not TOKEN:
        logging.error("BOT_TOKEN topilmadi!")
        return
        
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=aiogram.enums.ParseMode.MARKDOWN),
    )
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Render port talab qilgani uchun oddiy web server
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading

    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive!")

    def run_server():
        server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
        server.serve_forever()

    threading.Thread(target=run_server, daemon=True).start()

    # Botni ishga tushirish
    asyncio.run(main())

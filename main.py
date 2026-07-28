import ssl

# SSL sertifikat xatolarini to'liq chetlab o'tish
ssl._create_default_https_context = ssl._create_unverified_context

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
import easyocr
import pypdf
import requests

# .env fayldan token va admin id ni o'qish
dotenv.load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Majburiy obuna kanalingiz
CHANNEL_USERNAME = "@arenastars1"

dp = Dispatcher()

print("OCR modeli yuklanmoqda, iltimos kuting...")
reader = easyocr.Reader(["ru", "en"], gpu=False)
print("OCR modeli tayyor!")

last_request_time = {}
SPAM_DELAY = 2


def translate_to_uzbek(text: str) -> str:
  try:
    translated = GoogleTranslator(source="auto", target="uz").translate(text)
    return translated if translated else text
  except Exception as e:
    print(f"Tarjima qilishda xatolik: {e}")
    return text


def to_latin(text: str) -> str:
  cyrillic_to_latin = {
      "а": "a",
      "б": "b",
      "в": "v",
      "г": "g",
      "д": "d",
      "е": "e",
      "ё": "yo",
      "ж": "j",
      "з": "z",
      "и": "i",
      "й": "y",
      "к": "k",
      "л": "l",
      "м": "m",
      "н": "n",
      "о": "o",
      "п": "p",
      "р": "r",
      "с": "s",
      "т": "t",
      "у": "u",
      "ф": "f",
      "х": "x",
      "ц": "ts",
      "ч": "ch",
      "ш": "sh",
      "щ": "sh",
      "ъ": "",
      "ы": "i",
      "ь": "",
      "э": "e",
      "ю": "yu",
      "я": "ya",
      "ў": "o'",
      "ғ": "g'",
      "қ": "q",
      "ҳ": "h",
      "А": "A",
      "Б": "B",
      "В": "V",
      "Г": "G",
      "Д": "D",
      "Е": "E",
      "Ё": "Yo",
      "Ж": "J",
      "З": "Z",
      "И": "I",
      "Й": "Y",
      "К": "K",
      "Л": "L",
      "М": "M",
      "Н": "N",
      "О": "O",
      "П": "P",
      "Р": "R",
      "С": "S",
      "Т": "T",
      "У": "U",
      "Ф": "F",
      "Х": "X",
      "Ц": "Ts",
      "Ч": "Ch",
      "Ш": "Sh",
      "Щ": "Sh",
      "Ъ": "",
      "Ы": "I",
      "Ь": "",
      "Э": "E",
      "Ю": "Yu",
      "Я": "Ya",
      "Ў": "O'",
      "Ғ": "G'",
      "Қ": "Q",
      "Ҳ": "H",
  }
  result = ""
  for char in text:
    result += cyrillic_to_latin.get(char, char)
  return result


async def check_subscription(bot: Bot, user_id: int) -> bool:
  try:
    member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
    if member.status in ["creator", "administrator", "member"]:
      return True
    return False
  except Exception as e:
    print(f"Obunani tekshirishda xatolik: {e}")
    return True


# /start buyrug'i
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
  user_id = message.from_user.id
  user_name = html.quote(message.from_user.first_name)
  bot_instance = message.bot

  is_subscribed = await check_subscription(bot_instance, user_id)

  if not is_subscribed:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Kanalga obuna bo'lish",
                url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="✅ Obuna bo'ldim", callback_data="check_sub"
            ),
        ],
    ])
    await message.answer(
        f"Hurmatli {user_name}, botdan foydalanish uchun avval kanalimizga obuna bo'ling!",
        reply_markup=keyboard,
    )
    return

  welcome_text = (
      f"Assalomu alaykum, {user_name}! 👋\n\n"
      "Men ScanLotin botiman. 📸\n"
      "Rasm, PDF yoki matn yuboring — ularni o'qib, o'zbek tiliga tarjima qilib va Lotin alifbosida taqdim etaman.\n\n"
      "📖 /help - Qo'llanma"
  )
  await message.answer(welcome_text, parse_mode=aiogram.enums.ParseMode.MARKDOWN)


# /admin buyrug'i (Faqat ADMIN_ID uchun)
@dp.message(Command("admin"))
async def admin_panel(message: Message):
  if message.from_user.id != ADMIN_ID:
    await message.answer("❌ Kechirasiz, bu buyruq faqat bot admini uchun!")
    return

  admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
      [
          InlineKeyboardButton(
              text="📊 Bot holati", callback_data="admin_stats"
          )
      ],
  ])
  await message.answer(
      "👑 **Admin boshqaruv paneliga xush kelibsiz!**",
      reply_markup=admin_keyboard,
      parse_mode=aiogram.enums.ParseMode.MARKDOWN,
  )


@dp.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: Message):
  if callback.from_user.id != ADMIN_ID:
    return
  await callback.answer()
  await callback.message.edit_text(
      "📊 **Bot Statistikasi:**\n\n"
      "✅ Holati: Faol va ishlayapti\n"
      "🛡 Xavfsizlik: Anti-Flood yoqilgan\n"
      "🌐 Tarjima tizimi: Ulangan (Deep-Translator)",
      parse_mode=aiogram.enums.ParseMode.MARKDOWN,
  )


# /help buyrug'i
@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
  user_id = message.from_user.id
  if not await check_subscription(message.bot, user_id):
    await message.answer(
        "❌ Botdan foydalanish uchun avval kanalimizga obuna bo'ling!"
    )
    return

  help_text = (
      "🤖 **ScanLotin Bot Yo'riqnomasi:**\n\n"
      "1️⃣ **Rasm:** Matnli rasmni yuboring, tarjima qilib lotinlashtirib beradi.\n"
      "2️⃣ **PDF:** PDF fayllardagi matnlarni ham o'qiydi.\n"
      "3️⃣ **Matn:** Matn yuborsangiz o'zbek tiliga tarjima qilib lotinlashtiradi."
  )
  await message.answer(help_text, parse_mode=aiogram.enums.ParseMode.MARKDOWN)


@dp.callback_query(F.data == "check_sub")
async def process_check_sub(callback_query):
  user_id = callback_query.from_user.id
  user_name = html.quote(callback_query.from_user.first_name)

  if await check_subscription(callback_query.bot, user_id):
    await callback_query.message.delete()
    await callback_query.message.answer(
        f"Assalomu alaykum, {user_name}! Xush kelibsiz. Marhamat, fayl yoki matn yuboring."
    )
  else:
    await callback_query.answer(
        "❌ Siz hali kanalga obuna bo'lmagansiz!", show_alert=True
    )


# Rasm yoki PDF kelganda
@dp.message(F.photo | F.document)
async def handle_media(message: Message):
  user_id = message.from_user.id
  bot_instance = message.bot

  current_time = time.time()
  if user_id in last_request_time:
    if current_time - last_request_time[user_id] < SPAM_DELAY:
      await message.answer(
          "⚠️ Iltimos, so'rovlar orasida 2 soniya tanaffus saqlang!"
      )
      return
  last_request_time[user_id] = current_time

  if not await check_subscription(bot_instance, user_id):
    await message.answer("❌ Avval kanalimizga obuna bo'ling!")
    return

  wait_msg = await message.answer("⏳ Faylga ishlov berilmoqda...")

  try:
    raw_text = ""
    if message.photo:
      file_id = message.photo[-1].file_id
      file_info = await bot_instance.get_file(file_id)
      file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
      response_file = requests.get(file_url)
      with open("downloaded_image.jpg", "wb") as f:
        f.write(response_file.content)
      result = reader.readtext("downloaded_image.jpg", detail=0)
      raw_text = " ".join(result)

    elif message.document:
      if message.document.mime_type == "application/pdf":
        file_info = await bot_instance.get_file(message.document.file_id)
        file_url = (
            f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        )
        response_file = requests.get(file_url)
        with open("downloaded_document.pdf", "wb") as f:
          f.write(response_file.content)
        reader_pdf = pypdf.PdfReader("downloaded_document.pdf")
        pdf_text = [
            p.extract_text() for p in reader_pdf.pages if p.extract_text()
        ]
        raw_text = "\n".join(pdf_text)
      else:
        await message.answer(
            "❌ Faqat rasm yoki PDF formatidagi hujjat qabul qilinadi!"
        )
        await bot_instance.delete_message(
            chat_id=message.chat.id, message_id=wait_msg.message_id
        )
        return

    if not raw_text.strip():
      await message.answer("⚠️ Fayldan matn topilmadi.")
    else:
      translated = translate_to_uzbek(raw_text)
      final_text = to_latin(translated)
      if len(final_text) > 4000:
        final_text = final_text[:4000] + "\n\n... (qisqartirildi)"
      await message.answer(
          f"Natija:\n\n`{final_text}`",
          parse_mode=aiogram.enums.ParseMode.MARKDOWN,
      )

    await bot_instance.delete_message(
        chat_id=message.chat.id, message_id=wait_msg.message_id
    )
  except Exception as e:
    print(f"Xato: {e}")
    await message.answer("❌ Xatolik yuz berdi.")


# Oddiy matn kelganda
@dp.message(F.text)
async def handle_text(message: Message):
  user_id = message.from_user.id
  if message.text.startswith("/"):
    return

  current_time = time.time()
  if user_id in last_request_time:
    if current_time - last_request_time[user_id] < SPAM_DELAY:
      return
  last_request_time[user_id] = current_time

  if not await check_subscription(message.bot, user_id):
    await message.answer("❌ Avval kanalimizga obuna bo'ling!")
    return

  translated = translate_to_uzbek(message.text)
  final_text = to_latin(translated)

  await message.answer(
      f"O'zbek tilida (Lotin):\n\n`{final_text}`",
      parse_mode=aiogram.enums.ParseMode.MARKDOWN,
  )


async def main() -> None:
  bot = Bot(
      token=TOKEN,
      default=DefaultBotProperties(
          parse_mode=aiogram.enums.ParseMode.MARKDOWN
      ),
  )
  print("Barcha funksiyali mukammal bot ishga tushdi...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO, stream=sys.stdout)
  asyncio.run(main())
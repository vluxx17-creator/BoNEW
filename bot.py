import asyncio
import aiosqlite
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

# Внимание: Рекомендуется отозвать текущий токен в BotFather и использовать переменные окружения
TOKEN = '8690934918:AAFMqJUHiit4SY1n34GqzNc_Wy_tqHPMORE'
ADMIN_ID = 7572936594
CHANNEL_ID = "@owhig"

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def handle(request):
  return web.Response(text="Bot is running")

async def start_web_server():
  app = web.Application()
  app.router.add_get('/', handle)
  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080)))
  await site.start()

async def init_db():
  async with aiosqlite.connect("users.db") as db:
    await db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
    await db.commit()

@dp.message(Command("start"))
async def cmd_start(message: Message):
  async with aiosqlite.connect("users.db") as db:
    await db.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (message.from_user.id,))
    await db.commit()
  try:
    photo = FSInputFile("welcome.jpg")
    text = "Привет! Добро пожаловать в SEARCH.\n\n⚠️ Для работы подпишись на @owhig"
    await message.answer_photo(photo=photo, caption=text)
  except:
    await message.answer("Ошибка: Файл 'welcome.jpg' не найден.")

@dp.message(Command("broadcast"))
async def broadcast(message: Message):
  if message.from_user.id != ADMIN_ID: return
  text = message.text.replace("/broadcast ", "").strip()
  if not text: return
  async with aiosqlite.connect("users.db") as db:
    async with db.execute("SELECT id FROM users") as cursor:
      async for row in cursor:
        try: await bot.send_message(row[0], text)
        except: continue
  await message.answer("✅ Рассылка завершена.")

async def main():
  await init_db()
  await start_web_server()
  await dp.start_polling(bot)

if __name__ == "__main__":
  asyncio.run(main())
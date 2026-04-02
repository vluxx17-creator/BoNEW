import asyncio
import logging
import aiohttp
import sqlite3
import time
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- КОНФИГУРАЦИЯ (ТВОИ ДАННЫЕ) --- 
TOKEN = '8541837659:AAFTSpb_ozGp2ZqRc8oXShvFFxlJF7nl1zg'
VK_TOKEN = 'vk1.a.gg0A2uqhaeJR4Q0rQroAOrKxLtlld-zpDhUuNRsLph2tyJZzoyIioGN8vNs_AzCfepKFqTdigONU-ydz1VZnL68Ns7qZ0HcgUhmEOE_F1ZI26awIwunbGfzTpn-xmEEXAueaaBR5lb-ew_z478YoxYuNlAEHHfGBddR9u10-MJae6l1UUC4C3eKWD28ugFy7hhguP-Ihcxsb42Fbq_SPsw'
ADMIN_IDS = [7572936594] 

PORT = int(os.environ.get("PORT", 8080))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('vector_ultra.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, status TEXT)')
    conn.commit(); conn.close()

def add_user(uid, uname):
    conn = sqlite3.connect('vector_ultra.db')
    status = "ADMIN" if uid in ADMIN_IDS else "USER"
    conn.execute('INSERT OR IGNORE INTO users VALUES (?, ?, ?)', (uid, uname, status))
    conn.commit(); conn.close()

# --- RENDER KEEP-ALIVE ---
async def handle_root(request): return web.Response(text="VECTOR_SYSTEM_ONLINE", status=200)

async def start_server():
    app = web.Application()
    app.router.add_get("/", handle_root)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()

async def anti_sleep():
    if not RENDER_URL: return
    while True:
        await asyncio.sleep(600)
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(RENDER_URL) as r: logging.info(f"Ping: {r.status}")
        except: pass

# --- STATES ---
class OSINT(StatesGroup):
    ip = State()
    vk = State()
    ton = State()
    hlr = State()
    broadcast = State()

# --- UI ---
def main_kb(uid):
    kb = InlineKeyboardBuilder()
    btns = [
        ("🌐 NETWORK_INFRA (ГЛУБОКИЙ)", "s_ip"),
        ("👤 SOCIAL_VK (ДОСЬЕ)", "s_vk"),
        ("💎 BLOCKCHAIN_TON (АКТИВЫ)", "s_ton"),
        ("📞 CELLULAR_HLR (ПЕРЕХВАТ)", "s_hlr"),
        ("📂 SYSTEM_PROFILE", "profile")
    ]
    for text, data in btns: kb.row(types.InlineKeyboardButton(text=text, callback_data=data))
    if uid in ADMIN_IDS: kb.row(types.InlineKeyboardButton(text="⚙️ ADMIN_TERMINAL", callback_data="admin"))
    return kb.as_markup()

async def loading(m, module="SCANNER"):
    msg = await m.answer(f"🔍 **[ {module} ] Инициализация поиска...**")
    for s in [" [ . . . . ] 15%", " [ # # . . ] 45%", " [ # # # . ] 80%", " [ VECTOR ] 100%"]:
        await asyncio.sleep(0.4)
        await msg.edit_text(f"📡 **[ SHERLOK ] АНАЛИЗ ПАКЕТОВ ДАННЫХ**\n`{s}`", parse_mode="Markdown")
    return msg

# --- HANDLERS ---

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    add_user(m.from_user.id, m.from_user.username)
    await m.answer(
        "┌── [ HEMS OSINT ]\n"
        "│\n"
        "│ Приветствую в боте \n"
        "│ Тут есть все для начинающего осинтера \n"
        "│ Бот расскажет о данных от а до я \n"
        "│ Скорее пробуй и зови друзей \n"
        "│ @ovnoy \n"
        "│\n"
        "└── [ ACTIVE ]",
        reply_markup=main_kb(m.from_user.id)
    )

@dp.callback_query(F.data.startswith("s_"))
async def route(call: types.CallbackQuery, state: FSMContext):
    act = call.data.split("_")[1]
    p = {"ip": "Введите IPv4 адрес:", "vk": "Введите ссылку/ID профиля VK:", "ton": "Введите адрес TON:", "hlr": "Введите номер телефона (79...):"}
    await call.message.answer(f"⌨️ **[ VECTOR ]** {p[act]}", parse_mode="Markdown")
    await state.set_state(getattr(OSINT, act)); await call.answer()

# 1. EXPANDED IP MODULE
@dp.message(OSINT.ip)
async def mod_ip(m: types.Message, state: FSMContext):
    msg = await loading(m, "NET_INFRA_SCAN")
    ip = m.text.strip()
    
    # Расширенный скан портов
    ports = [21, 22, 23, 25, 53, 80, 110, 443, 3306, 5432, 8080]
    opened = []
    for p in ports:
        try:
            conn = asyncio.open_connection(ip, p)
            _, w = await asyncio.wait_for(conn, timeout=0.3)
            opened.append(str(p)); w.close(); await w.wait_closed()
        except: pass

    async with aiohttp.ClientSession() as s:
        # Получаем максимум полей через fields=66846719
        async with s.get(f"http://ip-api.com/json/{ip}?fields=66846719&lang=ru") as r:
            d = await r.json()
            if d.get('status') == 'success':
                rep = (
                    f"┌── [ ОТЧЕТ: NETWORK_INFRASTRUCTURE ]\n"
                    f"│\n"
                    f"├─ [ GEO ]\n"
                    f"├─ IP: `{ip}`\n"
                    f"├─ Страна: `{d.get('country')} ({d.get('countryCode')})`\n"
                    f"├─ Город: `{d.get('city')}`\n"
                    f"├─ ZIP: `{d.get('zip')}`\n"
                    f"├─ Timezone: `{d.get('timezone')}`\n"
                    f"│\n"
                    f"├─ [ NETWORK ]\n"
                    f"├─ Провайдер: `{d.get('isp')}`\n"
                    f"├─ Организация: `{d.get('org')}`\n"
                    f"├─ ASN: `{d.get('as')}`\n"
                    f"│\n"
                    f"├─ [ SECURITY ]\n"
                    f"├─ Хостинг/Сервер: `{'ДА' if d.get('hosting') else 'НЕТ'}`\n"
                    f"├─ Proxy/VPN: `{'ДА' if d.get('proxy') else 'НЕТ'}`\n"
                    f"├─ Мобильная сеть: `{'ДА' if d.get('mobile') else 'НЕТ'}`\n"
                    f"│\n"
                    f"├─ [ PORTS_SCAN ]\n"
                    f"└─ Открыты: `{', '.join(opened) if opened else 'НЕ ОБНАРУЖЕНО'}`\n"
                    f"│\n"
                    f"└── [ INFRA ANALYTICS ]"
                )
            else: rep = "❌ **[ ERROR ]** Неверный формат IP."
    await msg.edit_text(rep, parse_mode="Markdown"); await state.clear()

# 2. EXPANDED VK MODULE (Dossier)
@dp.message(OSINT.vk)
async def mod_vk(m: types.Message, state: FSMContext):
    msg = await loading(m, "VK_DOSSIER")
    uid = m.text.split("/")[-1].strip()
    # Запрашиваем расширенные поля
    fields = "bdate,city,verified,followers_count,last_seen,status,counters,career,education,blacklisted,can_send_friend_request"
    params = {'user_ids': uid, 'fields': fields, 'access_token': VK_TOKEN, 'v': '5.131'}
    
    async with aiohttp.ClientSession() as s:
        async with s.get("https://api.vk.com/method/users.get", params=params) as r:
            data = await r.json()
            if 'response' in data and data['response']:
                u = data['response'][0]
                ls_data = u.get('last_seen', {})
                ls_t = ls_data.get('time', 0)
                platforms = {1: "Mobile", 2: "iPhone", 3: "iPad", 4: "Android", 5: "WPhone", 6: "Windows", 7: "Web"}
                plt = platforms.get(ls_data.get('platform'), "N/A")
                ls = time.strftime('%d.%m.%Y %H:%M', time.localtime(ls_t)) if ls_t else "Скрыто"
                c = u.get('counters', {})
                
                rep = (
                    f"┌── [ ОТЧЕТ: SOCIAL_VK_DOSSIER ]\n"
                    f"│\n"
                    f"├─ [ IDENTITY ]\n"
                    f"├─ Имя: `{u.get('first_name')} {u.get('last_name')}`\n"
                    f"├─ ID: `{u.get('id')}`\n"
                    f"├─ Статус: `{u.get('status', 'N/A')}`\n"
                    f"├─ Профиль: `{'ЗАКРЫТ 🔒' if u.get('is_closed') else 'ОТКРЫТ ✅'}`\n"
                    f"│\n"
                    f"├─ [ ACTIVITY ]\n"
                    f"├─ Последний вход: `{ls}`\n"
                    f"├─ Платформа: `{plt}`\n"
                    f"├─ Верификация: `{'ЕСТЬ' if u.get('verified') else 'НЕТ'}`\n"
                    f"│\n"
                    f"├─ [ METRICS ]\n"
                    f"├─ Друзья: `{c.get('friends', 0)}` | Подписчики: `{u.get('followers_count', 0)}`\n"
                    f"├─ Фото: `{c.get('photos', 0)}` | Видео: `{c.get('videos', 0)}`\n"
                    f"├─ Группы: `{c.get('groups', 0)}` | Посты: `{c.get('posts', 0)}`\n"
                    f"│\n"
                    f"├─ [ INFO ]\n"
                    f"├─ Город: `{u.get('city', {}).get('title', 'N/A')}`\n"
                    f"├─ Образование: `{u.get('university_name', 'N/A')}`\n"
                    f"└─ Карьера: `{u.get('career', [{}])[0].get('company', 'N/A') if u.get('career') else 'N/A'}`\n"
                    f"│\n"
                    f"└── [ ANALYTICS ]"
                )
            else: rep = "❌ **[ ERROR ]** Объект не найден в VK."
    await msg.edit_text(rep, parse_mode="Markdown"); await state.clear()

# 3. TON MODULE
@dp.message(OSINT.ton)
async def mod_ton(m: types.Message, state: FSMContext):
    msg = await loading(m, "TON_ASSETS")
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://tonapi.io/v2/blockchain/accounts/{m.text}") as r:
            if r.status == 200:
                d = await r.json()
                bal = int(d.get('balance', 0)) / 10**9
                rep = (
                    f"┌── [ ОТЧЕТ: BLOCKCHAIN_TON ]\n"
                    f"│\n"
                    f"├─ Адрес: `{m.text[:12]}...`\n"
                    f"├─ Баланс: `{bal:.4f} TON`\n"
                    f"├─ Статус: `{d.get('status')}`\n"
                    f"├─ Версия: `{', '.join(d.get('interfaces', []))}`\n"
                    f"└─ Последняя активность: `{time.ctime(d.get('last_activity', 0))}`\n"
                    f"│\n"
                    f"└── [ BLOCKSCAN ]"
                )
            else: rep = "❌ **[ ERROR ]** Кошелек не найден."
    await msg.edit_text(rep, parse_mode="Markdown"); await state.clear()

# 4. HLR MODULE
@dp.message(OSINT.hlr)
async def mod_hlr(m: types.Message, state: FSMContext):
    msg = await loading(m, "CELLULAR_HLR")
    ph = m.text.replace("+", "").strip()
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://htmlweb.ru/geo/api.php?json&telcod={ph}") as r:
            d = await r.json()
            if "error" not in d:
                rep = (
                    f"┌── [ ОТЧЕТ: HLR_INTERCEPT ]\n"
                    f"│\n"
                    f"├─ Объект: `+{ph}`\n"
                    f"├─ Страна: `{d.get('country', {}).get('name')}`\n"
                    f"├─ Регион: `{d.get('region', {}).get('name')}`\n"
                    f"├─ Оператор: `{d.get('0', {}).get('oper')}`\n"
                    f"├─ MCC: `{d.get('0', {}).get('mcc')}` | MNC: `{d.get('0', {}).get('mnc')}`\n"
                    f"│\n"
                    f"├─ [ MESSENGERS ]\n"
                    f"└─ [WA](wa.me/{ph}) | [TG](tg://resolve?phone={ph})\n"
                    f"│\n"
                    f"└── [ GATEWAY ]"
                )
            else: rep = "❌ **[ ERROR ]** Номер не найден."
    await msg.edit_text(rep, parse_mode="Markdown"); await state.clear()

# --- ADMIN & PROFILE ---
@dp.callback_query(F.data == "profile")
async def profile(call: types.CallbackQuery):
    status = "ADMIN" if call.from_user.id in ADMIN_IDS else "USER"
    rep = (f"┌── [ СИСТЕМНЫЙ ПРОФИЛЬ ]\n├─ Юзер: @{call.from_user.username}\n├─ ID: `{call.from_user.id}`\n├─ Статус: `{status}`\n└── [ VECTOR SYSTEM ]")
    await call.message.answer(rep, parse_mode="Markdown"); await call.answer()

@dp.callback_query(F.data == "admin")
async def admin(call: types.CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    kb = InlineKeyboardBuilder().row(types.InlineKeyboardButton(text="📢 РАССЫЛКА", callback_data="broadcast"))
    await call.message.answer("⚙️ **[ ADMIN ACCESS GRANTED ]**", reply_markup=kb.as_markup()); await call.answer()

@dp.callback_query(F.data == "broadcast")
async def br_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("⌨️ Введите сообщение для рассылки:"); await state.set_state(OSINT.broadcast); await call.answer()

@dp.message(OSINT.broadcast)
async def br_do(m: types.Message, state: FSMContext):
    if m.from_user.id not in ADMIN_IDS: return
    conn = sqlite3.connect('vector_ultra.db')
    users = conn.execute('SELECT id FROM users').fetchall()
    conn.close()
    for u in users:
        try: await bot.send_message(u[0], m.text)
        except: pass
    await m.answer("✅ **Рассылка завершена.**"); await state.clear()

# --- RUN ---
async def main():
    init_db()
    await asyncio.gather(dp.start_polling(bot), start_server(), anti_sleep())

if __name__ == "__main__":
    asyncio.run(main())

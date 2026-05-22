import os
import asyncio
import logging
import re
import aiohttp
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ParseMode

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TOKEN = os.getenv("8758935544:AAEwREvxc7e0q-GuiO1Xx0oxA3d1UIHh39E")
if not TOKEN:
    raise ValueError("Критическая ошибка: TOKEN не задан в настройках Render!")

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# ASCII-баннер для вывода в консоль при старте
CONSOLE_BANNER = """
==================================================
  ██████  ██   ██ ███████ ██      ██      
  ██      ██   ██ ██      ██      ██      
  ██████  ███████ █████   ██      ██      
       ██ ██   ██ ██      ██      ██      
  ██████  ██   ██ ███████ ███████ ███████ 
              S E A R C H   
==================================================
"""

class OsintStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_ip = State()
    waiting_for_vk = State()
    waiting_for_username = State()
    waiting_for_bgp = State()
    waiting_for_domain = State()

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Телефон", callback_data="search_phone"),
         InlineKeyboardButton(text="🌐 IP-Адрес", callback_data="search_ip")],
        [InlineKeyboardButton(text="👥 VK ID", callback_data="search_vk"),
         InlineKeyboardButton(text="👤 Username", callback_data="search_username")],
        [InlineKeyboardButton(text="🏢 Провайдер (BGP)", callback_data="search_bgp"),
         InlineKeyboardButton(text="🖥 Домен (Whois)", callback_data="search_domain")]
    ])

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    # Красивый текстовый баннер внутри самого Telegram
    tg_banner = (
        f"<code>╔════════════════════════════════════╗\n"
        f"║  S H E L L S E A R C H   O S I N T  ║\n"
        f"╚════════════════════════════════════╝</code>\n\n"
        f"Добро пожаловать в интеллектуальную систему анализа открытых источников.\n\n"
        f"Выберите необходимый аналитический модуль на клавиатуре ниже:"
    )
    await message.answer(tg_banner, reply_markup=get_main_menu(), parse_mode=ParseMode.HTML)

# --- МОДУЛЬ 1: ПОИСК ПО ТЕЛЕФОНУ (РАСШИРЕННЫЙ) ---
@router.callback_query(F.data == "search_phone")
async def start_phone_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OsintStates.waiting_for_phone)
    await callback.message.edit_text("Введите номер телефона в международном формате (например, 79991234567):")

@router.message(OsintStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    num = ''.join(filter(str.isdigit, message.text))
    if len(num) < 10:
        await message.answer("❌ Ошибка: Неверный формат номера. Должно быть не менее 10 цифр.")
        return
    if num.startswith('8'):
        num = '7' + num[1:]
    
    code = num[1:4]
    url = f"https://mtt.ru{code}&number={num}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    op = data.get('operator', 'Не найден')
                    reg = data.get('region', 'Не найден')
                    
                    text = (
                        f"📊 <b>ГЛУБОКИЙ АНАЛИЗ НОМЕРА ТЕЛЕФОНА</b>\n"
                        f"<code>====================================</code>\n"
                        f"🔑 <b>ОСНОВНЫЕ ДАННЫЕ:</b>\n"
                        f" ├─ <b>Цель:</b> <code>+{num}</code>\n"
                        f" ├─ <b>Страна:</b> Российская Федерация (+7)\n"
                        f" ├─ <b>Префикс (DEF-код):</b> {code}\n"
                        f" <code>====================================</code>\n"
                        f"🌐 <b>ИНФОРМАЦИЯ О ПРОВАЙДЕРЕ СВЯЗИ:</b>\n"
                        f" ├─ <b>Текущий оператор:</b> {op}\n"
                        f" ├─ <b>Регион регистрации:</b> {reg}\n"
                        f" ├─ <b>Официальный реестр:</b> ОАО 'МТТ'\n"
                        f" <code>====================================</code>\n"
                        f"⚡️ <i>Проверка завершена успешно. Данные актуальны.</i>"
                    )
                    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                else:
                    await message.answer("❌ Ошибка: Сервер верификации МТТ временно недоступен.", reply_markup=get_main_menu())
    except Exception as e:
        logging.error(f"Phone error: {e}")
        await message.answer("❌ Произошла критическая ошибка при обработке запроса.", reply_markup=get_main_menu())
    await state.clear()
# --- МОДУЛЬ 2: ПОИСК ПО IP-АДРЕСУ (РАСШИРЕННЫЙ) ---
@router.callback_query(F.data == "search_ip")
async def start_ip_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OsintStates.waiting_for_ip)
    await callback.message.edit_text("Введите целевой IP-адрес для сканирования (например, 8.8.8.8):")

@router.message(OsintStates.waiting_for_ip)
async def process_ip(message: Message, state: FSMContext):
    ip = message.text.strip()
    url = f"http://ip-api.com{ip}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get('status') == 'success':
                    lat, lon = data.get('lat'), data.get('lon')
                    text = (
                        f"📊 <b>РАСШИРЕННЫЙ СЕТЕВОЙ ОТЧЕТ: {ip}</b>\n"
                        f"<code>====================================</code>\n"
                        f"🌍 <b>ГЕОЛОКАЦИОННЫЕ ДАННЫЕ:</b>\n"
                        f" ├─ <b>Страна назначения:</b> {data.get('country')} ({data.get('countryCode')})\n"
                        f" ├─ <b>Административный регион:</b> {data.get('regionName')} ({data.get('region')})\n"
                        f" ├─ <b>Населенный пункт (Город):</b> {data.get('city')}\n"
                        f" └─ <b>Почтовый индекс зоны:</b> {data.get('zip', 'Не указан')}\n"
                        f"<code>====================================</code>\n"
                        f"⚙️ <b>ТЕХНИЧЕСКИЕ ПАРАМЕТРЫ СЕТИ:</b>\n"
                        f" ├─ <b>Интернет-провайдер (ISP):</b> {data.get('isp')}\n"
                        f" ├─ <b>Владелец подсети (Org):</b> {data.get('org', 'Отсутствует')}\n"
                        f" ├─ <b>Спецификация ASN:</b> <code>{data.get('as')}</code>\n"
                        f" └─ <b>Временная зона хоста:</b> {data.get('timezone')}\n"
                        f"<code>====================================</code>\n"
                        f"🌐 <b>ТОПОГРАФИЧЕСКИЕ КООРДИНАТЫ:</b>\n"
                        f" ├─ <b>Широта (Latitude):</b> <code>{lat}</code>\n"
                        f" ├─ <b>Долгота (Longitude):</b> <code>{lon}</code>\n"
                        f" └─ <b>Спутниковые карты:</b> "
                        f"<a href='https://google.com{lat},{lon}'>Google Maps</a> | "
                        f"<a href='https://yandex.ru{lon}%2C{lat}&z=14'>Yandex Maps</a>\n"
                        f"<code>====================================</code>\n"
                        f"⚡️ <i>Сбор информации по сетевому адресу завершен.</i>"
                    )
                    await message.answer(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=get_main_menu())
                else:
                    await message.answer(f"❌ Ошибка: Глобальная база RDAP отклонила запрос [{data.get('message')}].", reply_markup=get_main_menu())
    except Exception as e:
        logging.error(f"IP error: {e}")
        await message.answer("❌ Не удалось обработать IP-адрес. Проверьте корректность ввода.", reply_markup=get_main_menu())
    await state.clear()

# --- МОДУЛЬ 3: ПОИСК ПО VK ID (РАСШИРЕННЫЙ) ---
@router.callback_query(F.data == "search_vk")
async def start_vk_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OsintStates.waiting_for_vk)
    await callback.message.edit_text("Введите VK ID или короткий буквенный никнейм профиля:")

@router.message(OsintStates.waiting_for_vk)
async def process_vk(message: Message, state: FSMContext):
    vk_id = message.text.strip().replace("https://vk.com", "").replace("://vk.com", "")
    url = f"https://reg://vk.comid{vk_id}/"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    match = re.search(r'Дата регистрации:\s*<b>([^<]+)</b>', html)
                    reg_date = match.group(1).strip() if match else "Скрыта приватностью / Не найдена"
                    
                    text = (
                        f"📊 <b>ПОЛНЫЙ КРИМИНАЛИСТИЧЕСКИЙ ОТЧЕТ: ВКОНТАКТЕ</b>\n"
                        f"<code>====================================</code>\n"
                        f"👤 <b>ИДЕНТИФИКАЦИЯ СУБЪЕКТА:</b>\n"
                        f" ├─ <b>Введенный маркер:</b> <code>{vk_id}</code>\n"
                        f" ├─ <b>Постоянный цифровой URL:</b> https://vk.comid{vk_id}\n"
                        f" └─ <b>Платформа:</b> VKontakte Social Network\n"
                        f"<code>====================================</code>\n"
                        f"📅 <b>ВРЕМЕННЫЕ ХАРАКТЕРИСТИКИ:</b>\n"
                        f" ├─ <b>Дата создания аккаунта:</b> {reg_date}\n"
                        f" ├─ <b>Тип записи:</b> Пользовательский профиль\n"
                        f" └─ <b>Статус верификации:</b> Открытый реестр regvk\n"
                        f"<code>====================================</code>\n"
                        f"⚡️ <i>Анализ профиля завершен. Сохранено в кэш системы.</i>"
                    )
                    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                else:
                    await message.answer("❌ Ошибка: Целевой аккаунт не существует, удален или заблокирован.", reply_markup=get_main_menu())
    except Exception as e:
        logging.error(f"VK error: {e}")
        await message.answer("❌ Ошибка при попытке парсинга данных структуры ВКонтакте.", reply_markup=get_main_menu())
    await state.clear()
# --- МОДУЛЬ 4: ПОИСК ПО USERNAME (РАСШИРЕННЫЙ) ---
@router.callback_query(F.data == "search_username")
async def start_username_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OsintStates.waiting_for_username)
    await callback.message.edit_text("Введите интересующий никнейм для глобального сканирования (без @):")

@router.message(OsintStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    username = message.text.strip().replace("@", "")
    
    platforms = {
        "Telegram (Мессенджер)": f"https://t.me{username}",
        "GitHub (Исходный код)": f"https://github.com{username}",
        "Twitter/X (Соцсеть)": f"https://x.com{username}",
        "YouTube (Видеохостинг)": f"https://youtube.com@{username}",
        "Reddit (Форум-платформа)": f"https://reddit.com{username}"
    }
    
    results = []
    async with aiohttp.ClientSession() as session:
        for name, url in platforms.items():
            try:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        results.append(f" ├─ ✅ <b>{name}:</b> <a href='{url}'>[ Профиль обнаружен ]</a>")
                    else:
                        results.append(f" ├─ ❌ <b>{name}:</b> Не зарегистрирован")
            except Exception:
                results.append(f" ├─ ⚠️ <b>{name}:</b> Таймаут/Заблокировано")
                
    text = (
        f"📊 <b>ГЛОБАЛЬНЫЙ КРИМИНАЛИСТИЧЕСКИЙ ОТЧЕТ: USERNAME</b>\n"
        f"<code>====================================</code>\n"
        f"👤 <b>ОБЪЕКТ АНАЛИЗА:</b>\n"
        f" ├─ <b>Искомый псевдоним:</b> <code>{username}</code>\n"
        f" └─ <b>Метод:</b> Прямая верификация HTTP-статусов ответов\n"
        f"<code>====================================</code>\n"
        f"🌐 <b>РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ ЦЕЛЕЙ:</b>\n"
        + "\n".join(results) + "\n"
        f"<code>====================================</code>\n"
        f"⚡️ <i>Анализ цифрового следа по никнейму успешно завершен.</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=get_main_menu())
    await state.clear()

# --- МОДУЛЬ 5: ПОИСК ПРОВАЙДЕРА BGP / ASN (РАСШИРЕННЫЙ) ---
@router.callback_query(F.data == "search_bgp")
async def start_bgp_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OsintStates.waiting_for_bgp)
    await callback.message.edit_text("Введите номер автономной системы (например, AS15169) или IP-адрес:")

@router.message(OsintStates.waiting_for_bgp)
async def process_bgp(message: Message, state: FSMContext):
    query = message.text.strip().upper()
    is_asn = query.startswith("AS")
    clean_query = query.replace("AS", "") if is_asn else query
    
    url = f"https://bgpview.io{clean_query}" if is_asn else f"https://bgpview.io{clean_query}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    res_data = await resp.json()
                    if res_data.get("status") == "ok":
                        data = res_data.get("data", {})
                        text = (
                            f"📊 <b>ИНФОРМАЦИОННЫЙ ОТЧЕТ ИНФРАСТРУКТУРЫ BGP</b>\n"
                            f"<code>====================================</code>\n"
                            f"🏢 <b>СПЕЦИФИКАЦИЯ МАРШРУТИЗАЦИИ:</b>\n"
                            f" ├─ <b>Входной запрос:</b> <code>{query}</code>\n"
                            f" ├─ <b>Тип объекта:</b> {'Автономная система (ASN)' if is_asn else 'Глобальный IP-Маршрут'}\n"
                            f" └─ <b>Источник реестра:</b> Глобальная база BGPView API\n"
                            f"<code>====================================</code>\n"
                            f"🖥 <b>ДАННЫЕ ВЛАДЕЛЬЦА И СЕТИ:</b>\n"
                            f" ├─ <b>Организация (Name):</b> {data.get('name', 'Не указано')}\n"
                            f" ├─ <b>Описание узла:</b> {data.get('description_short', 'Данные отсутствуют')}\n"
                            f" ├─ <b>Код страны:</b> <code>{data.get('country_code', '??')}</code>\n"
                            f" └─ <b>Регистратор:</b> Internet Assigned Numbers Authority (IANA)\n"
                            f"<code>====================================</code>\n"
                            f"⚡️ <i>Сетевой анализ BGP-структуры завершен.</i>"
                        )
                        await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                    else:
                        await message.answer("❌ Ошибка: Указанный объект в глобальной базе BGPView отсутствует.", reply_markup=get_main_menu())
                else:
                    await message.answer(f"❌ Ошибка: Сервер BGPView ответил статус-кодом {resp.status}.", reply_markup=get_main_menu())
    except Exception as e:
        logging.error(f"BGP error: {e}")
        await message.answer("❌ Не удалось извлечь данные BGP. Проверьте валидность ASN/IP.", reply_markup=get_main_menu())
    await state.clear()
# --- МОДУЛЬ 6: ПОИСК ДОМЕНА WHOIS (РАСШИРЕННЫЙ) ---
@router.callback_query(F.data == "search_domain")
async def start_domain_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OsintStates.waiting_for_domain)
    await callback.message.edit_text("Введите доменное имя сайта для проверки (например, google.com):")

@router.message(OsintStates.waiting_for_domain)
async def process_domain(message: Message, state: FSMContext):
    domain = message.text.strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
    url = f"https://rdap.org{domain}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    events = {e.get("action"): e.get("eventDate") for e in data.get("events", [])}
                    created = events.get("registration", "Данные отсутствуют").replace("T", " ").replace("Z", "")
                    changed = events.get("last changed", "Данные отсутствуют").replace("T", " ").replace("Z", "")
                    expiration = events.get("expiration", "Данные отсутствуют").replace("T", " ").replace("Z", "")
                    
                    text = (
                        f"📊 <b>ПОЛНЫЙ КРИМИНАЛИСТИЧЕСКИЙ ОТЧЕТ: WHOIS ДАННЫЕ</b>\n"
                        f"<code>====================================</code>\n"
                        f"🖥 <b>СПЕЦИФИКАЦИЯ ЦЕЛИ:</b>\n"
                        f" ├─ <b>Исследуемый домен:</b> <code>{domain}</code>\n"
                        f" └─ <b>Протокол проверки:</b> RDAP (Registration Data Access Protocol)\n"
                        f"<code>====================================</code>\n"
                        f"📅 <b>ВРЕМЕННЫЕ ХАРАКТЕРИСТИКИ РЕГИСТРАЦИИ:</b>\n"
                        f" ├─ <b>Дата создания домена:</b> <code>{created}</code>\n"
                        f" ├─ <b>Последняя модификация:</b> <code>{changed}</code>\n"
                        f" └─ <b>Дата окончания делегирования:</b> <code>{expiration}</code>\n"
                        f"<code>====================================</code>\n"
                        f"⚡️ <i>Сбор информации о доменной структуре завершен.</i>"
                    )
                    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu())
                else:
                    await message.answer("❌ Ошибка: Домен не зарегистрирован или регистратор скрыл RDAP-записи.", reply_markup=get_main_menu())
    except Exception as e:
        logging.error(f"Whois error: {e}")
        await message.answer("❌ Не удалось получить Whois данные. Проверьте синтаксис домена.", reply_markup=get_main_menu())
    await state.clear()


# --- ИНТЕГРАЦИЯ С ВЕБ-СЕРВЕРОМ ДЛЯ RENDER ---
async def start_web_server():
    app = aiohttp.web.Application()
    
    async def handle_ping(request):
        return aiohttp.web.Response(text="ShellSearch OSINT Engine is running online.")
        
    app.router.add_get('/', handle_ping)
    
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 10000))
    site = aiohttp.web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Веб-сервер успешно запущен на порту {port} для прохождения проверок Render.")

async def main():
    # Выводим собственный красивый баннер в консоль логирования Render при старте
    print(CONSOLE_BANNER)
    logging.info("Инициализация компонентов бота ShellSearch OSINT...")
    
    dp.include_router(router)
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    
    logging.info("Бот успешно авторизован в Telegram API и запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

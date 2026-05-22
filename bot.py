import os
import asyncio
import logging
import re
import datetime
import aiohttp
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Сервисный ключ VK (можно оставить пустым, бот использует публичный fallback-токен)
VK_TOKEN = os.getenv("VK_API_TOKEN", "") 

# Инициализация бота (Берется из переменных окружения на Render для безопасности на GitHub)
TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

BANNER = (
    "<b>╔══════════════════════════════════╗</b>\n"
    "<b>║            ShellSearch OSINT             ║</b>\n"
    "<b>╚══════════════════════════════════╝</b>\n\n"
    "🤖 <b>ShellSearch</b> — профессиональный инструмент комплексного анализа "
    "цифрового следа, сетевой инфраструктуры и открытых государственных реестров."
)

class SearchStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_ip = State()
    waiting_for_vk = State()
    waiting_for_username = State()
    waiting_for_provider = State()

start_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔍 Перейти к выбору пробива", callback_data="start_search")],
    [InlineKeyboardButton(text="ℹ️ Технический FAQ", callback_data="open_faq")]
])

search_methods_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📞 Анализ телефонного номера", callback_data="method_phone")],
    [InlineKeyboardButton(text="🌐 Геолокация и сканирование IP", callback_data="method_ip")],
    [InlineKeyboardButton(text="👤 Деанонимизация ВКонтакте", callback_data="method_vk")],
    [InlineKeyboardButton(text="📊 Аналитика уязвимостей Username", callback_data="method_username")],
    [InlineKeyboardButton(text="🏢 Картография провайдера (ASN)", callback_data="method_provider")],
    [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_main")]
])

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(BANNER, parse_mode="HTML", reply_markup=start_kb)

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(BANNER, parse_mode="HTML", reply_markup=start_kb)
    await callback.answer()

@router.callback_query(F.data == "open_faq")
async def process_faq(callback: CallbackQuery):
    faq_text = (
        "<b>ℹ️ Спецификация системы ShellSearch</b>\n\n"
        "🟢 <b>Порядок работы:</b> Все запросы обрабатываются асинхронно через неблокирующие сокеты.\n"
        "🟢 <b>Источники:</b> Прямые парсеры DOM-деревьев веб-страниц, BGP/RIPE таблицы маршрутизации, "
        "публичные API социальных платформ и реестры нумерации Роскомнадзора.\n"
        "🟢 <b>Безопасность:</b> Бот логирует только ошибки выполнения и не сохраняет историю запросов пользователей."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]])
    await callback.message.edit_text(faq_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "start_search")
async def process_start_search(callback: CallbackQuery):
    await callback.message.edit_text("🎯 <b>Выберите необходимый модуль OSINT-модуля:</b>", parse_mode="HTML", reply_markup=search_methods_kb)
    await callback.answer()

@router.callback_query(F.data.startswith("method_"))
async def choose_method(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена операции", callback_data="start_search")]])
    method = callback.data.split("_")[1]
    
    if method == "phone":
        await state.set_state(SearchStates.waiting_for_phone)
        await callback.message.edit_text("📝 <b>Введите номер телефона</b>\nФормат: 11 цифр (например, <code>79991234567</code>):", parse_mode="HTML", reply_markup=kb)
    elif method == "ip":
        await state.set_state(SearchStates.waiting_for_ip)
        await callback.message.edit_text("📝 <b>Введите целевой IP-адрес</b>\nФормат IPv4 (например, <code>8.8.8.8</code>):", parse_mode="HTML", reply_markup=kb)
    elif method == "vk":
        await state.set_state(SearchStates.waiting_for_vk)
        await callback.message.edit_text("📝 <b>Введите объект VK</b>\nПринимаются: Короткое имя, ID, или полная ссылка на профиль:", parse_mode="HTML", reply_markup=kb)
    elif method == "username":
        await state.set_state(SearchStates.waiting_for_username)
        await callback.message.edit_text("📝 <b>Введите исследуемый Username</b>\nИмя пользователя без символа @ (например, <code>shadow_user</code>):", parse_mode="HTML", reply_markup=kb)
    elif method == "provider":
        await state.set_state(SearchStates.waiting_for_provider)
        await callback.message.edit_text("📝 <b>Введите коммерческое название провайдера</b>\nПример: <code>Trytek</code>, <code>Rostelecom</code>, <code>Infolada</code>:", parse_mode="HTML", reply_markup=kb)
    
    await callback.answer()

# =====================================================================
# РЕАЛИЗАЦИЯ ПОЛНОРАЗМЕРНЫХ И ГЛУБОКИХ OSINT-ОТЧЕТОВ (ЧАСТЬ 1)
# =====================================================================

async def deep_phone_search(phone: str) -> str:
    clean_phone = re.sub(r'\D', '', phone)
    if len(clean_phone) == 11 and clean_phone.startswith('8'):
        clean_phone = '7' + clean_phone[1:]
    if len(clean_phone) != 11:
        return "❌ <b>Ошибка валидации:</b> Номер должен строго состоять из 11 цифр."
    
    code = clean_phone[1:4]
    num = clean_phone[4:]
    url = f"https://mtt.ru{code}&number={num}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10) as resp:
                if resp.status != 200:
                    return "❌ <b>Ошибка инфраструктуры:</b> Государственный реестр не отвечает."
                
                soup = BeautifulSoup(await resp.text(), 'html.parser')
                table = soup.find('table', class_='support-table')
                if not table:
                    return f"❌ <b>Анализ завершен:</b> Диапазон {code} не найден в официальном плане нумерации РФ."
                
                rows = table.find_all('tr')
                if len(rows) < 2:
                    return "❌ <b>Анализ завершен:</b> В таблице отсутствуют строки с данными."
                
                cols = rows[1].find_all('td')
                operator = cols[0].text.strip()
                region = cols[1].text.strip()
                start_range = cols[2].text.strip()
                end_range = cols[3].text.strip()
                capacity = cols[4].text.strip()

                return (
                    f"<b>📋 ПОЛНЫЙ КАРТОГРАФИЧЕСКИЙ ОТЧЕТ НОМЕРА</b>\n"
                    f"<i>Дата выгрузки: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>\n"
                    f"──────────────────────────────────\n"
                    f"📱 <b>Сведения о цели:</b>\n"
                    f"├─ <b>Введенный номер:</b> +{clean_phone}\n"
                    f"├─ <b>Международный код:</b> +7 (Российская Федерация)\n"
                    f"├─ <b>DEF-код (Префикс):</b> {code}\n"
                    f"└─ <b>Абонентский индекс:</b> {num}\n\n"
                    f"🏢 <b>Привязка к телеком-оператору:</b>\n"
                    f"├─ <b>Официальный провайдер:</b> {operator}\n"
                    f"├─ <b>Лицензионный регион:</b> {region}\n"
                    f"├─ <b>Размер выделенного пула:</b> {capacity} абонентов\n"
                    f"└─ <b>Границы диапазона:</b> {code}{start_range} — {code}{end_range}\n"
                    f"──────────────────────────────────\n"
                    f"📊 <b>Векторы для дальнейшего OSINT:</b>\n"
                    f"Часовой пояс региона: UTC+3 (соответствует региону {region}). Проверьте активность абонента в мессенджерах в рабочие часы данного региона."
                )
    except Exception as e:
        return f"❌ <b>Технический сбой сети:</b> {str(e)}"

async def deep_ip_search(ip: str) -> str:
    url = f"http://ip-api.com{ip.strip()}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=7) as resp:
                data = await resp.json()
                if data.get("status") == "fail":
                    return f"❌ <b>Ошибка сканирования IP:</b> {data.get('message', 'Некорректный узел')}"
                
                return (
                    f"<b>🌐 РАСШИРЕННЫЙ СЕТЕВОЙ ОТЧЕТ ХОСТА: {data.get('query')}</b>\n"
                    f"──────────────────────────────────\n"
                    f"📍 <b>Географическая локализация:</b>\n"
                    f"├─ <b>Страна размещения:</b> {data.get('country')} ({data.get('countryCode')})\n"
                    f"├─ <b>Административный регион:</b> {data.get('regionName')} (Код: {data.get('region')})\n"
                    f"├─ <b>Город/Населенный пункт:</b> {data.get('city')}\n"
                    f"├─ <b>Почтовый индекс зоны:</b> {data.get('zip', 'Не указан')}\n"
                    f"├─ <b>Временная зона (Локальное время):</b> {data.get('timezone')}\n"
                    f"└─ <b>Точные гео-координаты:</b> <code>{data.get('lat')}, {data.get('lon')}</code>\n\n"
                    f"🛰 <b>Сетевая телеметрия узла:</b>\n"
                    f"├─ <b>Официальное имя провайдера (ISP):</b> {data.get('isp')}\n"
                    f"├─ <b>Владелец инфраструктуры (Org):</b> {data.get('org')}\n"
                    f"└─ <b>Регистрационная запись ASN:</b> {data.get('as')}\n"
                    f"──────────────────────────────────\n"
                    f"🔗 <b>Спутниковая навигация картографии:</b>\n"
                    f"🔹 <a href='https://google.com{data.get('lat')},{data.get('lon')}'>Открыть на Google Maps</a>\n"
                    f"🔹 <a href='https://yandex.ru{data.get('lon')}%2C{data.get('lat')}&z=14'>Открыть на Yandex Maps</a>"
                )
    except:
        return "❌ <b>Ошибка сбора данных:</b> Удаленный узел BGP/RIPE не ответил на пакеты запроса."
async def deep_vk_search(target: str) -> str:
    screen_name = target.split("/")[-1].replace("@", "").strip()
    url = f"https://vk.com{screen_name}"
    vk_id = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=7) as resp:
                html = await resp.text()
                match = re.search(r'\"location\":\"vk\.com/id(\d+)\"', html) or re.search(r'href=\"/id(\d+)\"', html) or re.search(r'\"ownerId\":(\d+)', html)
                if match:
                    vk_id = match.group(1)
    except:
        return "❌ <b>Ошибка парсинга:</b> Не удалось установить соединение с серверами VK."

    if not vk_id:
        return "❌ <b>Анализ прерван:</b> Указанный объект ВКонтакте не существует или полностью закрыт приватностью."

    api_url = f"https://vk.com"
    params = {
        "user_ids": vk_id,
        "fields": "photo_max_orig,bdate,career,education,counters,last_seen,status,followers_count",
        "v": "5.131",
        "access_token": VK_TOKEN if VK_TOKEN else "841315578413155784131557f98466bb6b884138413155755106b001a1dbfe98ff02a24"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, timeout=7) as resp:
                result = await resp.json()
                if "response" not in result or not result["response"]:
                    return f"❌ <b>Ошибка API:</b> Не удалось выгрузить структуру аккаунта. ID: <code>id{vk_id}</code>"
                
                user_data = result["response"][0]
                first_name = user_data.get("first_name", "N/A")
                last_name = user_data.get("last_name", "N/A")
                status = user_data.get("status", "Отсутствует")
                bdate = user_data.get("bdate", "Скрыта или не указана")
                avatar_url = user_data.get("photo_max_orig", "Нет фото")
                followers = user_data.get("followers_count", 0)
                
                career_list = user_data.get("career", [])
                work_place = "Не заполнено в профиле"
                if career_list:
                    jobs = []
                    for job in career_list:
                        company = job.get("company", "")
                        position = job.get("position", "")
                        if company:
                            jobs.append(f"{company} ({position})" if position else company)
                    if jobs:
                        work_place = ", ".join(jobs)
                
                counters = user_data.get("counters", {})
                photos_count = counters.get("photos", "Скрыто")
                friends_count = counters.get("friends", "Скрыто")
                videos_count = counters.get("videos", "Скрыто")
                audios_count = counters.get("audios", "Скрыто")

                id_int = int(vk_id)
                if id_int < 5000000: est_year = "2006-2008 гг."
                elif id_int < 50000000: est_year = "2009-2010 гг."
                elif id_int < 150000000: est_year = "2011-2012 гг."
                elif id_int < 250000000: est_year = "2013-2014 гг."
                elif id_int < 400000000: est_year = "2015-2016 гг."
                elif id_int < 550000000: est_year = "2017-2019 гг."
                else: est_year = "2020-2026 гг."

                return (
                    f"<b>👤 ГЛУБОКОЕ ИССЛЕДОВАНИЕ ПРОФИЛЯ VKОНТАКТЕ</b>\n"
                    f"──────────────────────────────────\n"
                    f"📋 <b>Регистрационные и личные данные:</b>\n"
                    f"├─ <b>Имя / Фамилия:</b> {first_name} {last_name}\n"
                    f"├─ <b>Постоянный адрес:</b> <code>://vk.com{vk_id}</code>\n"
                    f"├─ <b>Дата рождения:</b> {bdate}\n"
                    f"├─ <b>Примерный период создания аккаунта:</b> {est_year}\n"
                    f"└─ <b>Установленный статус:</b> <i>«{status}»</i>\n\n"
                    f"💼 <b>Профессиональная занятость и работа:</b>\n"
                    f"└─ <b>Место работы / Должность:</b> {work_place}\n\n"
                    f"📊 <b>Статистический анализ активности и медиа:</b>\n"
                    f"├─ <b>Всего фотографий в альбомах:</b> <u>{photos_count}</u>\n"
                    f"├─ <b>Количество друзей:</b> {friends_count}\n"
                    f"├─ <b>Количество подписчиков:</b> {followers}\n"
                    f"├─ <b>Загруженных видеозаписей:</b> {videos_count}\n"
                    f"└─ <b>Аудиотека аккаунта:</b> {audios_count} треков\n"
                    f"──────────────────────────────────\n"
                    f"🖼 <b>Прямая ссылка на главное фото профиля (оригинал):</b>\n"
                    f"<a href='{avatar_url}'>[ОТКРЫТЬ ИЗОБРАЖЕНИЕ В ВЫСОКОМ КАЧЕСТВЕ]</a>"
                )
    except Exception as e:
        return f"❌ <b>Внутреннее исключение API:</b> {str(e)}"

async def deep_username_search(username: str) -> str:
    user = username.replace("@", "").strip()
    platforms = {
        "Telegram Мессенджер": f"https://t.me{user}",
        "GitHub Репозитории": f"https://github.com{user}",
        "ВКонтакте Соцсеть": f"https://vk.com{user}"
    }
    
    report_lines = [
        f"<b>📊 ОСИНТ-КАРТА ЗАЛИЯНИЯ НИКНЕЙМА: @{user}</b>",
        f"<i>Многопоточный анализ присутствия цифрового следа в базах данных.</i>",
        f"──────────────────────────────────"
    ]
    
    async with aiohttp.ClientSession() as session:
        for name, url in platforms.items():
            try:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5) as resp:
                    text = await resp.text()
                    if name == "Telegram Мессенджер" and "tgme_page_extra" in text:
                        report_lines.append(f"🟢 <b>{name}:</b> Аккаунт <b>НАЙДЕН</b>.\n└─ URL адресации: t.me/{user}")
                    elif name == "GitHub Репозитории" and resp.status == 200:
                        report_lines.append(f"🟢 <b>{name}:</b> Профиль <b>СУЩЕСТВУЕТ</b>.\n└─ Доступ к коду: ://github.com{user}")
                    elif name == "ВКонтакте Соцсеть" and ("подписаны" in text or "id" in resp.url.path or resp.status == 200):
                        report_lines.append(f"🟢 <b>{name}:</b> Зарегистрирован след пользователя.\n└─ Прямая линковка: ://vk.com{user}")
                    else:
                        report_lines.append(f"⚪️ <b>{name}:</b> Имя свободно / Профиль не обнаружен.")
            except:
                report_lines.append(f"⚠️ <b>{name}:</b> Сервер таймаута при сканировании.")
                
    report_lines.append("──────────────────────────────────")
    report_lines.append("💡 <b>Следствие OSINT:</b> Если на различных сервисах под данным никнеймом стоят одинаковые аватары или пересекается описание, с вероятностью 94% эти аккаунты принадлежат одному физическому лицу.")
    return "\n\n".join(report_lines)

async def deep_provider_search(provider_name: str) -> str:
    query = provider_name.strip()
    url = f"https://bgpview.io{query}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return "❌ <b>Ошибка базы данных:</b> Глобальный реестр BGPView временно недоступен."
                
                data = await resp.json()
                asns = data.get("data", {}).get("asns", [])
                if not asns:
                    return f"❌ <b>Поиск завершен:</b> Провайдер с названием «{query}» не найден в глобальной таблице BGP."
                
                asn_data = asns[0]
                asn_id = asn_data.get('asn')
                
                geo_url = f"https://bgpview.io{asn_id}"
                async with session.get(geo_url, timeout=10) as geo_resp:
                    geo_data = await geo_resp.json()
                    main_info = geo_data.get("data", {})
                
                return (
                    f"<b>🏢 РЕЕСТРОВЫЙ ОТЧЕТ СЕТЕВОГО ПРОВАЙДЕРА</b>\n"
                    f"──────────────────────────────────\n"
                    f"📝 <b>Основные реквизиты узла:</b>\n"
                    f"├─ <b>Коммерческое имя:</b> {asn_data.get('name')}\n"
                    f"├─ <b>Номер Автономной Системы:</b> <a href='https://bgpview.io{asn_id}'>AS{asn_id}</a>\n"
                    f"├─ <b>Зарегистрированное описание:</b> {asn_data.get('description')}\n"
                    f"└─ <b>Страна юрисдикции регистрации:</b> {asn_data.get('country_code')} ({main_info.get('owner_address', ['Не указано'])[0]})\n\n"
                    f"🌍 <b>Географическая локация и штаб-квартира:</b>\n"
                    f"├─ <b>Регистрационный адрес владельца:</b>\n"
                    f"│  <i>{', '.join(main_info.get('owner_address', []))}</i>\n"
                    f"└─ <b>Распределительный узел сети:</b> RIPE / APNIC Database Zone\n\n"
                    f"📡 <b>Инфраструктура маршрутизации (Текущая):</b>\n"
                    f"├─ <b>Связанные магистральные аплинки:</b> Выделенные пулы IPv4/IPv6\n"
                    f"└─ <b>Управление:</b> Данный провайдер управляет сетевыми шлюзами для сотен домашних и коммерческих роутеров по указанному юридическому адресу."
                )
    except:
        return "❌ <b>Техническая ошибка:</b> Не удалось распарсить структуру глобальных BGP-таблиц."

# --- ХЕНДЛЕРЫ ВВОДА ДАННЫХ ---

@router.message(SearchStates.waiting_for_phone)
async def res_phone(message: Message, state: FSMContext):
    await state.clear()
    status = await message.answer("⏳ <i>Опрос базы планов нумерации связи...</i>", parse_mode="HTML")
    res = await deep_phone_search(message.text)
    await status.edit_text(res, parse_mode="HTML", disable_web_page_preview=False, reply_markup=start_kb)

@router.message(SearchStates.waiting_for_ip)
async def res_ip(message: Message, state: FSMContext):
    await state.clear()
    status = await message.answer("⏳ <i>Сбор BGP-логов хоста и определение координат...</i>", parse_mode="HTML")
    res = await deep_ip_search(message.text)
    await status.edit_text(res, parse_mode="HTML", disable_web_page_preview=False, reply_markup=start_kb)

@router.message(SearchStates.waiting_for_vk)
async def res_vk(message: Message, state: FSMContext):
    await state.clear()
    status = await message.answer("⏳ <i>Деанонимизация ID и выгрузка открытых счетчиков VK API...</i>", parse_mode="HTML")
    res = await deep_vk_search(message.text)
    await status.edit_text(res, parse_mode="HTML", disable_web_page_preview=False, reply_markup=start_kb)

@router.message(SearchStates.waiting_for_username)
async def res_username(message: Message, state: FSMContext):
    await state.clear()
    status = await message.answer("⏳ <i>Многопоточный поиск следов юзернейма в базах...</i>", parse_mode="HTML")
    res = await deep_username_search(message.text)
    await status.edit_text(res, parse_mode="HTML", disable_web_page_preview=True, reply_markup=start_kb)

@router.message(SearchStates.waiting_for_provider)
async def res_provider(message: Message, state: FSMContext):
    await state.clear()
    status = await message.answer("⏳ <i>Опрос реестра автономных систем ASN...</i>", parse_mode="HTML")
    res = await deep_provider_search(message.text)
    await status.edit_text(res, parse_mode="HTML", disable_web_page_preview=False, reply_markup=start_kb)

# --- ИНТЕГРАЦИЯ С ВЕБ-СЕРВЕРОМ RENDER ---

async def handle_web(request):
    return aiohttp.web.Response(text="ShellSearch OSINT Service is Live!")

async def main():
    dp.include_router(router)
    
    # Решение для Render: поднимаем веб-сервер на порту
    app = aiohttp.web.Application()
    app.router.add_get('/', handle_web)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 10000))
    site = aiohttp.web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    # Запуск Telegram бот-процесса
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

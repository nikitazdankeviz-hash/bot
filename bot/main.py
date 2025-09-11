from __future__ import annotations
import asyncio, os, json, datetime as dt, pytz
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web

from .utils import CartItem, calc_total, human_rub
from .keyboards import main_menu_kb, categories_kb, products_kb, product_kb, cart_kb, admin_kb
from .storage import init_db, get_setting, set_setting, save_order, list_orders, export_orders_csv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS","").split(",") if x.strip().isdigit()]
DEFAULT_RATE = float(os.getenv("EXCHANGE_RATE", "3000"))
TZ = os.getenv("TZ","Europe/Moscow")
PORT = int(os.getenv("PORT", "8080"))

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

CARTS: dict[int, list[CartItem]] = {}

def load_catalog() -> dict:
    path = os.path.join(os.path.dirname(__file__), "data", "products.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class AddProductState(StatesGroup):
    waiting_json = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@dp.message(Command("start"))
async def start(m: Message):
    await m.answer("Привет! Это магазин (без оплаты). Выберите действие:", reply_markup=main_menu_kb().as_markup())

@dp.callback_query(F.data == "back_to_menu")
async def back_menu(c: CallbackQuery):
    await c.message.edit_text("Главное меню:", reply_markup=main_menu_kb().as_markup())

@dp.callback_query(F.data == "catalog")
async def show_catalog(c: CallbackQuery):
    cat = load_catalog()
    await c.message.edit_text("Выберите категорию:", reply_markup=categories_kb(cat["categories"]).as_markup())

@dp.callback_query(F.data.startswith("cat:"))
async def show_products(c: CallbackQuery):
    cat_id = c.data.split(":",1)[1]
    data = load_catalog()
    prods = [p for p in data["products"] if p["category"] == cat_id and p.get("active", True)]
    await c.message.edit_text("Товары:", reply_markup=products_kb(prods, cat_id).as_markup())

@dp.callback_query(F.data.startswith("prod:"))
async def prod_detail(c: CallbackQuery):
    prod_id = c.data.split(":",1)[1]
    data = load_catalog()
    prod = next((p for p in data["products"] if p["id"] == prod_id), None)
    if not prod:
        return await c.answer("Нет такого товара")
    text = f"<b>{prod['title']}</b>\nЦена: {int(prod['price_rub'])}₽"
    await c.message.edit_text(text, reply_markup=product_kb(prod_id).as_markup())

@dp.callback_query(F.data.startswith("add:"))
async def add_to_cart(c: CallbackQuery):
    _, prod_id, qty = c.data.split(":")
    qty = int(qty)
    data = load_catalog()
    prod = next((p for p in data["products"] if p["id"] == prod_id), None)
    if not prod:
        return await c.answer("Нет такого товара")
    items = CARTS.setdefault(c.from_user.id, [])
    items.append(CartItem(product_id=prod_id, title=prod['title'], qty=qty, price_rub=float(prod['price_rub'])))
    await c.answer("Добавлено в корзину")
    await show_cart(c)

@dp.callback_query(F.data == "cart")
async def show_cart(c: CallbackQuery):
    items = CARTS.get(c.from_user.id, [])
    if not items:
        return await c.message.edit_text("Корзина пуста.", reply_markup=cart_kb(False).as_markup())
    lines = [f"• {i.title} × {i.qty} = {human_rub(i.qty*i.price_rub)}" for i in items]
    total = calc_total(items)
    rate = float(get_setting("exchange_rate", str(DEFAULT_RATE)))
    lines.append(f"\nИтого: <b>{human_rub(total)}</b>\nТекущий курс: <b>{rate}</b>")
    await c.message.edit_text("\n".join(lines), reply_markup=cart_kb(True).as_markup())

@dp.callback_query(F.data == "cart_clear")
async def cart_clear(c: CallbackQuery):
    CARTS[c.from_user.id] = []
    await c.answer("Корзина очищена")
    await show_cart(c)

@dp.callback_query(F.data == "checkout")
async def checkout(c: CallbackQuery):
    items = CARTS.get(c.from_user.id, [])
    if not items:
        return await c.answer("Корзина пуста")
    total = calc_total(items)
    rate = float(get_setting("exchange_rate", str(DEFAULT_RATE)))
    order_id = save_order(c.from_user.id, c.from_user.username or "", 
                          [i.__dict__ for i in items], total, rate, 
                          comment=f"Order by @{c.from_user.username}")
    await c.message.answer(
        f"Заказ #{order_id} создан. Сумма: <b>{human_rub(total)}</b>\n"
        "Оплаты нет в этом шаблоне. Отправьте скрин/подтверждение вручную после перевода."
    )
    CARTS[c.from_user.id] = []

@dp.message(Command("admin"))
async def admin_menu(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return await m.reply("Доступ запрещён.")
    await m.answer("Админ-панель:", reply_markup=admin_kb().as_markup())

@dp.callback_query(F.data.startswith("admin:"))
async def admin_actions(c: CallbackQuery, state: FSMContext):
    if not is_admin(c.from_user.id):
        return await c.answer("Нет доступа")
    action = c.data.split(":",1)[1]
    if action == "rate":
        cur = get_setting("exchange_rate", str(DEFAULT_RATE))
        await c.message.answer(f"Текущий курс: <b>{cur}</b>\nПришлите новое значение (число).")
        await state.set_state("await_rate")
    elif action == "products":
        await c.message.answer("Отправьте JSON одной строкой для добавления/изменения каталога (перезапишет файл).")
        await state.set_state("waiting_json")
    elif action == "orders":
        orders = list_orders(20)
        if not orders:
            return await c.message.answer("Заказов пока нет.")
        text = "\n".join([f"#{o['id']} — {o['username']} — {int(o['total_rub'])}₽ — {o['status']}" for o in orders[:20]])
        await c.message.answer(text or "Пусто.")
    elif action == "export":
        fname = dt.datetime.now().strftime("exports/orders_%Y-%m-%d.csv")
        count = export_orders_csv(fname)
        await c.message.answer(f"Экспортировано строк: {count}. Файл: {fname}")

@dp.message(F.text, F.text.regexp(r"^\d+(?:\.\d+)?$"))
async def set_rate(m: Message, state: FSMContext):
    st = await state.get_state()
    if st == "await_rate":
        set_setting("exchange_rate", m.text)
        await m.reply(f"Курс обновлён: {m.text}")
        await state.clear()

@dp.message(F.text, ~F.text.regexp(r"^/.*"))
async def set_products(m: Message, state: FSMContext):
    st = await state.get_state()
    if st == "waiting_json" and is_admin(m.from_user.id):
        try:
            data = json.loads(m.text)
            path = os.path.join(os.path.dirname(__file__), "data", "products.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            await m.reply("Каталог обновлён.")
        except Exception as e:
            await m.reply(f"Ошибка: {e}")
        finally:
            await state.clear()

def setup_scheduler(loop: asyncio.AbstractEventLoop):
    tz = pytz.timezone(TZ)
    sched = AsyncIOScheduler(timezone=tz)
    async def job():
        fname = dt.datetime.now(tz).strftime("exports/orders_%Y-%m-%d.csv")
        count = export_orders_csv(fname)
        if ADMIN_IDS:
            await bot.send_message(ADMIN_IDS[0], f"[Авто] Экспортировано {count} строк в {fname}")
    sched.add_job(job, "cron", day_of_week="mon", hour=9, minute=0)
    sched.start()
    return sched

# HTTP server for Render free Web Service
from aiohttp import web

async def make_app():
    app = web.Application()
    async def index(request):
        return web.json_response({"ok": True, "service": "store-bot", "time": dt.datetime.utcnow().isoformat()})
    async def health(request):
        return web.Response(text="OK")
    app.add_routes([web.get("/", index), web.get("/healthz", health)])
    return app

async def run_http():
    app = await make_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def run_bot():
    # Ensure no webhook is set; otherwise Telegram forbids getUpdates (polling)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    # Simple retry loop to survive transient 'terminated by other getUpdates request'
    import asyncio
    for i in range(10):
        try:
            await dp.start_polling(bot)
            break
        except Exception as e:
            if "terminated by other getUpdates request" in str(e):
                await asyncio.sleep(2 + i)  # backoff
                continue
            raise


async def main():
    init_db()
    if get_setting("exchange_rate") is None:
        set_setting("exchange_rate", str(DEFAULT_RATE))
    setup_scheduler(asyncio.get_event_loop())
    await asyncio.gather(run_http(), run_bot())

if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
    except Exception:
        pass
    asyncio.run(main())

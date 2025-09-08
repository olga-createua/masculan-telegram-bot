# app.py — Telegram Shop Bot (Masculan)
# aiogram 3 + FastAPI (webhook), подходит для бесплатного деплоя на Render

import os
from fastapi import FastAPI, Request, Header, HTTPException
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, Update
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# === Переменные окружения (заполняются в Render → Environment) ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # токен от @BotFather
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "671863992"))  # ваш Telegram ID
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me")  # придумайте любой сложный ключ
BASE_URL = os.getenv("BASE_URL")  # например: https://your-service.onrender.com

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Add it as an environment variable.")

# Инициализация бота и веб-приложения
bot = Bot(BOT_TOKEN, parse_mode=None)
dp = Dispatcher()
app = FastAPI(title="Masculan Telegram Bot")

# === Каталог товаров (ваши позиции + цены) ===
PRODUCTS = [
    {"id":"p1",  "name":"Інтимний гель-змазка Masculan Вельвет 50 мл (4019042050108)",         "price": 318},
    {"id":"p2",  "name":"Інтимний гель-змазка Masculan Вельвет 5x3 мл (4019042003050)",        "price": 102},
    {"id":"p3",  "name":"Інтимний гель-змазка Masculan Зелене яблуко 75 мл (4019042700119)",   "price": 408},
    {"id":"p4",  "name":"Інтимний гель-змазка Masculan Полуниця 75 мл (4019042075026)",        "price": 408},
    {"id":"p5",  "name":"Інтимний гель-змазка Masculan Зігріваючий 75 мл (4019042075033)",     "price": 432},
    {"id":"p6",  "name":"Інтимний гель-змазка Masculan Шовк 75 мл (4019042075019)",            "price": 408},
    {"id":"p7",  "name":"Презервативи Masculan Anatomic 10 шт (4019042000042)",                "price": 288},
    {"id":"p8",  "name":"Презервативи Masculan Anatomic 3 шт (4019042000080)",                 "price": 108},
    {"id":"p9",  "name":"Презервативи Masculan Dotted 10 шт (4019042000028)",                  "price": 288},
    {"id":"p10", "name":"Презервативи Masculan Dotted 3 шт (4019042000066)",                   "price": 108},
    {"id":"p11", "name":"Презервативи Masculan Extra Double Protection 10 шт (4019042010218)","price": 288},
    {"id":"p12", "name":"Презервативи Masculan Extra Double Protection 3 шт (4019042003210)", "price": 108},
    {"id":"p13", "name":"Презервативи Masculan Extra Long Pleasure 10 шт (4019042003326)",     "price": 288},
    {"id":"p14", "name":"Презервативи Masculan Extra Long Pleasure 3 шт (4019042010324)",      "price": 108},
    {"id":"p15", "name":"Презервативи Masculan Frutti Edition 10 шт (4019042001100)",          "price": 288},
    {"id":"p16", "name":"Набір презервативів Masculan Кольорові з ароматами 150 шт (4019042021504)", "price": 3000},
    {"id":"p17", "name":"Презервативи Masculan Frutti Edition 3 шт (4019042001032)",           "price": 108},
    {"id":"p18", "name":"Презервативи Masculan Gold 10 шт (4019042000905)",                    "price": 300},
    {"id":"p19", "name":"Презервативи Masculan Gold 3 шт (4019042000936)",                     "price": 114},
    {"id":"p20", "name":"Презервативи Masculan Organic 10 шт (4019042700157)",                 "price": 300},
    {"id":"p21", "name":"Презервативи Masculan Organic 3 шт (4019042700140)",                  "price": 114},
    {"id":"p22", "name":"Презервативи Masculan Pur 10 шт (4019042701116)",                     "price": 300},
    {"id":"p23", "name":"Презервативи Masculan Pur 3 шт (4019042000639)",                      "price": 114},
    {"id":"p24", "name":"Презервативи Masculan Ribbed+Dotted 10 шт (4019042000035)",           "price": 288},
    {"id":"p25", "name":"Презервативи Masculan Ribbed+Dotted 3 шт (4019042000073)",            "price": 108},
    {"id":"p26", "name":"Презервативи Masculan Sensitive 10 шт (4019042000011)",               "price": 288},
    {"id":"p27", "name":"Презервативи Masculan Sensitive 3 шт (4019042000059)",                "price": 108},
    {"id":"p28", "name":"Набір презервативів Masculan Sensitive 150 шт (4019042011505)",       "price": 3000},
    {"id":"p29", "name":"Презервативи Masculan XXL 3 шт (4019042000356)",                      "price": 108},
    {"id":"p30", "name":"Презервативи Masculan XXL 10 шт (4019042001056)",                     "price": 288},
]

# === Машина состояний для оформления ===
class Checkout(StatesGroup):
    name = State()
    phone = State()
    address = State()

def catalog_kb():
    kb = InlineKeyboardBuilder()
    for p in PRODUCTS:
        kb.button(text=f"{p['name']} — {p['price']}₴", callback_data=f"add:{p['id']}")
    kb.button(text="🧺 Корзина", callback_data="cart")
    kb.adjust(1)
    return kb.as_markup()

def cart_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Оформити замовлення", callback_data="checkout")
    kb.button(text="⬅️ Назад у каталог", callback_data="back_catalog")
    kb.adjust(1)
    return kb.as_markup()

def get_cart(data: dict):
    return data.get("cart", {})

def add_to_cart(data: dict, pid: str):
    cart = data.setdefault("cart", {})
    cart[pid] = cart.get(pid, 0) + 1

def cart_text(cart: dict):
    if not cart:
        return "Корзина пуста."
    lines, total = [], 0
    for pid, qty in cart.items():
        p = next(p for p in PRODUCTS if p["id"] == pid)
        line_sum = p["price"] * qty
        total += line_sum
        lines.append(f"• {p['name']} × {qty} = {line_sum}₴")
    lines.append(f"\nРазом: {total}₴")
    return "\n".join(lines)

# === Хэндлеры ===
@dp.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Привіт! Оберіть товар з каталогу:", reply_markup=catalog_kb())

@dp.callback_query(F.data.startswith("add:"))
async def add_item(c: CallbackQuery, state: FSMContext):
    pid = c.data.split(":")[1]
    data = await state.get_data()
    add_to_cart(data, pid)
    await state.set_data(data)
    await c.answer("Додано в корзину")
    await c.message.edit_text("Товар додано. Що далі?", reply_markup=cart_kb())

@dp.callback_query(F.data == "cart")
async def show_cart(c: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await c.message.edit_text(cart_text(get_cart(data)), reply_markup=cart_kb())

@dp.callback_query(F.data == "back_catalog")
async def back_catalog(c: CallbackQuery):
    await c.message.edit_text("Каталог:", reply_markup=catalog_kb())

@dp.callback_query(F.data == "checkout")
async def ask_name(c: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not get_cart(data):
        await c.answer("Корзина пуста", show_alert=True)
        return
    await c.message.answer("Введіть ваше ім’я:")
    await state.set_state(Checkout.name)

@dp.message(Checkout.name)
async def ask_phone(m: Message, state: FSMContext):
    await state.update_data(customer_name=m.text.strip())
    await m.answer("Номер телефону (з кодом):")
    await state.set_state(Checkout.phone)

@dp.message(Checkout.phone)
async def ask_address(m: Message, state: FSMContext):
    await state.update_data(customer_phone=m.text.strip())
    await m.answer("Адреса/відділення для доставки:")
    await state.set_state(Checkout.address)

@dp.message(Checkout.address)
async def finalize(m: Message, state: FSMContext):
    await state.update_data(customer_address=m.text.strip())
    data = await state.get_data()
    cart = get_cart(data)

    total = 0
    lines = []
    for pid, qty in cart.items():
        p = next(p for p in PRODUCTS if p["id"] == pid)
        line_sum = p["price"] * qty
        total += line_sum
        lines.append(f"{p['name']} × {qty} = {line_sum}₴")

    order_text = (
        "🆕 Нове замовлення\n\n"
        + "\n".join(lines)
        + f"\n\nРазом: {total}₴"
        + f"\n\nКлієнт: {data.get('customer_name')}"
        + f"\nТелефон: {data.get('customer_phone')}"
        + f"\nАдреса: {data.get('customer_address')}"
        + f"\nTG: @{m.from_user.username or m.from_user.id}"
    )

    # отправляем заявку админу
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=order_text)
    await m.answer("Дякуємо! Замовлення відправлене менеджеру. Ми з вами зв’яжемося.")
    await state.set_data({})
    await state.clear()

# === FastAPI: webhook + health ===
@app.post("/webhook")
async def telegram_webhook(request: Request, x_telegram_bot_api_secret_token: str = Header(None)):
    # Простая защита по секрету (совпадает с secret_token в setWebhook)
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")
    update_data = await request.json()
    update = Update.model_validate(update_data, context={'bot': bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/")
@app.get("/health")
def health():
    return {"status": "ok"}

# Автопостановка вебхука при старте (если указан BASE_URL)
@app.on_event("startup")
async def on_startup():
    if BASE_URL:
        await bot.set_webhook(url=f"{BASE_URL}/webhook", secret_token=WEBHOOK_SECRET)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()

# Локальный запуск (опционально)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

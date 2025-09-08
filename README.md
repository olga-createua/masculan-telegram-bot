# Masculan Telegram Bot

Простой Telegram-бот для оформления заказов товаров **Masculan**.  
Реализован на **Python 3 + aiogram 3 + FastAPI**, работает через **webhook**.  
Подходит для деплоя в **Render (free plan)**.

---

## 🚀 Функционал
- Каталог товаров (готовый список из гелей-змазок и презервативов Masculan).
- Добавление товаров в корзину.
- Оформление заказа (имя, телефон, адрес).
- Отправка заказа администратору в Telegram.
- Веб-интерфейс FastAPI для webhook и проверки `/health`.

---

## 🔧 Установка и запуск локально (опционально)

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/username/masculan-telegram-bot.git
cd masculan-telegram-bot

# 2. Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Запустите
export BOT_TOKEN="ВАШ_ТОКЕН"
export ADMIN_CHAT_ID="671863992"
export WEBHOOK_SECRET="MySecretKey2024"
export BASE_URL="http://localhost:8000"

python app.py

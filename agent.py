import os
import yfinance as yf
import mplfinance as mpf
from groq import Groq
from telegram import Bot
import asyncio
from datetime import datetime

# --- Настройки берутся из секретов GitHub (мы добавим их позже) ---
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']        # например @trading_live_channel
GROQ_API_KEY = os.environ['GROQ_API_KEY']

# Тикер акции, которую анализируем. Можно поменять на другой (SPY, TSLA и т.д.)
TICKER = 'AAPL'

# --- 1. Скачиваем данные о цене с Yahoo Finance ---
data = yf.download(TICKER, period='5d', interval='1h')
last_price = data['Close'].iloc[-1]
first_price = data['Close'].iloc[0]
price_change = (last_price - first_price) / first_price * 100

# --- 2. Просим Groq написать пост ---
client = Groq(api_key=GROQ_API_KEY)
prompt = f"""
Ты – аналитик фондового рынка. Акция {TICKER}.
Последняя цена: {last_price:.2f}, изменение за 5 дней: {price_change:.1f}%.
Напиши пост для Telegram-канала (до 800 знаков):
- Краткий обзор динамики,
- Ключевые технические уровни поддержки и сопротивления,
- Настроение рынка,
- Возможный краткосрочный сетап (без рекомендаций).
Обязательно добавь в конце: «Не является инвестиционной рекомендацией».
"""
chat_completion = client.chat.completions.create(
    messages=[{"role": "user", "content": prompt}],
    model="llama3-70b-8192",
    temperature=0.7,
)
post_text = chat_completion.choices[0].message.content.strip()

# --- 3. Строим график (свечной) ---
mpf.plot(data, type='candle', volume=True,
         title=f'{TICKER} 5-дневный график',
         savefig='chart.png')

# --- 4. Отправляем фото и текст в Telegram ---
async def send_post():
    bot = Bot(token=TELEGRAM_TOKEN)
    with open('chart.png', 'rb') as photo:
        await bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=post_text)

asyncio.run(send_post())
print(f'[{datetime.now()}] Пост успешно опубликован в {CHANNEL_ID}')


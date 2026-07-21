import os
import yfinance as yf
import mplfinance as mpf
import google.generativeai as genai
from telegram import Bot
import asyncio
from datetime import datetime
import smtplib
from email.message import EmailMessage

# Настройки (будут подставлены из секретов GitHub)
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')     # если не нужен email, можно пропустить
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# Подключаем Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')  # быстрая бесплатная модель

TICKER = 'AAPL'  # тикер акции (можно поменять)

# 1. Скачиваем данные о цене
data = yf.download(TICKER, period='5d', interval='1h')
last_price = data['Close'].iloc[-1]
first_price = data['Close'].iloc[0]
price_change = (last_price - first_price) / first_price * 100

# 2. Просим Gemini написать пост
prompt = f"""
Ты – аналитик фондового рынка. Акция {TICKER}.
Последняя цена: {last_price:.2f}, изменение за 5 дней: {price_change:.1f}%.
Напиши пост для соцсетей (до 800 знаков):
- Обзор динамики,
- Ключевые технические уровни,
- Настроение,
- Возможный сетап (без рекомендаций).
В конце: «Не является инвестиционной рекомендацией».
"""
response = model.generate_content(prompt)
post_text = response.text.strip()

# 3. Рисуем график
mpf.plot(data, type='candle', volume=True,
         title=f'{TICKER} 5-дневный график',
         savefig='chart.png')

# 4. Отправляем в Telegram
async def send_telegram():
    bot = Bot(token=TELEGRAM_TOKEN)
    with open('chart.png', 'rb') as photo:
        await bot.send_photo(chat_id=CHANNEL_ID, photo=photo, caption=post_text)
    print('Пост отправлен в Telegram')

asyncio.run(send_telegram())

# 5. Отправляем копию на почту (если заданы настройки)
if EMAIL_ADDRESS and EMAIL_PASSWORD:
    msg = EmailMessage()
    msg['Subject'] = f'Новый пост по {TICKER} ({datetime.now().strftime("%d.%m.%Y")})'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    msg.set_content(post_text)
    with open('chart.png', 'rb') as f:
        img_data = f.read()
    msg.add_attachment(img_data, maintype='image', subtype='png', filename='chart.png')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print('Письмо отправлено на почту')
else:
    print('Email не настроен, пропускаем.')



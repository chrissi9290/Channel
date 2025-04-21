import requests
import time
import telegram
import asyncio
import websockets
import json
from threading import Thread
from datetime import datetime
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = '7807606650:AAHv4hr01aqQzrj5u3CwldPVCj-iKGVFWzI'
CHANNEL_USERNAME = '@DiamondCal'
BIRDEYE_API_KEY = '1c68ac943a2a423d91e73f1617b8ddf5'
bot = telegram.Bot(token=BOT_TOKEN)

# Zeitstempel für Statusbefehl
last_birdeye_check = "–"
last_pump_event = "–"
last_top10_post = "–"

# --------------------------------
# Top 10 Coins nach 1h-Gewinn über Birdeye
# --------------------------------
def post_top_10_gainers():
    global last_top10_post
    print("[Top10] gestartet.")
    first_run = True
    while True:
        try:
            headers = {'X-API-KEY': BIRDEYE_API_KEY}
            response = requests.get('https://public-api.birdeye.so/defi/token_trending', headers=headers)
            data = response.json()
            tokens = data.get('data', [])

            # Filtere Tokens mit ausreichender Liquidität
            filtered = []
            for token in tokens:
                try:
                    price_change = float(token.get('price_change_percentage_1h', 0))
                    liquidity = float(token.get('liquidity', 0))
                    if liquidity > 1000:
                        filtered.append((price_change, token))
                except:
                    continue

            top_10 = sorted(filtered, key=lambda x: x[0], reverse=True)[:10]
            last_top10_post = datetime.now().strftime("%H:%M:%S")

            if not top_10:
                print("[Top10] Keine Top Coins gefunden.")
                time.sleep(3600)
                continue

            message = "🔥 *Top 10 Coins – 1h Gewinn* 🔥\n\n"
            for idx, (change, token) in enumerate(top_10, 1):
                name = token.get('name', 'Unbekannt')
                symbol = token.get('symbol', '')
                price = float(token.get('price', 0))
                token_address = token.get('address', '')
                message += f"{idx}. [{name} ({symbol})](https://birdeye.so/token/{token_address}) – *+{change:.1f}%* – ${price:.6f}\n"

            message += "\n#crypto #gainers #trending"

            bot.send_message(chat_id=CHANNEL_USERNAME, text=message, parse_mode=telegram.ParseMode.MARKDOWN)

        except Exception as e:
            print(f"[Top10 Fehler] {e}")

        time.sleep(3600 if not first_run else 0)
        first_run = False

# --------------------------------
# Pump.fun – WebSocket live
# --------------------------------
async def pumpfun_listener():
    global last_pump_event
    print("[Pump.fun] gestartet.")
    uri = "wss://pumpportal.fun/api/data"
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({"method": "subscribeNewToken"}))
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)

                if data.get("method") == "newToken":
                    token = data.get("params", {})
                    name = token.get("name", "Unbekannt")
                    symbol = token.get("symbol", "")
                    mint = token.get("mint", "")
                    liquidity = token.get("liquidity", {}).get("baseTokenAmount", 0)
                    chart_url = f"https://pump.fun/{mint}"

                    last_pump_event = datetime.now().strftime("%H:%M:%S")

                    nachricht = (
                        f"🚀 *Neuer Pump.fun Token gelistet!*\n\n"
                        f"*Name:* {name} ({symbol})\n"
                        f"*Chain:* #solana\n"
                        f"*Preis:* _nicht verfügbar_\n"
                        f"*Liquidity:* {liquidity} SOL\n"
                        f"*FDV / Volumen:* _nicht verfügbar_\n\n"
                        f"[📊 Token auf Pump.fun ansehen]({chart_url})\n"
                        f"#crypto #listing #{symbol.lower()} #solana"
                    )

                    bot.send_message(chat_id=CHANNEL_USERNAME, text=nachricht, parse_mode=telegram.ParseMode.MARKDOWN)

    except Exception as e:
        print(f"[Pump.fun Fehler] {e}")
        await asyncio.sleep(10)
        await pumpfun_listener()

# --------------------------------
# /status Command
# --------------------------------
def status_handler(update, context):
    message = (
        f"✅ *Bot-Status:*\n\n"
        f"• Birdeye zuletzt geprüft: `{last_top10_post}`\n"
        f"• Pump.fun letztes Event: `{last_pump_event}`"
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=telegram.ParseMode.MARKDOWN)

def telegram_commands():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("status", status_handler))
    updater.start_polling()
    updater.idle()

# --------------------------------
# Threads starten
# --------------------------------
def start_top10():
    post_top_10_gainers()

def start_pumpfun():
    asyncio.run(pumpfun_listener())

if __name__ == '__main__':
    Thread(target=start_top10).start()
    Thread(target=start_pumpfun).start()
    Thread(target=telegram_commands).start()
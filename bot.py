import requests
import time
import telegram
import asyncio
import websockets
import json
from threading import Thread
from datetime import datetime

BOT_TOKEN = '7807606650:AAHv4hr01aqQzrj5u3CwldPVCj-iKGVFWzI'
CHANNEL_USERNAME = '@DiamondCal'
bot = telegram.Bot(token=BOT_TOKEN)

# Zeitstempel für Status-Check
last_dex_check = "–"
last_pump_event = "–"
last_top10_post = "–"

gepostete_pairs = set()

# --------------------------------
# DexScreener – Neue Listings
# --------------------------------
def fetch_dexscreener():
    global last_dex_check
    while True:
        try:
            print("[DexScreener] Hole Daten...")
            response = requests.get('https://api.dexscreener.com/latest/dex/pairs')
            data = response.json()

            pairs = data.get('pairs', [])
            print(f"[DexScreener] Gefundene Paare: {len(pairs)}")

            last_dex_check = datetime.now().strftime("%H:%M:%S")

            for pair in pairs:
                pair_id = pair.get('pairAddress')
                if pair_id in gepostete_pairs:
                    continue

                name = pair.get('baseToken', {}).get('name', 'Unbekannt')
                symbol = pair.get('baseToken', {}).get('symbol', '')
                chain = pair.get('chainId', '')
                price = pair.get('priceUsd', '0')
                liquidity = float(pair.get('liquidity', {}).get('usd', 0))
                fdv = float(pair.get('fdv', 0) or 0)
                volume = float(pair.get('volume', {}).get('h24', 0))
                chart_url = f"https://dexscreener.com/{chain}/{pair_id}?interval=5m"

                nachricht = (
                    f"🚀 *Neuer Coin gelistet!*\n\n"
                    f"*Name:* {name} ({symbol})\n"
                    f"*Chain:* #{chain.lower()}\n"
                    f"*Preis:* ${float(price):,.6f}\n"
                    f"*Liquidity:* ${liquidity:,.0f}\n"
                    f"*FDV (Market Cap):* ${fdv:,.0f}\n"
                    f"*Volumen (24h):* ${volume:,.0f}\n\n"
                    f"[📊 5-Minuten-Chart ansehen]({chart_url})\n"
                    f"#crypto #listing #{symbol.lower()} #{chain.lower()}"
                )

                bot.send_message(chat_id=CHANNEL_USERNAME, text=nachricht, parse_mode=telegram.ParseMode.MARKDOWN)
                gepostete_pairs.add(pair_id)

            time.sleep(60)

        except Exception as e:
            print(f"[DexScreener Fehler] {e}")
            time.sleep(30)

# --------------------------------
# Pump.fun – WebSocket live
# --------------------------------
async def pumpfun_listener():
    global last_pump_event
    uri = "wss://pumpportal.fun/api/data"
    try:
        async with websockets.connect(uri) as websocket:
            print("[Pump.fun] WebSocket verbunden...")
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
# Top 10 Coins nach 1h-Gewinn
# --------------------------------
def post_top_10_gainers():
    global last_top10_post
    first_run = True
    while True:
        try:
            print("[Top10] Hole DexScreener-Daten für Ranking...")
            response = requests.get('https://api.dexscreener.com/latest/dex/pairs')
            data = response.json()
            pairs = data.get('pairs', [])

            filtered = []
            for pair in pairs:
                try:
                    change = float(pair.get('priceChange', {}).get('h1', 0))
                    liquidity = float(pair.get('liquidity', {}).get('usd', 0))
                    if liquidity > 1000:
                        filtered.append((change, pair))
                except:
                    continue

            top_10 = sorted(filtered, key=lambda x: x[0], reverse=True)[:10]

            if not top_10:
                print("[Top10] Keine Top Coins gefunden.")
                time.sleep(3600)
                continue

            message = "🔥 *Top 10 Coins – 1h Gewinn* 🔥\n\n"
            for idx, (change, pair) in enumerate(top_10, 1):
                name = pair.get('baseToken', {}).get('name', 'Unbekannt')
                symbol = pair.get('baseToken', {}).get('symbol', '')
                chain = pair.get('chainId', '')
                price = float(pair.get('priceUsd', 0) or 0)
                url = pair.get('url', '')
                message += f"{idx}. [{name} ({symbol})]({url}) – *+{change:.1f}%* – ${price:.6f} – #{chain.lower()}\n"

            message += "\n#crypto #gainers #trending"

            last_top10_post = datetime.now().strftime("%H:%M:%S")
            print("[Top10] Liste gesendet.")
            bot.send_message(chat_id=CHANNEL_USERNAME, text=message, parse_mode=telegram.ParseMode.MARKDOWN)

        except Exception as e:
            print(f"[Top10 Fehler] {e}")

        time.sleep(3600 if not first_run else 0)
        first_run = False

# --------------------------------
# /status Command
# --------------------------------
from telegram.ext import Updater, CommandHandler

def status_handler(update, context):
    message = (
        f"✅ *Bot-Status:*\n\n"
        f"• DexScreener zuletzt geprüft: `{last_dex_check}`\n"
        f"• Pump.fun letztes Event: `{last_pump_event}`\n"
        f"• Top 10 zuletzt gepostet: `{last_top10_post}`"
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
def start_dexscreener():
    fetch_dexscreener()

def start_pumpfun():
    asyncio.run(pumpfun_listener())

def start_top10():
    post_top_10_gainers()

if __name__ == '__main__':
    Thread(target=start_dexscreener).start()
    Thread(target=start_pumpfun).start()
    Thread(target=start_top10).start()
    Thread(target=telegram_commands).start()
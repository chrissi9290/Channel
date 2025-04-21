import requests
import time
import telegram
import asyncio
import websockets
import json
from threading import Thread

BOT_TOKEN = '7807606650:AAHv4hr01aqQzrj5u3CwldPVCj-iKGVFWzI'
CHANNEL_USERNAME = '@DiamondCal'
bot = telegram.Bot(token=BOT_TOKEN)

gepostete_pairs = set()

# --------------------------------
# DexScreener – Neue Listings
# --------------------------------
def fetch_dexscreener():
    while True:
        try:
            response = requests.get('https://api.dexscreener.com/latest/dex/pairs')
            data = response.json()

            for pair in data.get('pairs', []):
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
                url = pair.get('url', chart_url)

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
            print(f"DexScreener Fehler: {e}")
            time.sleep(30)

# --------------------------------
# Pump.fun – WebSocket live
# --------------------------------
async def pumpfun_listener():
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
        print(f"Pump.fun Fehler: {e}")
        await asyncio.sleep(10)
        await pumpfun_listener()

# --------------------------------
# Top 10 Coins nach 1h-Gewinn
# --------------------------------
def post_top_10_gainers():
    while True:
        try:
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

            bot.send_message(chat_id=CHANNEL_USERNAME, text=message, parse_mode=telegram.ParseMode.MARKDOWN)

        except Exception as e:
            print(f"Top10 Fehler: {e}")

        time.sleep(3600)  # 60 Minuten warten

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
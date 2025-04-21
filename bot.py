import requests
import time
import telegram

# Telegram Bot Konfiguration
BOT_TOKEN = '7807606650:AAHv4hr01aqQzrj5u3CwldPVCj-iKGVFWzI'
CHANNEL_USERNAME = '@DiamondCal'

bot = telegram.Bot(token=BOT_TOKEN)

# Testnachricht beim Start
bot.send_message(chat_id=CHANNEL_USERNAME, text='Bot wurde erfolgreich gestartet!')

gepostete_pairs = set()

while True:
    try:
        response = requests.get('https://api.dexscreener.com/latest/dex/pairs')
        data = response.json()

        for pair in data.get('pairs', []):
            pair_id = pair['pairAddress']
            if pair_id not in gepostete_pairs:
                name = pair.get('baseToken', {}).get('name', 'Unbekannt')
                symbol = pair.get('baseToken', {}).get('symbol', '')
                chain = pair.get('chainId', '')
                price = pair.get('priceUsd', '0')
                url = pair.get('url', 'https://dexscreener.com')
                liquidity = float(pair.get('liquidity', {}).get('usd', 0))
                fdv = float(pair.get('fdv', 0) or 0)
                volume = float(pair.get('volume', {}).get('h24', 0))

                chart_url = f"https://dexscreener.com/{chain}/{pair_id}?interval=5m"

                nachricht = (
                    f"🚀 *Neuer Coin gelistet!*\n\n"
                    f"*Name:* {name} ({symbol})\n"
                    f"*Chain:* #{chain.lower()}\n"
                    f"*Preis:* ${price}\n"
                    f"*Liquidity:* ${liquidity:,.0f}\n"
                    f"*FDV (Market Cap):* ${fdv:,.0f}\n"
                    f"*Volumen (24h):* ${volume:,.0f}\n\n"
                    f"[📊 5-Minuten-Chart ansehen]({chart_url})\n"
                    f"#crypto #listing #{symbol.lower()}"
                )

                bot.send_message(chat_id=CHANNEL_USERNAME, text=nachricht, parse_mode=telegram.ParseMode.MARKDOWN)
                gepostete_pairs.add(pair_id)

        time.sleep(60)

    except Exception as e:
        print(f"Fehler: {e}")
        time.sleep(30)
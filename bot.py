import requests
import time
import telegram

BOT_TOKEN = '7807606650:AAHv4hr01aqQzrj5u3CwldPVCj-iKGVFWzI'
CHANNEL_USERNAME = '@DiamondCal'

bot = telegram.Bot(token=BOT_TOKEN)
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

                nachricht = (
                    f"**Neuer Coin gelistet!**\n"
                    f"Name: {name} ({symbol})\n"
                    f"Chain: {chain}\n"
                    f"Preis: ${price}\n"
                    f"[Zur DexScreener Seite]({url})"
                )

                bot.send_message(chat_id=CHANNEL_USERNAME, text=nachricht, parse_mode=telegram.ParseMode.MARKDOWN)
                gepostete_pairs.add(pair_id)

        time.sleep(60)

    except Exception as e:
        print(f"Fehler: {e}")
        time.sleep(30)

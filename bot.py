import requests
import time
import telegram
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os

# Bot config
BOT_TOKEN = '7807606650:AAHv4hr01aqQzrj5u3CwldPVCj-iKGVFWzI'
CHANNEL_USERNAME = '@DiamondCal'
bot = telegram.Bot(token=BOT_TOKEN)

# Screenshot-Funktion (DexScreener Chart)
def screenshot_chart(url, filename='chart.png'):
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--window-size=1200,800")
    
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.get(url)
    time.sleep(5)  # warten, bis Seite geladen ist
    driver.save_screenshot(filename)
    driver.quit()
    return filename

gepostete_pairs = set()

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
            url = pair.get('url', 'https://dexscreener.com')
            chart_url = f"https://dexscreener.com/{chain}/{pair_id}?interval=5m"

            nachricht = (
                f"🚀 *Neuer Coin gelistet!*\n\n"
                f"*Name:* {name} ({symbol})\n"
                f"*Chain:* #{chain.lower()}\n"
                f"*Preis:* ${float(price):,.6f}\n"
                f"*Liquidity:* ${liquidity:,.0f}\n"
                f"*FDV (Market Cap):* ${fdv:,.0f}\n"
                f"*Volumen (24h):* ${volume:,.0f}\n\n"
                f"[📊 5-Minuten-Chart öffnen]({chart_url})\n"
                f"[➡️ DexScreener öffnen]({url})\n\n"
                f"#crypto #listing #{symbol.lower()} #{chain.lower()}"
            )

            # Screenshot vom Chart holen
            chart_file = screenshot_chart(chart_url)

            # Bild + Text an Telegram senden
            with open(chart_file, 'rb') as img:
                bot.send_photo(chat_id=CHANNEL_USERNAME, photo=img, caption=nachricht, parse_mode=telegram.ParseMode.MARKDOWN)

            gepostete_pairs.add(pair_id)
            os.remove(chart_file)  # aufräumen

        time.sleep(60)

    except Exception as e:
        print(f"Fehler: {e}")
        time.sleep(30)
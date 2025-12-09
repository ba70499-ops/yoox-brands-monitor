# YOOX 指定ブランド入荷監視 - エラー時通知なし版

import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import sys

CHANNEL_TOKEN = os.getenv('CHANNEL_TOKEN')
YOOX_URL_MEN = "https://www.yoox.com/us/men/shoes"
YOOX_URL_WOMEN = "https://www.yoox.com/us/women/shoes"
PRICE_DB_FILE = "/tmp/yoox_brands.json"
LINE_API_URL = "https://api.line.me/v2/bot/message/broadcast"

TARGET_BRANDS = ['Edward Green', 'George Cleverley', 'Anthony Cleverley', 'Crockett & Jones', 'Alden', 'Paraboot', 'John Lobb']

if not CHANNEL_TOKEN:
    print("❌ CHANNEL_TOKEN 未設定")
    sys.exit(1)

def send_line(text):
    headers = {"Authorization": f"Bearer {CHANNEL_TOKEN}", "Content-Type": "application/json"}
    data = {"messages": [{"type": "text", "text": text}]}
    try:
        r = requests.post(LINE_API_URL, headers=headers, json=data, timeout=10)
        print(f"✅ LINE: {r.status_code}")
        return True
    except:
        return False

def load_db():
    try:
        if os.path.exists(PRICE_DB_FILE):
            with open(PRICE_DB_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_db(db):
    with open(PRICE_DB_FILE, 'w') as f:
        json.dump(db, f)

def check_yoox(url, gender):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.content, 'html.parser')
        text = soup.get_text().lower()
        found = [brand for brand in TARGET_BRANDS if brand.lower() in text]
        return [f"{gender}:{b}" for b in found]
    except:
        print(f"❌ {gender} YOOXエラー（通知なし）")
        return None

def main():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')
    db = load_db()
    
    men = check_yoox(YOOX_URL_MEN, "Men")
    women = check_yoox(YOOX_URL_WOMEN, "Women")
    
    if men is None or women is None:
        print("📊 YOOXエラー → 通知なし（正常）")
        return
    
    all_found = men + women
    new_arrivals = [b for b in all_found if b not in db.get('last_seen', [])]
    
    if new_arrivals:
        msg = f"🆕 【YOOX入荷】{len(new_arrivals)}件\n⏰ {timestamp}\n\n" + "\n".join(new_arrivals)
        send_line(msg)
    
    db['last_seen'] = all_found
    save_db(db)

if __name__ == "__main__":
    main()

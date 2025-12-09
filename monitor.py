#!/usr/bin/env python3
# YOOX 指定ブランド入荷監視 - 2時間ごと

import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import sys
import re

CHANNEL_TOKEN = os.getenv('CHANNEL_TOKEN')
YOOX_URL_MEN = "https://www.yoox.com/us/men/shoes"
YOOX_URL_WOMEN = "https://www.yoox.com/us/women/shoes"
PRICE_DB_FILE = "/tmp/yoox_brands.json"
LINE_API_URL = "https://api.line.me/v2/bot/message/broadcast"

# 指定ブランドリスト
TARGET_BRANDS = [
    'Edward Green', 'George Cleverley', 'Anthony Cleverley', 
    'Crockett & Jones', 'Alden', 'Paraboot', 'John Lobb'
]

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

def check_yoox_brands(url, gender):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.content, 'html.parser')
        found_brands = []
        
        # 全テキストからブランド検索
        text = soup.get_text()
        for brand in TARGET_BRANDS:
            if brand.lower() in text.lower():
                found_brands.append(f"{gender}:{brand}")
        
        print(f"👠 {gender}: {len(found_brands)}ブランド検知")
        return found_brands
    except:
        return []

def main():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')
    db = load_db()
    
    # メンズ＆ウィメンズ両方チェック
    men_brands = check_yoox_brands(YOOX_URL_MEN, "Men")
    women_brands = check_yoox_brands(YOOX_URL_WOMEN, "Women")
    
    all_found = men_brands + women_brands
    
    # 新規入荷検知（DBにないブランド）
    new_arrivals = [brand for brand in all_found if brand not in db.get('last_seen', [])]
    
    if new_arrivals:
        message = f"🆕 【YOOX入荷】{len(new_arrivals)}ブランド\n⏰ {timestamp}\n\n"
        for brand in new_arrivals:
            message += f"✨ {brand}\n"
        message += f"🔗 {YOOX_URL_MEN}\n{YOOX_URL_WOMEN}"
        
        send_line(message)
        print(f"✅ YOOX入荷通知: {len(new_arrivals)}ブランド")
    else:
        print("📊 YOOX新入荷なし")
    
    # DB更新
    db['last_seen'] = all_found
    save_db(db)
    print("✅ YOOX監視完了")

if __name__ == "__main__":
    main()

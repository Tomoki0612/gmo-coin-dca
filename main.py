import os
import requests
import json
import hmac
import hashlib
import time
from datetime import datetime
import logging
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# BitFlyer API設定
BITFLYER_API_KEY = os.getenv('BITFLYER_API_KEY')
BITFLYER_API_SECRET = os.getenv('BITFLYER_API_SECRET')
BITFLYER_API_ENDPOINT = 'https://api.bitflyer.com'

# GMOコイン API設定
GMO_API_KEY = os.getenv('GMO_API_KEY')
GMO_API_SECRET = os.getenv('GMO_API_SECRET')
GMO_API_ENDPOINT = 'https://api.coin.z.com/private'

# 取引設定
TRADE_AMOUNT = 10000  # 10,000円の取引に設定

def bitflyer_get_signature(method, endpoint, body):
    timestamp = str(time.time())
    message = timestamp + method + endpoint + body
    signature = hmac.new(BITFLYER_API_SECRET.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return signature, timestamp

def bitflyer_place_market_order(amount):
    method = 'POST'
    endpoint = '/v1/me/sendchildorder'
    body = json.dumps({
        "product_code": "BTC_JPY",
        "child_order_type": "MARKET",
        "side": "BUY",
        "size": amount,
    })

    signature, timestamp = bitflyer_get_signature(method, endpoint, body)

    headers = {
        'ACCESS-KEY': BITFLYER_API_KEY,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-SIGN': signature,
        'Content-Type': 'application/json'
    }

    response = requests.post(BITFLYER_API_ENDPOINT + endpoint, headers=headers, data=body)
    return response.json()

def gmo_get_signature(path, query, body):
    timestamp = str(int(time.time() * 1000))
    text = timestamp + 'POST' + path + query + body
    signature = hmac.new(GMO_API_SECRET.encode('utf-8'), text.encode('utf-8'), hashlib.sha256).hexdigest()
    return signature, timestamp

def gmo_place_market_order(amount):
    path = '/v1/order'
    query = ''
    body = json.dumps({
        "symbol": "BTC",
        "side": "BUY",
        "executionType": "MARKET",
        "size": str(amount)
    })

    signature, timestamp = gmo_get_signature(path, query, body)

    headers = {
        'API-KEY': GMO_API_KEY,
        'API-TIMESTAMP': timestamp,
        'API-SIGN': signature,
        'Content-Type': 'application/json'
    }

    response = requests.post(GMO_API_ENDPOINT + path, headers=headers, data=body)
    return response.json()

def get_btc_price(exchange):
    if exchange == 'bitflyer':
        response = requests.get(BITFLYER_API_ENDPOINT + '/v1/ticker?product_code=BTC_JPY')
        return float(response.json()['ltp'])
    elif exchange == 'gmo':
        response = requests.get('https://api.coin.z.com/public/v1/ticker?symbol=BTC')
        return float(response.json()['data'][0]['last'])

def main():
    logging.info("プログラムが開始されました")

    # BitFlyerでの注文
    bitflyer_price = get_btc_price('bitflyer')
    bitflyer_amount = TRADE_AMOUNT / bitflyer_price
    logging.info(f"BitFlyer - 現在のBTC価格: {bitflyer_price} JPY")
    logging.info(f"BitFlyer - 購入予定量: {bitflyer_amount:.8f} BTC")
    
    bitflyer_result = bitflyer_place_market_order(bitflyer_amount)
    logging.info(f"BitFlyer - 注文結果: {bitflyer_result}")

    # GMOコインでの注文
    gmo_price = get_btc_price('gmo')
    gmo_amount = TRADE_AMOUNT / gmo_price
    logging.info(f"GMOコイン - 現在のBTC価格: {gmo_price} JPY")
    logging.info(f"GMOコイン - 購入予定量: {gmo_amount:.8f} BTC")
    
    gmo_result = gmo_place_market_order(gmo_amount)
    logging.info(f"GMOコイン - 注文結果: {gmo_result}")

    logging.info("プログラムが終了しました")

if __name__ == "__main__":
    main()
import os
import requests
import json
import hmac
import hashlib
import time
import logging
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GMOコイン API設定
GMO_API_KEY = os.getenv('GMO_API_KEY')
GMO_API_SECRET = os.getenv('GMO_API_SECRET')
GMO_API_ENDPOINT = 'https://api.coin.z.com'

# 取引設定
TRADE_AMOUNT = 30000  # 30,000円の取引に設定

def gmo_get_signature(method, path, query, body):
    timestamp = str(int(time.time() * 1000))
    text = timestamp + method + path + query + body
    signature = hmac.new(GMO_API_SECRET.encode('utf-8'), text.encode('utf-8'), hashlib.sha256).hexdigest()
    return signature, timestamp

def gmo_api_request(method, path, query='', body=''):
    signature, timestamp = gmo_get_signature(method, path, query, body)
    headers = {
        'API-KEY': GMO_API_KEY,
        'API-TIMESTAMP': timestamp,
        'API-SIGN': signature,
        'Content-Type': 'application/json'
    }
    url = f"{GMO_API_ENDPOINT}{path}"
    if query:
        url += f"?{query}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, data=body)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None

def gmo_place_market_order(amount):
    path = '/private/v1/order'
    body = json.dumps({
        "symbol": "BTC",
        "side": "BUY",
        "executionType": "MARKET",
        "size": str(amount)
    })
    return gmo_api_request('POST', path, body=body)

def get_btc_price():
    response = gmo_api_request('GET', '/public/v1/ticker', query='symbol=BTC')
    if response and response['status'] == 0:
        return float(response['data'][0]['last'])
    else:
        raise Exception(f"GMO API error: {response['messages'] if response else 'No response'}")

def main():
    logging.info("プログラムが開始されました")

    try:
        # BTCの現在価格を取得
        btc_price = get_btc_price()
        if btc_price is None:
            raise Exception("BTCの価格取得に失敗しました")

        # 購入量の計算
        btc_amount = TRADE_AMOUNT / btc_price
        logging.info(f"GMOコイン - 現在のBTC価格: {btc_price} JPY")
        logging.info(f"GMOコイン - 購入予定量: {btc_amount:.8f} BTC")
        
        # 注文の実行
        order_result = gmo_place_market_order(btc_amount)
        if order_result and order_result['status'] == 0:
            logging.info(f"GMOコイン - 注文成功: {order_result['data']}")
        else:
            logging.error(f"GMOコイン - 注文失敗: {order_result}")

    except Exception as e:
        logging.error(f"エラーが発生しました: {e}")

    logging.info("プログラムが終了しました")

if __name__ == "__main__":
    main()
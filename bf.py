import pandas as pd
import time


from cryptography.fernet import Fernet
from rsa import encrypt

# encryption decryption class


class simple_en_decrypt:
    def __init__(self, key=None):
        if key is None:  # 키가 없다면
            key = Fernet.generate_key()  # 키를 생성한다
        self.key = key
        self.f = Fernet(self.key)

    def encrypt(self, data, is_out_string=True):
        if isinstance(data, bytes):
            ou = self.f.encrypt(data)  # 바이트형태이면 바로 암호화
        else:
            ou = self.f.encrypt(data.encode('utf-8'))  # 인코딩 후 암호화
        if is_out_string is True:
            return ou.decode('utf-8')  # 출력이 문자열이면 디코딩 후 반환
        else:
            return ou

    def decrypt(self, data, is_out_string=True):
        if isinstance(data, bytes):
            ou = self.f.decrypt(data)  # 바이트형태이면 바로 복호화
        else:
            ou = self.f.decrypt(data.encode('utf-8'))  # 인코딩 후 복호화
        if is_out_string is True:
            return ou.decode('utf-8')  # 출력이 문자열이면 디코딩 후 반환
        else:
            return ou


# key = Fernet.generate_key()
# print(key)

simple_en_decrypt = simple_en_decrypt(
    b'ICYcnGOXMmtPNDkTyQ2Z-Vn4jAkzeGUNb92qobkzdL4=')

original_access = "Zd2awwadeB2BFrxvs3tLQixrpVtkM8PfvvCVZAHeaF1RSYWckSOdUfJvwt6elXeF"
encrypt_original_access = simple_en_decrypt.encrypt(original_access)



# ----------------- binance functions -----------------------


'''
ohclv: candle data
standard_date
    -1: today(now)
    -2: yesterday / before
'''


def get_RSI(ohlcv, period, standard_date):
    ohlcv["close"] = ohlcv["close"]
    delta = ohlcv["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    return float(pd.Series(100 - (100 / (1 + RS)), name="RSI").iloc[standard_date])


def get_MA(ohclv, period, standard_date):
    close = ohclv["close"]
    ma = close.rolling(period).mean()
    return float(ma[standard_date])


# period: (1d,4h,1h,15m,10m,1m ...)
def get_ohlcv(binance, ticker, period):
    btc_ohlcv = binance.fetch_ohlcv(ticker, period)
    ohlcv = pd.DataFrame(btc_ohlcv, columns=[
                         'datetime', 'open', 'high', 'low', 'close', 'volume'])
    ohlcv['datetime'] = pd.to_datetime(ohlcv['datetime'], unit='ms')
    ohlcv.set_index('datetime', inplace=True)
    return ohlcv


# cut_rate: (1.0: -100% clearing, 0.1: -10% stop loss)
def set_stop_loss(binance, ticker, cut_rate):
    time.sleep(0.1)
    orders = binance.fetch_orders(ticker)

    stop_loss_ok = False
    for order in orders:

        if order['status'] == "open" and order['type'] == 'stop_market':
            # print(order)
            stop_loss_ok = True
            break

    # if no stop loss -> take order
    if stop_loss_ok == False:

        time.sleep(10.0)

        balance = binance.fetch_balance(params={"type": "future"})
        time.sleep(0.1)

        amt = 0
        entry_price = 0
        leverage = 0
        for posi in balance['info']['positions']:
            if posi['symbol'] == ticker.replace("/", ""):
                entry_price = float(posi['entryPrice'])
                amt = float(posi['positionAmt'])
                leverage = float(posi['leverage'])

        side = "sell"
        if amt < 0:
            side = "buy"

        danger_rate = ((100.0 / leverage) * cut_rate) * 1.0

        # stop loss price for long
        stop_price = entry_price * (1.0 - danger_rat * 0.01)

        # stop loss price for short
        if amt < 0:
            stop_price = entry_price * (1.0 + danger_rate * 0.01)

        params = {
            'stop_price': stop_price,
            'close_position': True
        }

        print("side:", side, "   stop_price:",
              stop_price, "   entry_price:", entry_price)

        # stop loss order
        print(binance.create_order(ticker, 'STOP_MARKET',
              side, abs(amt), stop_price, params))

        print("--------------- STOPLOSS SETTING DONE ---------------")


# amount for buying
def get_amount(usdt, coin_price, rate):

    target = usdt * rate

    amount = target / coin_price
    # at least 0.001 coin for trading
    if amount < 0.001:
        amount = 0.001

    #print("amout", amout)
    return amount


def get_coin_current_price(binance, ticker):
    coin_info = binance.fetch_ticker(ticker)
    coin_price = coin_info['last']  # coin_info['close'] == coin_info['last']

    return coin_price

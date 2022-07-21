import pandas as pd
import time
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
        stop_price = entry_price * (1.0 - danger_rate * 0.01)

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

# ---------------- library -------------------------
from aem import con
import pyupbit
import time
import pandas as pd
from regex import P

access = "JW7G0hr9xnBWpejlquZkEW78db0GXX1ROrPgK6ws"
secret = "tWLOFowynAXsT5UitsM4tPPuL1uIxrMNtYThIDZj"
upbit = pyupbit.Upbit(access, secret)

# ----------------- functions -----------------------

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


'''
interval: interval(day, week, minute5 ...)
top: top volume money stocks
'''


def get_top_coin_list(interval, top):
    print("------------------ Get Top Coin List Start ---------------")
    tickers = pyupbit.get_tickers("KRW")
    dic_coin_money = dict()

    for ticker in tickers:
        try:
            day_candle = pyupbit.get_ohlcv(ticker, interval)
            volume_money = (day_candle['close'][-1] * day_candle['volume']
                            [-1]) + (day_candle['close'][-2] * day_candle['volume'][-2])

            dic_coin_money[ticker] = volume_money

            print(ticker, dic_coin_money[ticker])
            time.sleep(0.02)

        except Exception as e:
            print("exception:", e)

    dic_sorted_coin_money = sorted(
        dic_coin_money.items(), key=lambda x: x[1], reverse=True)

    coin_list = list()
    cnt = 0

    for coin_data in dic_sorted_coin_money:
        cnt += 1
        if cnt <= top:
            coin_list.append(coin_data[0])
        else:
            break
    print("------------------ Returned Top Coin List ---------------")

    return coin_list


def check_coin_in_list(coin_list, ticker):
    in_coin_ok = False
    for coin_ticker in coin_list:
        if coin_ticker == ticker:
            in_coin_ok = True
            break

    return in_coin_ok


# ---------------------- variables --------------------------
top_coin_list = get_top_coin_list("week", 10)
danger_coin_list = ["KRW-DOGE"]
my_coin_list = []
tickers = pyupbit.get_tickers("KRW")

# ------------------- working part ----------------------------
print("--------------- BTC BOT WORKING ---------------")

for ticker in tickers:
    try:
        if check_coin_in_list(top_coin_list, ticker) == False:
            continue
        # if check_coin_in_list(danger_coin_list, ticker) == True:
        #     continue
        # if check_coin_in_list(my_coin_list, ticker) == False:
        #     continue
        print(ticker, "is target")
    except Exception as e:
        print(e)

print("----------------------------------------")

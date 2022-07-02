import pyupbit
import time
import pandas as pd

access = "JW7G0hr9xnBWpejlquZkEW78db0GXX1ROrPgK6ws"
secret = "tWLOFowynAXsT5UitsM4tPPuL1uIxrMNtYThIDZj"
upbit = pyupbit.Upbit(access, secret)

# --------------------------------------------------

# upbit.buy_market_order("KRW-BTC", 5000)
'''
ohclv: candle data 
standard_date
    -1: today(now)
    -2: yesterday
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


def get_MA(ohclv, perode, standard_date):


    # ------------------------------------------------------
day_candle = pyupbit.get_ohlcv("KRW-BTC", interval="minute240")

print(get_RSI(day_candle, 14, -1))
# RSI_today
# get_RSI(day_candle, 14).iloc[-1]

# ---------------------------------------------------------
rsi_14 = get_RSI(day_candle, 14)

print("---------------btc bot working-----------------")

if rsi_14 <= 30:
    print(upbit.buy_market_order("KRW-BTC", 5000))

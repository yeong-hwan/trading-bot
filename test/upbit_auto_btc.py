# ---------------- library -------------------------
import pyupbit
import time
import pandas as pd

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

# Relative Strength Index


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

# Moving Average


def get_MA(ohclv, period, standard_date):
    close = ohclv["close"]
    ma = close.rolling(period).mean()
    return float(ma[standard_date])


# ---------------------- variables --------------------------
day_candle = pyupbit.get_ohlcv("KRW-BTC", interval="day")
minute_240_candle = pyupbit.get_ohlcv("KRW-BTC", interval="minute240")

rsi_14_today = get_RSI(minute_240_candle, 14, -1)
rsi_14_yesterday = get_RSI(minute_240_candle, 14, -2)

ma_5_before_2 = get_MA(day_candle, 5, -3)
ma_5_before = get_MA(day_candle, 5, -2)
ma_5_now = get_MA(day_candle, 5, -1)

ma_20_before_2 = get_MA(day_candle, 20, -3)
ma_20_before = get_MA(day_candle, 20, -2)
ma_20_now = get_MA(day_candle, 20, -1)

# ------------------- working part ----------------------------
print("--------------- BTC BOT WORKING ---------------")
print("--------------- MA CHECK ---------------")
print(
    f"ma_5_before_2: {ma_5_before_2}\nma_5_before: {ma_5_before}\nma_5_now: {ma_5_now}")


print("----------------------------------------")

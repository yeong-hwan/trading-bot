import pyupbit
import time

access = "JW7G0hr9xnBWpejlquZkEW78db0GXX1ROrPgK6ws"
secret = "tWLOFowynAXsT5UitsM4tPPuL1uIxrMNtYThIDZj"
upbit = pyupbit.Upbit(access, secret)

# --------------------------------------------------

tickers = pyupbit.get_tickers("KRW")

for ticker in tickers:
    if ticker == "KRW-BTC":
        day_candle = pyupbit.get_ohlcv(ticker, interval="day")
        # min_candle = pyupbit.get_ohlcv(ticker, interval="minute1")
        print(day_candle)
        break

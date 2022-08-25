# -------- libraries ---------
import ccxt
import time
import pprint
import json
# -------- import key & functions & alert ---------
import encrypt_key
import original_key
import bf
import line_alert
import traceback
import schedule


# ---------- key decoding ---------------
simple_en_decrypt = original_key.simple_en_decrypt(encrypt_key.encrypt_key)
binance_access = simple_en_decrypt.decrypt(original_key.access)
binance_secret = simple_en_decrypt.decrypt(original_key.secret)

binance = ccxt.binance(config={
    'apiKey': binance_access,
    'secret': binance_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

balance = binance.fetch_balance(params={"type": "future"})

tickers = binance.fetch_tickers()

up_trend_1, down_trend_1 = 0, 0
up_trend_2, down_trend_2 = 0, 0


# ------------------ build supertrend cloud ----------------
multi_5m_1, period_5m_1, multi_5m_2, period_5m_2 = 10, 6, 6, 10
multi_4h_1, period_4h_1, multi_4h_2, period_4h_2 = 3, 10, 6, 10


def run_bot(binance):
    target_coin_ticker = "SOL/USDT"

    candle = bf.get_ohlcv(
        binance, target_coin_ticker, '5m')

    candle_close_series = candle['close']
    candle_close_current = candle_close_series[-1]

    supertrend_line_1, trend_1, up_trend_1, down_trend_1 = bf.get_supertrend(
        candle, period_5m_1, multi_5m_1, up_trend_1, down_trend_1)

    supertrend_line_2, trend_2, up_trend_2, down_trend_2 = bf.get_supertrend(
        candle, period_5m_2, multi_5m_2, up_trend_2, down_trend_2)

    print("-----------------------------------------------")
    long_condition = bf.cross_over(candle_close_series, supertrend_line_1) \
        and candle_close_current > supertrend_line_2 \
        or bf.cross_over(candle_close_series, supertrend_line_2) \
        and candle_close_current > supertrend_line_1

    short_condition = bf.cross_under(candle_close_series, supertrend_line_1) \
        and candle_close_current < supertrend_line_2 \
        or bf.cross_under(candle_close_series, supertrend_line_2) \
        and candle_close_current < supertrend_line_1

    cloud_condition = bf.cross_under(candle_close_series, supertrend_line_1) \
        and candle_close_current > supertrend_line_2 \
        or bf.cross_over(candle_close_series, supertrend_line_1) \
        and candle_close_current < supertrend_line_2 \
        or bf.cross_under(candle_close_series, supertrend_line_2) \
        and candle_close_current > supertrend_line_1 \
        or bf.cross_over(candle_close_series, supertrend_line_2) \
        and candle_close_current < supertrend_line_2

    print(long_condition, short_condition, cloud_condition)

    in_long, in_short = False, False

    if long_condition:
        in_long = True
    else:
        if short_condition:
            in_long = False

    if short_condition:
        in_short = True
    else:
        if long_condition:
            in_short = False
            
    print(f"Long : {long_condition}\nShort : {short_condition}")


try:
    schedule.every(5).seconds.do(run_bot, binance)
    # schedule.every(10).seconds.do(hello)

    while True:

        schedule.run_pending()
        time.sleep(1)

except Exception as e:
    line_alert.send_message(str(e))

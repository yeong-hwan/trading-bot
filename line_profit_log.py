# -------- libraries ---------
import ccxt
import time
import json
# -------- import key & functions & alert ---------
import encrypt_key
import original_key
import bf
import line_alert


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

# ------------------ setting options ----------------------
time.sleep(0.1)

# -------------- time monitor ---------------------

# # if want to execute bot, server time = set time - 9
time_info = time.gmtime()
hour_server = time_info.tm_hour
minute = time_info.tm_min

mid_day_server = "AM"
if hour_server >= 12:
    hour_server -= 12
    mid_day_server = "PM"

hour_kst = hour_server + 9

mid_day_kst = mid_day_server
if hour_kst >= 12:
    hour_kst -= 12
    if mid_day_server == "PM":
        mid_day_kst = "AM"
    else:
        mid_day_kst = "PM"

year = time_info.tm_year
month = time_info.tm_mon
day = time_info.tm_mday

# ---------------------------------------------------

exchange_rate = bf.get_usd_krw()
total_money_usd = round(float(balance['USDT']['total']), 3)
total_money_krw = round(total_money_usd * exchange_rate, 3)
used_money = float(balance['USDT']['used'])
free_money = float(balance['USDT']['free'])

total_usd = format(total_money_usd, ',')
total_krw = format(total_money_krw, ',')


try:

    json_info = f"\n{year}.{month}.{day}\nUSD : {total_usd} $\nKRW : {total_krw} ₩\n"

    profit_log_list = list()

    # server
    profit_log_file_path = "/var/trading-bot/profit_log.json"

    # local
    # profit_log_file_path = "profit_log.json"

    try:
        with open(profit_log_file_path, 'r') as json_file:
            profit_log_list = json.load(json_file)

    except Exception as e:
        print(f"Exception: {e}")

    profit_log_list.append(json_info)

    if len(profit_log_list) > 7:
        profit_log_list.pop(0)

    with open(profit_log_file_path, 'w') as json_file:
        json.dump(profit_log_list, json_file)

    line_profit_message = ""
    for log in profit_log_list:
        line_profit_message += log

    line_alert.send_message(line_profit_message)


except Exception as e:
    line_alert.send_message(f"\n\nException: {e}")

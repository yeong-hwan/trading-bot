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
invest_rate = 0.2
coin_cnt = 5

message_status = ""

print("---------------------------------------------")
message_status += "\n\n--------------------------------------\n"

# ------------------ setting options ----------------------
set_leverage = 3

time.sleep(0.1)

# -------------- time monitor ---------------------
# print(time_info)

# if want to execute bot, server time = set time - 9
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

print("---------------------------------------------\n|")
message_status += "--------------------------------------\n"

print(f"| Server time | {hour_server} {mid_day_server} : {minute}")
print(f"| KST (UTC+9) | {hour_kst} {mid_day_kst} : {minute}\n|")
message_status += f"|\n| Server time | {hour_server} {mid_day_server} : {minute}\n"
message_status += f"| KST (UTC+9) | {hour_kst} {mid_day_kst} : {minute}\n|\n"

print("| -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n|")
message_status += "| -  -  -  -  -  -  -  -  -  -  -  -  -  -\n|\n"

exchange_rate = bf.get_usd_krw()
total_money_usd = float(balance['USDT']['total'])
total_money_krw = total_money_usd * exchange_rate
used_money = float(balance['USDT']['used'])
free_money = float(balance['USDT']['free'])
total_usd = format(total_money_usd, ',')
total_krw = format(total_money_krw, ',')

print("| Total USD :", total_usd, "$")
print("| Total KRW :", total_krw, "₩")
print("| Exchange Rate :", exchange_rate, "$")
print("| Positioned :", used_money, "$")
print("| Remainder :", free_money, "$", "\n|")


print("| -  -  -  -  -  -  -  -  -  -  -  -  -  -  -\n|")
message_status += "| -  -  -  -  -  -  -  -  -  -  -  -  -  -\n|\n"

print("| Leverage :", set_leverage, "\n|")
message_status += f"| Leverage : {set_leverage}\n|\n"

print("---------------------------------------------\n")
message_status += "--------------------------------------\n"

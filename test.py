# -------- libraries ---------
import ccxt
import time
import pprint
import json
from datetime import datetime
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

message_status = ""

balance = binance.fetch_balance(params={"type": "future"})
tickers = binance.fetch_tickers()


# ----------------- json control ---------------------
positioned_list = list()

positioned_file_path = "test.json"

try:
    with open(positioned_file_path, 'r') as json_file:
        positioned_list = json.load(json_file)

except Exception as e:
    print("| Exception by First | Not Positioned")

    message_status += "\n| Exception by First | Not Positioned\n\n"


#
#

# ------------------ setting options ----------------------
invest_rate = 0.3
coin_cnt = 5

set_leverage = 3
top_coin_list = bf.get_top_coin_list(binance, coin_cnt)

time.sleep(0.1)
# ---------------------------------------------------------

#
#
#

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

#
#
#

# ------------------ supertrend cloud ----------------
ticker_order = 1
message_info = ""

for ticker in tickers:
    if "/USDT" in ticker:
        if bf.check_coin_in_list(positioned_list, ticker) == True or bf.check_coin_in_list(top_coin_list, ticker) == True:
            time.sleep(0.2)

            target_coin_ticker = ticker
            message_ticker = ""

            print(positioned_list)

            ticker_data = (ticker, "5m", 5, 0, coin_price)
            positioned_list.append(ticker_data)
            #
            with open(positioned_file_path, 'w') as outfile:
                json.dump(positioned_list, outfile)

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

# ----------------- json control ---------------------
positioned_list = list()

# server
# positioned_file_path = "/var/trading-bot/positioned_list.json"

# local
positioned_file_path = "positioned_list.json"

# ----------------------------------------------------
try:
    with open(positioned_file_path, 'r') as json_file:
        positioned_list = json.load(json_file)

except Exception as e:
    # line_alert.send_message("| Exception by First | Not Positioned")
    print("\n| Exception by First | Not Positioned\n")

# ---------------------------------------------------

time.sleep(0.1)

print("\n┍--------------------------------------------\n|")


exchange_rate = bf.get_usd_krw()
total_money_usd = float(balance['USDT']['total'])
total_money_krw = total_money_usd * exchange_rate
used_money = float(balance['USDT']['used'])
free_money = float(balance['USDT']['free'])
total_usd = format(total_money_usd, ',')
total_krw = format(total_money_krw, ',')

print("| Total USD :", total_usd, "$")
print("| Total KRW :", total_krw, "₩")
print("| Exchange Rate(1$) :", exchange_rate, "₩")
print("| Positioned :", used_money, "$")
print("| Remainder :", free_money, "$", "\n|")


print("┕--------------------------------------------\n")

print("[ Top Coin List ]")
print("|", "\n| ".join(bf.get_top_coin_list(binance, 10)), "\n")

print("[ Positioned List ]")
idx = 1
for position_data in positioned_list:
    ticker_name, position_side = position_data[0], position_data[2]
    if position_side == "long":
        position_side = "L"
    else:
        position_side = "S"
    print(f"{idx}. [{position_side}] | {ticker_name[:-5]}")
    idx += 1
print("")

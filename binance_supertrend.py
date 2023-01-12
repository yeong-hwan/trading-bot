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


# binance.verbose = True
balance = binance.fetch_balance(params={"type": "future"})
tickers = binance.fetch_tickers()


# ----------------- json control ---------------------
positioned_list = list()

# server
positioned_file_path = "/var/trading-bot/positioned_list.json"

# local
# positioned_file_path = "positioned_list.json"


try:
    with open(positioned_file_path, 'r') as json_file:
        positioned_list = json.load(json_file)

except Exception as e:
    line_alert.send_message("| Exception by First | Not Positioned")
    print("| Exception by First | Not Positioned")

# line_alert.send_message("supertrend working")

try:
    #
    #
    # ------------------ setting options ----------------------
    invest_rate = 1
    set_leverage = 5

    coin_cnt = 10
    top_coin_list = bf.get_top_coin_list(binance, coin_cnt)

    target_coin_list = top_coin_list
    for positioned_ticker in positioned_list:
        if positioned_ticker not in target_coin_list:
            target_coin_list.append(positioned_ticker)

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
    # time monitor not used
    #

    # ------------------ banned ticker list --------------
    banned_ticker_list = ["SRM/USDT", "FTT/USDT"]

    # ------------------ supertrend cloud ----------------
    ticker_order = 1
    report_message = ""

    for ticker in target_coin_list:

        if "/USDT" in ticker:

            long_5m, short_5m, cloud_5m = False, False, False
            long_4h, short_4h, cloud_4h = False, False, False

            supertrend_line_1_5m, supertrend_line_2_5m = 0, 0
            supertrend_line_1_4h, supertrend_line_2_4h = 0, 0

            candle_5m = bf.get_ohlcv(
                binance, ticker, '5m')
            time.sleep(0.02)

            candle_4h = bf.get_ohlcv(
                binance, ticker, '4h')
            time.sleep(0.02)

        # get supertrend cloud
        # continue skip current ticker

            # exception for banned_ticker_list
            if ticker in banned_ticker_list:
                continue

            elif ticker == "BTC/USDT":
                # continue
                long_5m, short_5m, cloud_5m, supertrend_line_1_5m, supertrend_line_2_5m, state = bf.get_supertrend_cloud(
                    candle_5m, '5m', True)
                # long_4h, short_4h, cloud_4h, supertrend_line_1_4h, supertrend_line_2_4h, status = bf.get_supertrend_cloud(
                #     candle_4h, '4h', True)

            else:
                # if ticker == "SOL/USDT":
                long_5m, short_5m, cloud_5m, supertrend_line_1_5m, supertrend_line_2_5m, state = bf.get_supertrend_cloud(
                    candle_5m, '5m')

                # long_4h, short_4h, cloud_4h, supertrend_line_1_4h, supertrend_line_2_4h = bf.get_supertrend_cloud(
                #     candle_4h, '4h')
                # else:
                #     continue

            # --------------
            boolean_list = [long_5m, short_5m,
                            cloud_5m, long_4h, short_4h, cloud_4h]

            if True in boolean_list:
                line_alert.send_message(f"{ticker} | {boolean_list[:3]}")

            # --------------

# ----------------------------------------------

            if bf.check_coin_in_list(target_coin_list, ticker) == True:
                time.sleep(0.3)

                target_coin_ticker = ticker
                message_ticker = ""

                print(f"{ticker_order}.")
                print("-------", "target_coin_ticker :",
                      target_coin_ticker, "-------\n|")

                target_coin_symbol = ticker.replace("/", "")
                time.sleep(0.05)

                minimum_amount_tuple = bf.get_min_amount(
                    binance, target_coin_ticker)

                minimum_cost = minimum_amount_tuple[0]
                minimum_amount = minimum_amount_tuple[1]

                leverage = 0

                coin_price = bf.get_coin_current_price(
                    binance, target_coin_ticker)
                max_amount = 0

                try:
                    max_amount = float(binance.amount_to_precision(target_coin_ticker, bf.get_amount(
                        float(balance['USDT']['total']), coin_price, invest_rate / coin_cnt))) * set_leverage
                # adjust max_amount when 0
                except Exception as e:
                    pass
                if max_amount == 0:
                    max_amount = minimum_amount * 5

                total_money_usd = float(balance['USDT']['total'])
                budget_for_current_ticker = total_money_usd / 10

                cost_to_amt_ratio = budget_for_current_ticker / minimum_cost
                invest_ratio = cost_to_amt_ratio * set_leverage

                expected_budget = minimum_cost * invest_ratio
                buy_amount = minimum_amount * invest_ratio

                # round amounts
                minimum_amount = round(minimum_amount, 5)
                # max_amount = round(max_amount, 5)
                expected_budget = round(expected_budget, 5)
                buy_amount = round(buy_amount, 5)

                print(f"| min_amount : {minimum_amount} EA")
                # print(f"| max_amount : {max_amount} EA")
                print(f"| expected_budget : {expected_budget} $")
                print(f"| buy_amount : {buy_amount} EA")

                amt_long, amt_short = 0, 0
                entry_price_long, entry_price_short = 0, 0

                isolated = True

                # short position setting
                for position in balance['info']['positions']:
                    if position['symbol'] == target_coin_symbol and position['positionSide'] == 'SHORT':
                        amt_short = float(position["positionAmt"])
                        entry_price_short = float(position['entryPrice'])
                        leverage = float(position['leverage'])
                        isolated = position['isolated']
                        break

                # long position setting
                for position in balance['info']['positions']:
                    if position['symbol'] == target_coin_symbol and position['positionSide'] == 'LONG':
                        amt_long = float(position["positionAmt"])
                        entry_price_long = float(position['entryPrice'])
                        leverage = float(position['leverage'])
                        isolated = position['isolated']
                        break

                # --------- leverage & isloate setting -----------
                if leverage != set_leverage:
                    print(binance.fapiPrivate_post_leverage(
                        {'symbol': target_coin_symbol, 'leverage': set_leverage}))

                    time.sleep(0.1)

                if isolated == False:
                    print(binance.fapiPrivate_post_margintype(
                        {'symbol': target_coin_symbol, 'marginType': 'ISOLATED'}))

                    time.sleep(0.1)

                if True:

                    # ---------------------------------------------------------

                    candle_close_current = candle_5m['close'][-3]

                    supertrend_line_1_5m, supertrend_line_2_5m = round(
                        supertrend_line_1_5m, 4), round(supertrend_line_2_5m, 4)
                    # supertrend_line_1_4h, supertrend_line_2_4h = round(
                    #     supertrend_line_1_4h, 4), round(supertrend_line_2_4h, 4)

                    report_message += f"\n{ticker_order}. {target_coin_ticker} Now : {candle_close_current}\n"
                    report_message += f"| 5m  St1 : {supertrend_line_1_5m} St2 : {supertrend_line_2_5m}\n"
                    # report_message += f"| 4h  St1 : {supertrend_line_1_4h} St2 : {supertrend_line_2_4h}\n"

                    report_message += f"| {state}"

# ----------------------- enter position -----------------------

                    # 5m
                    if long_5m:
                        line_alert.send_message(
                            f"{target_coin_ticker} 5m long position chance")

                        time.sleep(0.1)

                        params = {
                            'positionSide': 'LONG'
                        }
                        long_order = binance.create_market_buy_order(
                            target_coin_ticker, buy_amount, params)

                        time.sleep(0.1)

                        ticker_data = (ticker, "5m", "long",
                                       buy_amount, coin_price)

                        positioned_list.append(ticker_data)

                        with open(positioned_file_path, 'w') as outfile:
                            json.dump(positioned_list, outfile)

                    elif short_5m:
                        line_alert.send_message(
                            f"{target_coin_ticker} 5m short position chance")

                        time.sleep(0.1)

                        params = {
                            'positionSide': 'SHORT'
                        }
                        short_order = binance.create_market_sell_order(
                            target_coin_ticker, buy_amount, params)

                        time.sleep(0.1)

                        ticker_data = (ticker, "5m", "short",
                                       buy_amount, coin_price)

                        positioned_list.append(ticker_data)

                        with open(positioned_file_path, 'w') as outfile:
                            json.dump(positioned_list, outfile)

                    # 4h
                    if long_4h:
                        line_alert.send_message(
                            f"{target_coin_ticker} 4h long position chance")

                        params = {
                            'positionSide': 'LONG'
                        }
                        long_order = binance.create_market_buy_order(
                            target_coin_ticker, buy_amount, params)

                        time.sleep(0.1)

                        ticker_data = (ticker, "4h", "long",
                                       buy_amount, coin_price)

                        positioned_list.append(ticker_data)

                        with open(positioned_file_path, 'w') as outfile:
                            json.dump(positioned_list, outfile)

                    elif short_4h:
                        line_alert.send_message(
                            f"{target_coin_ticker} 4h short position chance")

                        params = {
                            'positionSide': 'SHORT'
                        }
                        short_order = binance.create_market_sell_order(
                            target_coin_ticker, buy_amount, params)

                        time.sleep(0.1)

                        ticker_data = (ticker, "4h", "short",
                                       buy_amount, coin_price)

                        positioned_list.append(ticker_data)

                        with open(positioned_file_path, 'w') as outfile:
                            json.dump(positioned_list, outfile)

# -----------------------------------------------------------------
                    ticker_name = ""

                    candle_period_5m = ""
                    position_side_5m = ""
                    positioned_amt_5m = 0
                    positioned_coin_price_5m = 0

                    candle_period_4h = ""
                    position_side_4h = ""
                    positioned_amt_4h = 0
                    positioned_coin_price_4h = 0

                    for position_data in positioned_list:
                        ticker_name = position_data[0]
                        candle_data = position_data[1]
                        position_side_data = position_data[2]
                        buy_amt_data = position_data[3]
                        coin_price_data = position_data[4]

                        if ticker_name == ticker and candle_data == "5m":
                            candle_period_5m = candle_data
                            position_side_5m = position_side_data
                            positioned_amt_5m = buy_amt_data
                            positioned_coin_price_5m = coin_price_data

                        if ticker_name == ticker and candle_data == "4h":
                            candle_period_4h = candle_data
                            position_side_4h = position_side_data
                            positioned_amt_4h = buy_amt_data
                            positioned_coin_price_4h = coin_price_data

                        ticker_data_5m = (
                            candle_period_5m, position_side_5m, positioned_amt_5m, positioned_coin_price_5m)
# -----------------------------------------------------------------

#
#
#

# -----------------------  exit position -----------------------
                        # 5m
                        if (cloud_5m and ticker_name == target_coin_ticker):
                            line_alert.send_message(
                                f"{target_coin_ticker} 5m close position")

                            line_alert.send_message(
                                f"{ticker_data_5m}")

                            if position_side_5m == "long":
                                params = {
                                    'positionSide': 'LONG'
                                }
                                close_long = binance.create_market_sell_order(
                                    target_coin_ticker, positioned_amt_5m, params)

                                line_alert.send_message(
                                    f"\nclose_long\n{close_long}")

                            if position_side_5m == "short":
                                params = {
                                    'positionSide': 'SHORT'
                                }
                                close_short = binance.create_market_buy_order(
                                    target_coin_ticker, positioned_amt_5m, params)
                                line_alert.send_message(
                                    f"\nclose_short\n{close_short}")

                            positioned_list.remove(position_data)

                            with open(positioned_file_path, 'w') as outfile:
                                json.dump(positioned_list, outfile)

                        # 4h
                        if cloud_4h:
                            line_alert.send_message(
                                f"{target_coin_ticker} 4h close position")

                            if position_side_4h == "long":
                                params = {
                                    'positionSide': 'LONG'
                                }
                                binance.create_market_sell_order(
                                    target_coin_ticker, positioned_amt_4h, params)

                            if position_side_4h == "short":
                                params = {
                                    'positionSide': 'SHORT'
                                }
                                binance.create_market_buy_order(
                                    target_coin_ticker, positioned_amt_4h, params)

                            positioned_list.remove(position_data)

                            with open(positioned_file_path, 'w') as outfile:
                                json.dump(positioned_list, outfile)

            print("--------------------------------------------\n\n")

            ticker_order += 1

    line_alert.send_message(report_message)


except Exception as e:
    print("Exception :", e)
    line_alert.send_message("Exception : " + str(e))
    line_alert.send_message(traceback.format_exc())

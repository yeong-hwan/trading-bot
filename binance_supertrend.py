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

# server
positioned_file_path = "/var/trading-bot/positioned_list.json"

# local
# positioned_file_path = "positioned_list.json"


try:
    with open(positioned_file_path, 'r') as json_file:
        positioned_list = json.load(json_file)

except Exception as e:
    print("| Exception by First | Not Positioned")

    message_status += "\n| Exception by First | Not Positioned\n\n"

try:
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

                print(f"{ticker_order}.")
                print("-------", "target_coin_ticker :",
                      target_coin_ticker, "-------\n|")

                target_coin_symbol = ticker.replace("/", "")
                time.sleep(0.05)

                get_min_amount_tuple = bf.get_min_amount(
                    binance, target_coin_ticker)

                minimum_amount = get_min_amount_tuple[0]
                message_ticker += get_min_amount_tuple[1]

                leverage = 0

                coin_price = bf.get_coin_current_price(
                    binance, target_coin_ticker)

                max_amount = float(binance.amount_to_precision(target_coin_ticker, bf.get_amount(
                    float(balance['USDT']['total']), coin_price, invest_rate / coin_cnt))) * set_leverage

                # adjust max_amount when 0
                if max_amount == 0:
                    max_amount = minimum_amount * 5

                buy_amount = max_amount / 10

                buy_amount = float(binance.amount_to_precision(
                    target_coin_ticker, buy_amount))

                # round amounts
                buy_amount = round(buy_amount, 5)
                minimum_amount = round(minimum_amount, 5)
                max_amount = round(max_amount, 5)

                if buy_amount < minimum_amount:
                    buy_amount = minimum_amount

                print(f"| min_amount : {minimum_amount} EA")
                print(f"| max_amount : {max_amount} EA")
                print(f"| buy_amount : {buy_amount} EA")

                amt_long, amt_short = 0, 0
                entry_price_long, entry_price_short = 0, 0

                isolated = True

                # short position
                for position in balance['info']['positions']:
                    if position['symbol'] == target_coin_symbol and position['positionSide'] == 'SHORT':
                        amt_short = float(position["positionAmt"])
                        entry_price_short = float(position['entryPrice'])
                        leverage = float(position['leverage'])
                        isolated = position['isolated']
                        break

                # long position
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

                if isolated == False:
                    print(binance.fapiPrivate_post_margintype(
                        {'symbol': target_coin_symbol, 'marginType': 'ISOLATED'}))

                # positioned case
                if bf.check_coin_in_list(positioned_list, ticker) == True:

                    line_alert.send_message(
                        f"\n\n{ticker_order}.\n| {ticker}\n| pass by positioned")

                    # message_info += f"\n\n{ticker_order}.\n| {target_coin_ticker}\n| pass by break through listed"

                    # no position
                    # if abs(amt_short) == 0 and abs(amt_long) == 0:
                    #     # binance.cancel_all_orders(target_coin_ticker)
                    #     time.sleep(0.1)

                    #     # positioned_list.remove()

                    #     with open(positioned_file_path, 'w') as outfile:
                    #         json.dump(positioned_list, outfile)

                    #
                    #
                    #

                    # not positioned
                else:
                    # logic period: 1m
                    if minute & 1 == 0:
                        long_5m, short_5m, cloud_5m = False, False, False
                        long_4h, short_4h, cloud_4h = False, False, False

                        candle_5m = bf.get_ohlcv(
                            binance, target_coin_ticker, '5m')

                        time.sleep(0.2)

                        candle_4h = bf.get_ohlcv(
                            binance, target_coin_ticker, '4h')
                        time.sleep(0.2)

                        # get supertrend cloud
                        if ticker == "BTC/USDT":
                            long_5m, short_5m, cloud_5m = bf.get_supertrend_cloud(
                                candle_5m, '5m', True)
                            long_4h, short_4h, cloud_4h = bf.get_supertrend_cloud(
                                candle_4h, '4h', True)

                        else:
                            long_5m, short_5m, cloud_5m = bf.get_supertrend_cloud(
                                candle_5m, '5m')
                            long_4h, short_4h, cloud_4h = bf.get_supertrend_cloud(
                                candle_4h, '4h')

    # ---------------------------------------------------------

    # ---------------------------------------------------------

                        print("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -")
                        print("| 5m")
                        print(
                            f"| Long : {long_4h}\n| Short : {short_4h}\n| Cloud : {cloud_4h}")
                        print("-  -  -  -  -  -  -  -  -  -  -  -  -  -  -  -")
                        print("| 4h")
                        print(
                            f"| Long : {long_4h}\n| Short : {short_4h}\n| Cloud : {cloud_4h}")

                        orders = binance.fetch_orders(ticker)

    # ----------------------- enter position -----------------------

                        # 5m
                        if long_5m:
                            line_alert.send_message(
                                f"{target_coin_ticker} 5m long position chance")

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
                                positioned_coin_price_5m = coin_price_data

    # -----------------------------------------------------------------

    #
    #
    #

    # -----------------------  exit position -----------------------
                            # 5m
                            if cloud_5m:
                                line_alert.send_message(
                                    f"{target_coin_ticker} 5m close position")

                                if position_side_5m == "long":
                                    params = {
                                        'positionSide': 'LONG'
                                    }
                                    binance.create_market_sell_order(
                                        target_coin_ticker, positioned_amt_5m, params)

                                if position_side_5m == "short":
                                    params = {
                                        'positionSide': 'SHORT'
                                    }
                                    binance.create_market_buy_order(
                                        target_coin_ticker, positioned_amt_5m, params)

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
                message_ticker += "--------------------------------------\n"

                ticker_order += 1

except Exception as e:
    print("Exception :", e)
    line_alert.send_message("Exception : " + str(e))
    line_alert.send_message(traceback.format_exc())


# def run_bot(binance):
#     print(f"\n\nFetching new bars for {datetime.now().isoformat()}")

#     long_condition, short_condition, cloud_condition = bf.get_supertrend_cloud(
#         candle, '5m')

#     print(
#         f"Long : {long_condition}\nShort : {short_condition}\nCloud : {cloud_condition}")


# try:
#     schedule.every(10).seconds.do(run_bot, binance)
#     # schedule.every(10).seconds.do(hello)

#     while True:

#         schedule.run_pending()
#         time.sleep(1)

# except Exception as e:
#     line_alert.send_message(str(e))

import ccxt
import time
import pandas as pd
import pprint

access = "Zd2awwadeB2BFrxvs3tLQixrpVtkM8PfvvCVZAHeaF1RSYWckSOdUfJvwt6elXeF"
secret = "9pumuiCRihNdUTY7BO2d0sRZrBaeII7oERqNe7kDpqKoL9pVDVLQlMSsLFqZ4CGb"

binance = ccxt.binance(config={
    'apiKey': access,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

target_coin_ticker = "BTC/USDT"
target_coin_symbol = "BTCUSDT"

btc = binance.fetch_ticker(target_coin_ticker)
btc_price = btc['close']

pprint.pprint(btc)


# taker_short
# binance.create_market_sell_order(target_coin_ticker, 0.001)

# taker_long
# binance.create_market_buy_order(target_coin_ticker, 0.001)

# maker_short
# binance.create_limit_sell_order(target_coin_ticker, 0.001, btc_price)

balance = binance.fetch_balance(params={"type": "future"})
pprint.pprint(balance)
print(balance['USDT'])

for position in balance['info']['positions']:
    if position['symbol'] == target_coin_symbol:
        leverage = float(position['leverage'])
        entry_price = float(position['entryPrice'])
        unrealized_profit = float(position['unrealizedProfit'])
        amt = float(position['positionAmt'])

'''
entry_price: average buy price
amt: amount of position
'''

print("amt:", amt)
print("entry_price:", entry_price)
print("leverage:", leverage)
print("unrealized_profit:", unrealized_profit)

# short to long (sell position)
abs_amt = abs(amt)

# long sell
entry_price_long = entry_price * 1.001
# short sell
entry_price_short = entry_price * 0.999
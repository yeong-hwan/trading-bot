import ccxt
import time
import pandas as pd
import pprint

access = "UGZCnsSs7qGO57JbAnBaEECKp6Te1paWsdSk3tnGkbP04ZQLokQOvKsF9Ls23TR1"
secret = "2sVI8v2N2j0E4yoQZWkIVmzpopWNHxxYbx0yI9XqaVpIGMZKPsvtNMwjSPIot9ad"

binance = ccxt.binance(config={
    'apikey': access,
    'secret': secret,
    'enable_rate_limit': True,
    'options': {
        'default_type': 'future'
    }
})

target_coin_ticker = "BTC/USDT"
btc = binance.fetch_ticker(target_coin_ticker)
pprint.pprint(btc)

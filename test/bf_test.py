import bf

candle_close_series = [10, 1]

line = 5

print(bf.cross_over(candle_close_series, line))
print(bf.cross_under(candle_close_series, line))

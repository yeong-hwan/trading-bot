import bf

candle_close_series = [10, 1]

line = 5

print(bf.get_cross_over(candle_close_series, line))
print(bf.get_cross_under(candle_close_series, line))


# def detect_hammer_patterns( open, high, low, close):
#     signal = ''
#     body_range = abs(open - close)
#     total_range = high - low
#
#     if body_range < total_range * 0.3:
#         if open > close and ((close - low) / total_range > 0.6):  # and ((close - low) / total_range < 0.2):
#             signal = 'LONG'
#         elif open > close and ((high - open) / total_range > 0.6):  # and ((high - open) / total_range < 0.2):
#             signal = 'SHORT'
#     return signal


def detect_hammer_patterns(open, high, low, close, timeframe):
    signal = ''
    body_range = abs(open - close)
    total_range = high - low
    shadow_limit = 0.01  # 1 procent by default
    shadow_rate = 1
    if timeframe == '4h':
        shadow_limit = 0.02
    elif timeframe == "1d":
        shadow_limit = 0.02
    elif timeframe == "1m":
        shadow_limit = 0.003

    if body_range * 3 < total_range:

        if open > close:
            # red hummers
            if ((close - low) / total_range > 0.6) and (
                    close - low > shadow_limit * open) and (
                    (close - low) / (high - open) >= 3):  # and ((close - low) / total_range < 0.2):
                signal = 'LONG'
            elif ((high - open) / total_range > 0.6) and (
                    high - open > shadow_limit * open) and (
                    (high - open) / (close - low) >= 3):  # and ((high - open) / total_range < 0.2):
                signal = 'SHORT'

        else:
            # green hummers
            if ((open - low) / total_range > 0.6) and (open - low > shadow_limit * open) \
                    and ((open - low) / (high - close) >= 3):
                signal = 'LONG'
            elif ((high - close) / total_range > 0.6) and (
                    high - close > shadow_limit * open) and (
                    (high - close) / (open - low) >= 3):  # and ((high - open) / total_range < 0.2):
                signal = 'SHORT'

    return signal



signal = detect_hammer_patterns(open=0.00890 ,high=0.00966 ,low=0.00878, close=0.00886, timeframe="4h")
print(signal)

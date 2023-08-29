
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




def detect_hammer_patterns2(open, high, low, close, timeframe):
    signal = ''
    body_range = abs(open - close)
    total_range = high - low
    shadow_limit = 0.01  # 1 procent by default
    shadow_rate = 1
    if timeframe == '4h':
        shadow_limit = 0.01
    elif timeframe == "1d":
        shadow_limit = 0.02
    elif timeframe == "1m":
        shadow_limit = 0.003

    try:

        if body_range * 3 < total_range:

            # ---------float zero division error correction
            if high == open:
                high = open + 0.001 * open
            elif close == low:
                low = close - close * 0.001
            elif high == close:
                high = close + close * 0.001
            elif open == low:
                low = open - open * 0.001
            # ---------------------------------------------

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
    except Exception as e:
        print(f"detect_hammer_patterns error: {e}")
    return signal


def detect_hammer_patterns(open, high, low, close, timeframe):
    signal = ''
    body_range = abs(open - close)
    total_range = high - low
    shadow_limit = 0.01  # 1 procent by default
    shadow_rate = 1
    if timeframe == '4h':
        shadow_limit = 0.01
    elif timeframe == "1d":
        shadow_limit = 0.02
    elif timeframe == "1m":
        shadow_limit = 0.003

    try:

        if body_range * 3 < total_range:

            # ---------float zero division error correction
            if high == open:
                high = open + 0.001 * open
            elif close == low:
                low = close - close * 0.001
            elif high == close:
                high = close + close * 0.001
            elif open == low:
                low = open - open * 0.001
            # ---------------------------------------------

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
    except Exception as e:
        print(e)
    return signal



signal = detect_hammer_patterns2(open=0.03915 ,high=0.03947 ,low=0.03858, close=0.03886, timeframe="4h")
print(signal)

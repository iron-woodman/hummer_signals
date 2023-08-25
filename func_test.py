

def detect_hammer_patterns( open, high, low, close):
    signal = ''
    body_range = abs(open - close)
    total_range = high - low

    if body_range < total_range * 0.3:
        if open > close and ((close - low) / total_range > 0.6):  # and ((close - low) / total_range < 0.2):
            signal = 'LONG'
        elif open > close and ((high - open) / total_range > 0.6):  # and ((high - open) / total_range < 0.2):
            signal = 'SHORT'
    return signal




detect_hammer_patterns(0.001300, 0.001417, 0.001271, 0.001299)
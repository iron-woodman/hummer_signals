import pandas as pd

def detect_hammer_patterns(data):
    signals = []

    for i in range(1, len(data)):
        open_price = data['Open'][i]
        close_price = data['Close'][i]
        high_price = data['High'][i]
        low_price = data['Low'][i]

        body_range = abs(open_price - close_price)
        total_range = high_price - low_price

        if body_range < total_range * 0.3:
            if close_price > open_price and (close_price - low_price) / total_range > 0.6:
                signals.append((data.index[i], 'Bull Hammer'))
            elif open_price > close_price and (open_price - low_price) / total_range > 0.6:
                signals.append((data.index[i], 'Bear Hammer'))

    return signals

# Example historical price data (replace this with your own dataset)
data = pd.DataFrame({
    'Open': [100, 105, 110, 115, 120, 125],
    'Close': [105, 108, 114, 118, 119, 124],
    'High': [107, 109, 115, 119, 121, 126],
    'Low': [98, 103, 108, 112, 116, 121]
}, index=pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06']))

hammer_signals = detect_hammer_patterns(data)
for date, pattern in hammer_signals:
    print(f"{pattern} pattern detected on {date.date()}")

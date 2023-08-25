## -*- coding: utf-8 -*-

class TLGMessage:
    def __init__(self, pair, timeframe, direction, bar_rate, volume_rate=None):
        self.pair = pair
        self.timeframe = timeframe
        if timeframe == '4h' or timeframe == '1d':
            self.timeframe = f'*{timeframe}*'# выделяем старшие ТФ жирным
        self.direction = direction
        self.bar_rate = bar_rate
        self.volume_rate = volume_rate

    def generate_message(self):
        try:
            direction = "Long" if self.direction == "LONG" else "Short"
            message = (
                f"Pair: {self.pair} \n"
                f"Timeframe: {self.timeframe}\n"
                f"Direction: {direction}\n"
                f"Size:{self.bar_rate}\n"

            )
            if self.volume_rate is not None:
                message += f"Vol: x {self.volume_rate}"

            return message
        except Exception as e:
            print(e)
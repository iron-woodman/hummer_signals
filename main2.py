## -*- coding: utf-8 -*-
import logging
from time import sleep

import json
import os
import requests
from binance import Client, ThreadedWebsocketManager
import datetime

from telegram_message import TLGMessage
import logger as custom_logging

common_params = dict()  # основные параметры скрипта
avg_volumes = dict()  # средние объемы для разных ТФ
CH = logging.StreamHandler()
CH.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))

DEBUG = True  # флаг переключения режима скритпа debug/release


class QueueManager():
    _log = logging.getLogger(__name__)
    _log.setLevel(logging.INFO)
    _log.addHandler(CH)

    def __init__(self, symbols: list = [], timeframes: list = []) -> None:
        self._twm = ThreadedWebsocketManager()
        # self._streams = list(map(lambda s: f"{s.replace('/', '').lower()}@kline_{timeframe}", symbols))
        self._streams = []
        for symbol in symbols:
            for timeframe in timeframes:
                self._streams.append(f"{symbol.replace('/', '').lower()}@kline_{timeframe}")

        self.send_signal(f'Bot started. Coins count: {len(symbols)}. TF:{timeframes}')

        self._twm.start()
        self._log.warning(f"Start listening to {len(self._streams)} streams")
        self._listener: str = self._twm.start_multiplex_socket(callback=self._handle_socket_message,
                                                               streams=self._streams)

    def send_signal(self, signal):

        global common_params

        print("*" * 30 + "\n" + signal)
        self._log.info(signal)
        token = common_params["telegram_token"]
        url = "https://api.telegram.org/bot"
        channel_id = common_params["telegram_channel_id"]
        # channel_name = "signals555"
        url += token
        method = url + "/sendMessage"
        attemts_count = 5
        while (attemts_count > 0):
            r = requests.post(method, data={
                "chat_id": channel_id,
                "text": signal,
                "parse_mode": "Markdown"
            })
            if r.status_code == 200:
                return
            elif r.status_code != 200:
                print(f'Telegram send signal error ({signal}).')
                self._log.error(f'Telegram send signal error:\n ({signal}). \nAttempts count={attemts_count}')
                datetime.time.sleep(1)
                attemts_count -= 1

    def detect_hammer_patterns(self, open, high, low, close, timeframe):
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
                            close - low > shadow_limit * open) and ((close-low)/(high-open) >= 3):  # and ((close - low) / total_range < 0.2):
                        signal = 'LONG'
                    elif ((high - open) / total_range > 0.6) and (
                            high - open > shadow_limit * open) and ((high-open)/(close-low) >= 3):  # and ((high - open) / total_range < 0.2):
                        signal = 'SHORT'

                else:
                    # green hummers
                    if ((open - low) / total_range > 0.6) and (open - low > shadow_limit * open)\
                            and ((open-low)/(high-close) >=3):
                        signal = 'LONG'
                    elif ((high - close) / total_range > 0.6) and (
                            high - close > shadow_limit * open) and ((high-close)/(open-low) >=3):  # and ((high - open) / total_range < 0.2):
                        signal = 'SHORT'
        except Exception as e:
            self._log.error(f"detect_hammer_patterns error: {e}")
        return signal


    def get_candle_proportion(self, open_, high, low, close):
        if open_ == close:
            open_ = open_ + open_ * 0.0001
        proportion = round((high - low) / abs(open_ - close), 2)
        if proportion > 2 and proportion <= 2.5:
            return "1 to 2"
        elif proportion > 2.5 and proportion <= 3:
            return "1 to 3"
        elif proportion > 3 and proportion <= 3.5:
            return "1 to 3"
        elif proportion > 3.5 and proportion <= 4:
            return "1 to 4"
        elif proportion > 4 and proportion <= 4.5:
            return "1 to 4"
        elif proportion > 4.5 and proportion <= 5:
            return "1 to 5"
        elif proportion > 5 and proportion <= 5.5:
            return "1 to 5"
        elif proportion > 5.5 and proportion <= 6:
            return "1 to 6"
        elif proportion > 6 and proportion <= 6.5:
            return "1 to 6"
        elif proportion > 6.5 and proportion <= 7:
            return "1 to 7"
        elif proportion > 7 and proportion <= 7.5:
            return "1 to 7"
        elif proportion > 7.5 and proportion <= 8:
            return "1 to 8"
        elif proportion > 8 and proportion <= 8.5:
            return "1 to 8"
        elif proportion > 8.5 and proportion <= 9:
            return "1 to 9"
        elif proportion > 9 and proportion <= 9.5:
            return "1 to 9"
        elif proportion > 9.5 and proportion <= 10:
            return "1 to 10"
        elif proportion > 10 and proportion <= 10.5:
            return "1 to 10"
        else:
            return f"1 to {proportion}"

    def check_bar_for_signal(self, symbol, open_, high, low, close, volume, timeframe, candle_time):
        signal = ''
        try:
            hummer_direction = self.detect_hammer_patterns(open_, high, low, close, timeframe)
            proportion = self.get_candle_proportion(open_, high, low, close)
            volume_ratio = self.get_volume_ratio(volume, timeframe, symbol)
            if hummer_direction != '':
                tlg_message = TLGMessage(symbol, timeframe, hummer_direction, proportion, volume_ratio)
                signal = tlg_message.generate_message()

                # signal = f'{symbol}:{timeframe}:{hummer_direction}:{proportion}'
                # if volume_ratio is not None:
                #     signal += f'\nvolume: x {volume_ratio}'

        except Exception as e:
            print(e)
            self._log.error(f"check_bar_for_signal error: {e}.")
        return signal

    def _handle_socket_message(self, message):
        if ('e' in message):
            if (message['m'] == 'Queue overflow. Message not filled'):
                self._log.warning("Socket queue full. Resetting connection.")
                self.reset_socket()
                return
            else:
                self._log.error(f"Stream error: {message['m']}")
                exit(1)
        try:

            if 'stream' in message and 'data' in message:
                json_message = message['data']
                symbol = json_message['s']
                candle = json_message['k']
                is_candle_closed = candle[
                    'x']  # True -свеча сформировалась (закрыта), False - еще формируется (открыта)
                open_ = float(candle['o'])
                high = float(candle['h'])
                low = float(candle['l'])
                close = float(candle['c'])
                volume = float(candle['v'])
                timeframe = candle['i']
                candle_time = candle['t']

                if is_candle_closed:
                    signal = ''
                    signal = self.check_bar_for_signal(symbol, open_, high, low, close, volume, timeframe, candle_time)
                    if signal != '':
                        # print(signal)
                        self.send_signal(signal, candle_time)


        except Exception as e:
            print("on_message exception:", e)
            self._log.error("on_message exception:", e)
        # print(message)

        if False:
            # in case your internal logic invalidates the items in the queue
            # (e.g. your business logic ran too long and items in queue became "too old")
            reset_socket()

    def reset_socket(self):
        self._twm.stop_socket(self._listener)
        self._listener = self._twm.start_multiplex_socket(callback=self._handle_socket_message, streams=self._streams)
        if (self._log.isEnabledFor(logging.DEBUG)):
            self._log.debug("Reconnecting. Waiting for 5 seconds...")
            sleep(5)

    def join(self):
        self._twm.join()

    def get_volume_ratio(self, volume, timeframe, symbol):
        global avg_volumes
        avg_volume = 0.0
        ratio = 0.0
        if symbol in avg_volumes:
            if timeframe in avg_volumes[symbol]:
                avg_volume = avg_volumes[symbol][timeframe]
                ratio = round(volume / avg_volume, 1)
                return ratio
        else:
            self._log.warning(f"Avg volume not exists for {symbol}:{timeframe}.")


def load_futures_list():
    global common_params
    try:
        client = Client(common_params["API_Key"], common_params["Secret_Key"])
        futures_info_list = client.futures_exchange_info()
        futures = []
        for item in futures_info_list['symbols']:
            if item['status'] != 'TRADING': continue
            futures.append(item['pair'])
    except Exception as e:
        custom_logging.add_log(f"load_futures_luist exception: {e}", level=logging.ERROR)
    return futures


def load_common_params(file):
    if os.path.exists(file) is False:
        print(f'File {file} not exists.')
        custom_logging.add_log(f'File {file} not exists.', level=logging.WARNING)
        return None

    with open(file, 'r') as f:
        params = json.load(f)
    return params


def load_avg_volumes(file):
    try:
        with open(file, 'r', encoding='cp1251') as f:
            avg_volumes = json.load(f)
        print('avg volumes loaded')
        return avg_volumes
    except Exception as e:
        print("Load_avg_volume_params exception:", e)
        custom_logging.add_log(f"Load_avg_volume_params exception: {e}", level=logging.ERROR)
        return None


def main():
    global common_params
    global avg_volumes
    global DEBUG
    custom_logging.add_log(f"\n*******************************************************************************")
    custom_logging.add_log(f"Bot started.")

    if DEBUG:
        common_params = load_common_params('common_params_debug.json')
        custom_logging.add_log(f"Params loaded from 'common_params_debug.json'")
    else:
        common_params = load_common_params('common_params.json')
        custom_logging.add_log(f"Params loaded from 'common_params.json'")

    if common_params is None: exit(1)
    futures = load_futures_list()
    if os.path.isfile(common_params['avg_volumes_file']) is True:  # файл средних объемов существует
        avg_volumes = load_avg_volumes(common_params['avg_volumes_file'])
    custom_logging.add_log(f'Coins is loaded ({len(futures)}.)')
    print(f'Coins is loaded ({len(futures)}.)')
    manager = QueueManager(symbols=futures, timeframes=common_params['timeframes'])
    manager.join()


if __name__ == "__main__":
    main()

## -*- coding: utf-8 -*-
import logging
from time import sleep

import json
import os
import requests
from binance import Client, ThreadedWebsocketManager
import datetime


common_params = dict() # основные параметры скрипта
CH = logging.StreamHandler()
CH.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))


class QueueManager():
    _log = logging.getLogger(__name__)
    _log.setLevel(logging.WARNING)
    _log.addHandler(CH)

    def __init__(self, symbols: list = [], timeframes: list = []) -> None:
        self._twm = ThreadedWebsocketManager()
        # self._streams = list(map(lambda s: f"{s.replace('/', '').lower()}@kline_{timeframe}", symbols))
        self._streams = []
        for symbol in symbols:
            for timeframe in timeframes:
                self._streams.append(f"{symbol.replace('/', '').lower()}@kline_{timeframe}")

        self.send_signal(f'Запуск ПО. Мониторим монеты {len(symbols)} шт. ТФ:{timeframes}', datetime.datetime.now().timestamp())

        self._twm.start()
        self._log.warning(f"Start listening to {len(self._streams)} streams")
        self._listener: str = self._twm.start_multiplex_socket(callback=self._handle_socket_message,
                                                               streams=self._streams)

    def send_signal(self, signal, candle_time):

        global common_params

        print("*" * 30 + " " + signal)
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
                "text": signal
            })
            if r.status_code == 200:
                return
            elif r.status_code != 200:
                print(f'Telegram send signal error ({signal}).')
                datetime.time.sleep(1)
                attemts_count -= 1

    def is_hummer2(self, open, high, low, close):
        '''
        check candle for hummer pattern
        :param open:
        :param high:
        :param low:
        :param close:
        :return:
        '''
        return (((high - low) > 3 * (open - close)) and
                ((close - low) / (.001 + high - low) > 0.6) and
                ((open - low) / (.001 + high - low) > 0.6))

    def is_hanging_man2(self, open, high, low, close):
        return (((high - low > 3 * (open - close)) and
                 ((close - low) / (.001 + high - low) >= 0.75) and
                 ((open - low) / (.001 + high - low) >= 0.75))
            # and
            # prev_high < open and
            # b_prev_high < open
            )

    # def is_hanging_man(open, high, low, close):
    #     return (((high - low >  * (open - close)) and
    #              ((close - low) / (.001 + high - low) >= 0.75) and
    #              ((open - low) / (.001 + high - low) >= 0.75)) and
    #             prev_high < open and
    #             b_prev_high < open)

    def is_hummer(self, open_, high, low, close):
        '''
        check candle for hummer pattern
        ex.: https://www.youtube.com/watch?v=NdlEpNl9oYA
        :param open_:
        :param high:
        :param low:
        :param close:
        :return:
        '''
        if high - low > 3 * (open_ - close) and (close - low) / (0.001 + high - low) > 0.6 and \
                (open_ - low) / (0.001 + high - low) > 0.6 and \
                abs(close - open_) > 0.1 * (high - low):
            return True
        else:
            return False

    def get_candle_proportion(self, open_, high, low, close):
        if open_ == close:
            open_ = open_ + 0.0001
        proportion = round(abs(high - low) / abs(open_ - close), 2)
        if proportion > 2 and proportion <= 2.5:
            return "1 к 2"
        elif proportion > 2.5 and proportion <= 3:
            return "1 к 3"
        elif proportion > 3 and proportion <= 3.5:
            return "1 к 3"
        elif proportion > 3.5 and proportion <= 4:
            return "1 к 4"
        elif proportion > 4 and proportion <= 4.5:
            return "1 к 4"
        elif proportion > 4.5 and proportion <= 5:
            return "1 к 5"
        elif proportion > 5 and proportion <= 5.5:
            return "1 к 5"
        elif proportion > 5.5 and proportion <= 6:
            return "1 к 6"
        elif proportion > 6 and proportion <= 6.5:
            return "1 к 6"
        elif proportion > 6.5 and proportion <= 7:
            return "1 к 7"
        elif proportion > 7 and proportion <= 7.5:
            return "1 к 7"
        elif proportion > 7.5 and proportion <= 8:
            return "1 к 8"
        elif proportion > 8 and proportion <= 8.5:
            return "1 к 8"
        elif proportion > 8.5 and proportion <= 9:
            return "1 к 9"
        elif proportion > 9 and proportion <= 9.5:
            return "1 к 9"
        elif proportion > 9.5 and proportion <= 10:
            return "1 к 10"
        elif proportion > 10 and proportion <= 10.5:
            return "1 к 10"
        else:
            return f"1 к {proportion}"

    def check_bar_for_signal(self, symbol, open_, high, low, close, volume, timeframe, candle_time):
        signal = ''
        try:
            hummer = self.is_hummer2(open_, high, low, close)
            hanging_man = self.is_hanging_man2(open_, high, low, close)
            proportion = self.get_candle_proportion(open_, high, low, close)
            if hummer:
                signal = f'{symbol}:{timeframe}:LONG:{proportion}'
            elif hanging_man:
                signal = f'{symbol}:{timeframe}:SHORT:{proportion}'
        except Exception as e:
            print(e)
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
                    signal = self.check_bar_for_signal(symbol, open_, high, low, close, volume, timeframe, candle_time)
                    if signal != '':
                        # print(signal)
                        self.send_signal(signal, candle_time)


        except Exception as e:
            print("on_message exception:", e)
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

def load_futures_list():
    global common_params
    client = Client(common_params["API_Key"], common_params["Secret_Key"])
    futures_info_list = client.futures_exchange_info()
    futures = []
    for item in futures_info_list['symbols']:
        if item['status'] != 'TRADING': continue
        futures.append(item['pair'])
    return futures


def load_common_params(file):
    if os.path.exists(file) is False:
        print(f'File {file} not exists.')
        return None

    with open(file, 'r') as f:
        params = json.load(f)
    return params


def main():
    global common_params
    common_params = load_common_params('common_params.json')
    if common_params is None: exit(1)
    futures = load_futures_list()
    print(f'Coins is loaded ({len(futures)}.)')
    manager = QueueManager(symbols=futures, timeframes=['1h', '4h'])
    manager.join()


if __name__ == "__main__":
    main()

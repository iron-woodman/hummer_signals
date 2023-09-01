import websocket
import json
from binance import Client, ThreadedWebsocketManager
import logger as custom_logging
import logging
import os


common_params = dict()  # основные параметры скрипта
futures = [] # список фьючерсов USDT
DEBUG = True

CH = logging.StreamHandler()
CH.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))

_log = logging.getLogger(__name__)
_log.setLevel(logging.INFO)
_log.addHandler(CH)

def load_common_params(file):
    if os.path.exists(file) is False:
        print(f'File {file} not exists.')
        custom_logging.add_log(f'File {file} not exists.', level=logging.WARNING)
        return None

    with open(file, 'r') as f:
        params = json.load(f)
    return params


def lets_close_ws():
    with open('closing_socket.txt') as f:
        return int(f.readline()) > 0



def on_open(_wsa):
    global futures
    global common_params
    data = dict(
        method="SUBSCRIBE",
        id=1,
        params=[]
    )

    for symbol in futures:
        for timeframe in common_params['timeframes']:
            data['params'].append(f"{symbol.replace('/', '').lower()}@kline_{timeframe}")
    _wsa.send(json.dumps(data))


def on_message(_wsa, message):
    if lets_close_ws(): _wsa.close()

    # if ('e' in message):
        # if (message['m'] == 'Queue overflow. Message not filled'):
        #     _log.warning("Socket queue full. Resetting connection.")
        #     reset_socket()
        #     return
        # else:
        #     _log.error(f"Stream error: {message['m']}")
        #     exit(1)
    try:

        json_message = json.loads(message)
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
            _log.info(f'{symbol}:(open={open_}, high={high}, low={low}, close={close}, timeframe="{timeframe}")')
            # with open(f"candles_{timeframe}.txt", "a") as f:
            #     f.write(f"(open={open_}, high={high}, low={low}, close={close}, volume={volume}, timeframe={timeframe})")

            signal = ''
            # signal = self.check_bar_for_signal(symbol, open_, high, low, close, volume, timeframe)
            # if signal != '':
            #     # print(signal)
            #     self.send_signal(signal)


    except Exception as e:
        print("on_message exception:", e)
        # self._log.error("on_message exception:", e)
    # print(message)


def load_futures_list():
    global common_params
    _ = []
    try:
        client = Client(common_params["API_Key"], common_params["Secret_Key"])
        futures_info_list = client.futures_exchange_info()
        for item in futures_info_list['symbols']:
            if item['status'] != 'TRADING': continue
            _.append(item['pair'])
    except Exception as e:
        custom_logging.add_log(f"load_futures_luist exception: {e}", level=logging.ERROR)
    return _


def run():
    global futures
    global common_params
    if DEBUG:
        common_params = load_common_params('common_params_debug.json')
        custom_logging.add_log(f"Params loaded from 'common_params_debug.json'")
    else:
        common_params = load_common_params('common_params.json')
        custom_logging.add_log(f"Params loaded from 'common_params.json'")
    futures = load_futures_list()

    WEBSOCKET_URL_FUTURES = "wss://fstream.binance.com/ws"
    WEBSOCKET_URL_SPOT = "wss://stream.binance.com:9443/ws"
    stream_name = 'saa_binance_clines_stream'
    wss = f'{WEBSOCKET_URL_FUTURES}/{stream_name}'
    wsa = websocket.WebSocketApp(wss, on_message=on_message, on_open=on_open)
    wsa.run_forever()




if __name__ == '__main__':
    run()
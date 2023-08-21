## -*- coding: utf-8 -*-
# https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md#subscribe-to-a-stream
# https://www.youtube.com/watch?v=z2ePTq-KTzQ
import websocket
import json
import rel
import os
import requests
import time
import multiprocessing
from binance import Client
import datetime

from sqlalchemy import create_engine


# engine = create_engine('sqlite:///CryptoDB.db')
THREAD_CNT = 2 # 3 потока на ядро
DEBUG = True # флаг вывода отладочных сообщений во время разработки
currency_pairs = [] # пары криптовалют
time_frames = [] # рабочие таймфреймы
timeframe_pricelimit_volumelimit = dict() # key = timeframe, value={price_procent, volume_procent}
avg_volumes = [] # средние объемы для каждого таймфрейма

rel.safe_read()
last_bar = dict() # предыдущий бар key=symbol_timeframe, val=[open, high, low, close, volume]
common_params = dict() # основные параметры скрипта
TRIAL_EXP_DATE=1642365487.853374
# "Program_Key": 595595

def load_timeframe_params(file):
    global timeframe_pricelimit_volumelimit

    if os.path.isfile(file) is False:  # файл еще не существует
        return None
    with open(file, 'r') as f:
        timeframe_params = json.load(f)
    for item in timeframe_params:
        print(item)
    for param in timeframe_params:
        time_frames.append(param['timeframe'])
        limits = dict()
        # timeframe_pricelimit_volumelimit = dict()  # key = timeframe, value={price_procent, volume_procent}
        if "price change (%)" in param.keys():
            limits['price procent'] = param["price change (%)"]
        else:
            limits['price procent'] = 0

        if "volume change average(%)" in param.keys():
            limits['volume procent'] = param['volume change average(%)']
        else:
            limits['volume procent'] = 0

        timeframe_pricelimit_volumelimit[param['timeframe']] = limits
    return timeframe_params


def load_avg_volume_params(file):
    if os.path.isfile(file) is False: # файл еще не существует
        print(f'файл средних объемов {file} не обнаружен')
        return
    pairs = []
    with open(file, 'r') as f:
        avg_volumes = json.load(f)
        for avg_volume in avg_volumes:
            pairs.append(avg_volume)
    print('Валютные пары и средние объемы загружены.')
    return avg_volumes, pairs


def load_common_params(file):
    if os.path.exists(file) is False:
        print(f'Файл {file} не существует.')
        return None

    with open(file, 'r') as f:
        params = json.load(f)
    return params


def GetVolumeListAndAvg(bars):
    _ = []
    avg = 0.0
    for bar in bars:
        val = float(bar[5])
        _.append(val)
        avg += val
    avg = avg/len(bars)
    return avg


def load_history_bars(task):
    """
    загрузить исторические бары валютной пары по каждому таймфрейму из настроек
    :return:
    """
    result = dict()
    pair = task[0]
    api_key = task[1]
    secret_key = task[2]
    all_timeframes = task[3]
    client = Client(api_key, secret_key)

    try:

        result['id'] = pair

        for timeframe in all_timeframes :

            if timeframe == '1m':
                st_time = "1 day ago UTC"
                # delta = timedelta(minutes=bars_count)
            elif timeframe == '3m':
                st_time = "3 day ago UTC"
                # delta = timedelta(minutes=bars_count * 3)
            elif timeframe == '5m':
                st_time = "5 day ago UTC"
                # delta = timedelta(minutes=bars_count * 5)
            elif timeframe == '15m':
                st_time = "15 day ago UTC"
                # st_time = str(int(datetime.now().timestamp() * 1000))
                # delta = timedelta(minutes=bars_count * 15)
            elif timeframe == '30m':
                st_time = "30 day ago UTC"
                # delta = timedelta(minutes=bars_count * 30)
            elif timeframe == '1h':
                st_time = "60 day ago UTC"
                # delta = timedelta(hours=bars_count)
            elif timeframe == '2h':
                st_time = "120 day ago UTC"
                # delta = timedelta(hours=bars_count * 2)
            elif timeframe == '4h':
                st_time = "120 day ago UTC"
                # delta = timedelta(hours=bars_count * 4)
            elif timeframe == '6h':
                st_time = "120 day ago UTC"
                # delta = timedelta(hours=bars_count * 6)
            elif timeframe == '8h':
                st_time = "120 day ago UTC"
                # delta = timedelta(hours=bars_count * 8)
            elif timeframe == '12h':
                st_time = "185 day ago UTC"
                # delta = timedelta(hours=bars_count * 12)
            elif timeframe == '1d':
                st_time = "365 day ago UTC"
                # delta = timedelta(days=bars_count)
            # elif timeframe == '3d':
            #     st_time = "2 year ago UTC"
            #     # delta = timedelta(days=bars_count * 3)
            # elif timeframe == '1w':
            #     st_time = "2 year ago UTC"
            #     # delta = timedelta(weeks=bars_count)
            # elif timeframe == '1M':
            #     st_time = "3 year ago UTC"
            #     # delta = timedelta(days=bars_count*31)
            else:
                print('неизвестный таймфрейм:', timeframe)
                continue

            # рассчитываем время загрузки баров (start_str)
            # st_time = (datetime.now() - delta).date()
            # st_time = st_time.ctime()
            # st_time = st_time.replace('00:00:00', '')
            # st_time = '"12 Jan, 2022"'
            bars = []
            try:
                bars = client.get_historical_klines(pair, timeframe, st_time)
            except Exception as e:
                print(e.status_code, e.Message)

            if len(bars) == 0:
                print(f"В результате запроса client.get_historical_klines({pair}, {timeframe}, {st_time}) "
                      f"получено 0 баров истории. Видимо следует исправить количество запрашиваемых баров истории.")
                result[timeframe] = 0
                continue
            avg = GetVolumeListAndAvg(bars)
            result[timeframe] = round(avg, 2) #float("{0.2f}".format(avg))
        print(result)
        time.sleep(1)
        return result
    except Exception as e:
        print("Exception when calling load_history_bars: %s\n" % e)
        return None


def update_avg_volumes():
    global currency_pairs
    global common_params
    global time_frames
    tasks = []
    for symbol in currency_pairs:
        tasks.append((symbol, common_params["API_Key"], common_params["Secret_Key"], time_frames))

    try:
        with multiprocessing.Pool(multiprocessing.cpu_count() * THREAD_CNT) as pool:
            responce_list = pool.map(load_history_bars, tasks)
            data = dict()
            for responce in responce_list:
                id = responce['id']
                del responce['id']
                data[id] = responce
            # print(data)
            try:
                with open('pair_volume.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                    print('объемы сохранены в файл.')
            except Exception as e:
                print(e)
            pool.close()
            pool.join()

    except Exception as ex:
        print("update_avg_volumes exception: %s\n" % (ex.Message))
        return
    print('обновление средних объемов завершено')

def check_trial_date(candle_time):
    if candle_time > TRIAL_EXP_DATE:
        print("Срок действия триальной версии истек. Обратитесь к разработчику за лицензией на данное ПО.")
        return False
    return True


def send_signal(signal, candle_time):

    global common_params
    if "Program_Key" not in common_params:
        print('595')
        if check_trial_date(candle_time) == False: return
    elif common_params["Program_Key"] != 595595:
        print("Неверный ключ лицензии ПО. Обратитесь к разработчику")
        return

    print("*"*30 + " " + signal)
    token = common_params["telegram_token"]
    url = "https://api.telegram.org/bot"
    channel_id = common_params["telegram_channel_id"]
    # channel_name = "signals555"
    url += token
    method = url + "/sendMessage"
    attemts_count = 5
    while(attemts_count > 0):
        r = requests.post(method, data={
             "chat_id": channel_id,
             "text": signal
              })
        if r.status_code == 200:
            return
        elif r.status_code != 200:
            print(f'Ошибка при попытке отправить сигнал ({signal}) в телеграм.')
            print(f'Осталось {attemts_count} попыток.')
            time.sleep(1)
            attemts_count -= 1

def check_bar_for_signal(pair, close, volume, timeframe, candle_time):
    global avg_volumes
    try:
        volume_percent_limit = timeframe_pricelimit_volumelimit[timeframe]["volume procent"] # объем берем только для заданного таймфрейма

        # for timeframe in time_frames:
        price_percent_limit = timeframe_pricelimit_volumelimit[timeframe][
            "price procent"]  # key = timeframe, value={price_procent, volume_procent}
        prev_bar_close = last_bar[pair + "_" + timeframe][
            'close']  # key = pair_timefame, value = dict{close, time, volume}
        price_percent = abs((prev_bar_close - close) / prev_bar_close) * 100
        # направление изменения цены
        direction ="+"# "выросла"
        if prev_bar_close > close:
            direction = "-"# "упала"

        if price_percent_limit > 0.0 and volume_percent_limit > 0.0:
             # для данного таймфрейма необходимо проверить условия по объему и цене
             if price_percent >= price_percent_limit:
                 # есть сигнал по цене, проверяем сигнал по объему
                 avg_volume = avg_volumes[pair][timeframe]
                 if avg_volume > volume:
                     return
                     # continue # об уменьшении объема сигнал не подаем
                 if avg_volume <= 0.0:
                     print(f'{pair}: средний объем = 0')
                     return
                     # continue
                 else:
                    volume_percent = abs((avg_volume - volume) / avg_volume) * 100
                    if volume_percent > volume_percent_limit:
                         # есть сигнал и по объему
                         send_signal(
                             f'{pair} на {timeframe}: цена {direction} на {round(price_percent, 2)}%, объем + {round(volume_percent, 2)}%', candle_time)

        elif price_percent_limit > 0 and volume_percent_limit == 0:
             # для данного таймфрейма необходимо проверить условия по цене
             if price_percent >= price_percent_limit:
                 send_signal(
                     f'{pair} на {timeframe}: цена {direction} на {round(price_percent, 2)}%', candle_time)

        elif price_percent_limit == 0 and volume_percent_limit > 0:
            # для данного таймфрейма необходимо проверить условия по объему
            avg_volume = avg_volumes[pair][timeframe]
            if avg_volume <= 0.0:
                return
            if avg_volume > volume:
                # continue  # об уменьшении объема сигнал не подаем
                return
            volume_percent = abs((avg_volume - volume) / avg_volume) * 100
            if volume_percent > volume_percent_limit:
                # есть сигнал и по объему
                send_signal(f'{pair} на {timeframe}: объем + на {round(volume_percent, 2)}%', candle_time)
    except Exception as e:
        print(f'check_bar_for_signal({pair}, {close}, {volume}, {timeframe}) exception:', e.Message, '\n')

def check_for_avg_volume_update(file):
    global common_params
    try:
        last_update_time = datetime.datetime.fromtimestamp(os.path.getmtime(file))
        update_interval = common_params["avg_volumes_update_interval(hours)"]
        next_update_time = last_update_time + datetime.timedelta(hours=update_interval)#datetime.timedelta(hours=update_interval)
        if datetime.datetime.now() > next_update_time:
            return True
        else:
            return False
    except Exception as e:
        print("check_for_avg_volume_update exception:", e.Message)
        return False




def on_message(ws, message):
    global avg_volumes
    try:
        json_message = json.loads(message)
        symbol = json_message['s']
        candle = json_message['k']
        is_candle_closed = candle['x'] #True -свеча сформировалась (закрыта), False - еще формируется (открыта)
        open_ = float(candle['o'])
        high = float(candle['h'])
        low = float(candle['l'])
        close = float(candle['c'])
        volume = float(candle['v'])
        timeframe = candle['i']
        candle_time = candle['t']

        if is_candle_closed:
            if symbol + '_' + timeframe in last_bar:
                check_bar_for_signal(symbol, close, volume, timeframe, candle_time)
            last_bar[symbol + '_' + timeframe] = {'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume}
            if DEBUG: print(symbol, timeframe, last_bar[symbol + '_' + timeframe])
            if check_for_avg_volume_update('pair_volume.json') is True:
                # пришло время обновить средние объемы
                update_avg_volumes()
                avg_volumes, currency_pairs = load_avg_volume_params('pair_volume.json')
    except Exception as e:
        print("on_message exception:", e)
        # запись свечей в файл для теста
        # try:
        #     file_path = os.getcwd() + f"\data\{symbol}_{timeframe}.json"
        #     with open(file_path, 'a', encoding='utf-8') as f:
        #         json.dump(last_bar[symbol + '_' + timeframe], f, ensure_ascii=False, indent=4)
        # except Exception as e:
        #     print(e.Message)

def on_error(ws, error):
    print('Socket error:', error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def load_params():
    """
    формируем список таймфремов по которым нужны бары и кол-во этих баров
    :return:
    """

    global timeframe_pricelimit_volumelimit
    try:




        with open('timeframes_params.json', 'r') as f:
            config = json.load(f)
            print(config)

        time_frames = []
        for param in config:
            time_frames.append(param['timeframe'])
            limits = dict()
            # timeframe_pricelimit_volumelimit = dict()  # key = timeframe, value={price_procent, volume_procent}
            if "price change (%)" in param.keys():
                limits['price procent'] = param["price change (%)"]
            else:
                limits['price procent'] = 0

            if "volume change average(%)" in param.keys():
                limits['volume procent'] = param['volume change average(%)']
            else:
                limits['volume procent'] = 0

            timeframe_pricelimit_volumelimit[param['timeframe']] = limits

        return time_frames, filters

    except Exception as e:
        print(e)
        return None

def load_futures_list():
    global common_params
    client = Client(common_params["API_Key"], common_params["Secret_Key"])
    futures_info_list = client.futures_exchange_info()
    futures = []
    for item in futures_info_list['symbols']:
        if item['status'] != 'TRADING': continue
        futures.append(item['pair'])
    return futures

def update_pairs_list(config, filters):
    """
    update list all currency pairs supported
    :return:
    """
    global futures
    global common_params
    client = Client(common_params["API_Key"], common_params["Secret_Key"])
    pairs = []
    try:
        # Extract trading pairs from exchange information
        tickers = client.get_ticker()
        for ticker in tickers:
            if float(ticker['volume']) < filters["volume_24h"]: continue
            if filters['USDT_only'] == 'True' and 'USDT' not in ticker['symbol']: continue
            if filters['futures_only'] == 'True' and ticker['symbol'] not in futures: continue
            # config['id'] = ticker['symbol']
            pairs.append(ticker['symbol'])
        return pairs
    except Exception as ex:
        print("update_pairs_list exception, label: %s, message: %s\n" % (ex.label, ex.message))
        return None

def load_filters(file):
    with open(file, 'r') as f:
        filters = json.load(f)
        return  filters

def main():
    global avg_volumes
    global common_params
    global currency_pairs
    global filters
    global futures

    common_params = load_common_params('common_params.json')
    if common_params is None: exit(1)

    filters = load_filters('data_filters.json')
    time_frame_params = load_timeframe_params('timeframes_params.json')
    if time_frame_params is None: exit(1)

    if filters["futures_only"]: # загружаем список фьючерсов
        futures = load_futures_list()
    currency_pairs = update_pairs_list(time_frame_params, filters)
    send_signal('Запуск ПО. Проверка связи.', datetime.datetime.now().timestamp())

    if os.path.isfile('pair_volume.json') is False: # файл средних объемов еще не существует
        # нужно собрать средние объемы
        update_avg_volumes()
    avg_volumes, currency_pairs = load_avg_volume_params('pair_volume.json')

    if DEBUG: print(len(currency_pairs))

    streams = []
    for symbol in currency_pairs:
        for timeframe in time_frames:
            streams.append(f"{symbol.lower()}@kline_{timeframe}")

    try:
        socket = "wss://stream.binance.com:9443/ws/" + '/'.join(streams)
        ws = websocket.WebSocketApp(socket,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        ws.run_forever(dispatcher=rel)  # Set dispatcher to automatic reconnection
        rel.signal(2, rel.abort)        # Keyboard Interrupt
        rel.dispatch()

    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()


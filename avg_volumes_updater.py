## -*- coding: utf-8 -*-
import multiprocessing
import json
import os
import time

from binance import Client

THREAD_CNT = 2 # 3 потока на ядро
PAUSE = 5 # пауза между запросами истории
DEBUG = False# флаг вывода отладочных сообщений во время разработки
currency_pairs = [] # пары криптовалют
common_params = dict() # основные параметры скрипта


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
                st_time = "90 day ago UTC"
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
                print(pair,':', e)

            if len(bars) == 0:
                print(f"В результате запроса client.get_historical_klines({pair}, {timeframe}, {st_time}) "
                      f"получено 0 баров истории. Видимо следует исправить количество запрашиваемых баров истории.")
                result[timeframe] = 0
                continue
            avg = GetVolumeListAndAvg(bars)
            result[timeframe] = round(avg, 2) #float("{0.2f}".format(avg))
        print(result)
        time.sleep(PAUSE)
        return result
    except Exception as e:
        print("Exception when calling load_history_bars: ", e)
        return None


def load_history_bars_end(responce_list):
    global avg_volumes
    global common_params

    data = dict()
    for responce in responce_list:
        id = responce['id']
        del responce['id']
        data[id] = responce
    # print(data)
    try:
        with open(common_params['avg_volumes_file'], 'w', encoding='cp1251') as f:
            json.dump(data, f, ensure_ascii=False, indent=4, separators=(',', ': '))
            print('объемы сохранены в файл.')
        avg_volumes = load_avg_volume_params(common_params['avg_volumes_file'])
    except Exception as e:
        print("Исключение при сохранении средних объемов в файл:", e)


def load_avg_volume_params(file):
    if os.path.isfile(file) is False: # файл еще не существует
        print(f'файл средних объемов {file} не обнаружен')
        return None
    pairs = []
    try:
        with open(file, 'r', encoding='cp1251') as f:
            avg_volumes = json.load(f)
        print('Cредние объемы загружены.')
        return avg_volumes
    except Exception as e:
        print("load_avg_volume_params exception:", e)
        return None


def update_avg_volumes(timeframes):
    global currency_pairs
    global common_params
    tasks = []

    for symbol in currency_pairs:
        tasks.append((symbol, common_params["API_Key"], common_params["Secret_Key"], timeframes))

    try:
        with multiprocessing.Pool(multiprocessing.cpu_count() * THREAD_CNT) as pool:
            pool.map_async(load_history_bars, tasks, callback=load_history_bars_end)
            pool.close()
            pool.join()
    except Exception as ex:
        print("update_avg_volumes exception:", ex)
        return


def load_common_params(file):
    if os.path.exists(file) is False:
        print(f'File {file} not exists.')
        return None
    with open(file, 'r') as f:
        params = json.load(f)
    return params


def load_futures_list():
    global common_params
    client = Client(common_params["API_Key"], common_params["Secret_Key"])
    futures_info_list = client.futures_exchange_info()
    futures = []
    for item in futures_info_list['symbols']:
        if item['status'] != 'TRADING': continue
        futures.append(item['pair'])
    return futures


def main():
    global common_params
    global currency_pairs
    common_params = load_common_params('common_params.json')

    if common_params is None: exit(1)
    currency_pairs = load_futures_list()
    if os.path.isfile(common_params['avg_volumes_file']) is False:  # файл средних объемов еще не существует
        # нужно собрать средние объемы
        update_avg_volumes(common_params['timeframes'])
    elif os.path.getsize(common_params['avg_volumes_file']) == 0:
        update_avg_volumes(common_params['timeframes'])


if __name__ == '__main__':
    main()
from secret import sandboxapikey, proapikey

import asyncio
import aiohttp
import json
from time import time
from datetime import datetime
import re

# Я не придумал ничего лучше,
# чем сохранять результат работы асинхронной функции
# в глобальной переменной.
# Я знаю что это не очень круто.
results = []


def check_last_updated(data):
    res = True
    todaystr = datetime.today().strftime('%Y-%m-%d')
    for ticker in data['data']:
        if ticker['last_updated'].split('T')[0] != todaystr:
            res = False
            break
    return res


def check_tests_passed(results):
    tests_passed = True
    for idx, result in enumerate(results):
        if result['status_code'] != 200:
            tests_passed = False
            print('Запрос № {} тест провален, код ответа - {} не равен 200.'.format(idx + 1, result['status_code']))
            break
        elif result['time'] >= 0.5:
            tests_passed = False
            print('Запрос № {} тест провален, время выполнения запроса {} секунд больше 0.5.'.format(idx + 1, result['time']))
            break
        elif result['size'] > 10240:
            tests_passed = False
            print('Запрос № {} тест провален, размер полученного пакета данных = {} больше 10 Кб.'.format(idx + 1, result['size']))
            break
        elif not check_last_updated(result['data']):
            tests_passed = False
            print('Запрос № {} тест провален, информация не актуальна (не за текущий день).'.format(idx + 1))
            break
    return tests_passed


def latency80(latencies):
    latencies.sort()
    idx = int(0.8 * len(latencies)) - 1
    return latencies[idx]


def write_response_to_file(data):
    filename = re.sub(data['status']['timestamp'], ':', '-')
    with open(filename, 'w') as file:
        json.dump(data, file, indent=2)


async def fetch_content(url, parameters, session):
    global results
    t0 = time()
    async with session.get(url, params=parameters) as response:
        data = await response.json()
        status_code = response.status
        datasize = response.content.total_bytes
    delta_t = time() - t0
    result = {'time': delta_t,
              'status_code': status_code,
              'data': data,
              'size': datasize
              }
    results.append(result)


async def make_requests(number_of_tests):
    # url = 'https://sandbox-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    parameters = {
        'start': '1',
        'limit': '10',
        'convert': 'USD',
        'sort': 'volume_24h'
    }
    headers = {
        'Accepts': 'application/json',
        # 'X-CMC_PRO_API_KEY': sandboxapikey,
        'X-CMC_PRO_API_KEY': proapikey
    }
    tasks = []

    async with aiohttp.ClientSession(headers=headers) as session:
        for i in range(number_of_tests):
            task = asyncio.create_task(fetch_content(url, parameters, session))
            tasks.append(task)

        await asyncio.gather(*tasks)


def main():
    NUMBER_OF_TESTS = 8
    t0 = time()
    asyncio.run(make_requests(NUMBER_OF_TESTS))
    delta_t = time() - t0

    for idx, result in enumerate(results):
        print('Время выполнения запроса {} - {} секунд, код ответа {}.'.format(idx + 1, result['time'], result['status_code']))
        write_response_to_file(result['data'])

    print('Время выполнения всех запросов {} секунд'.format(delta_t))
    rps = NUMBER_OF_TESTS / delta_t
    print('rps = ', rps)
    latency_80 = latency80([result['time'] for result in results])
    print('80% latency = ', latency_80)

    if not check_tests_passed(results):
        print('Test failed')
    elif rps <= 5:
        print('Test failed, rps = {} - меньше 5 запросов в секунду'.format(rps))
    elif latency_80 >= 0.45:
        print('Test failed, 80% latency = {} > 450 мс'.format(latency_80))
    else:
        print('Tests passed')


if __name__ == '__main__':
    main()

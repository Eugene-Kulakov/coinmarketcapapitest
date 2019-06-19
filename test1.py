from secret import sandboxapikey, proapikey
from requests import Session
import json
from time import time
from datetime import datetime
from sys import getsizeof


def gettickerslist():
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

    session = Session()
    session.headers.update(headers)

    t0 = time()
    response = session.get(url, params=parameters)
    delta_t = time() - t0
    return response, delta_t


def write_response_to_file(data):
    filename = 'output\\response{}.txt'.format(int(time() * 1000))
    with open(filename, 'w') as file:
        json.dump(data, file, indent=2)


def check_last_updated(data):
    res = True
    todaystr = datetime.today().strftime('%Y-%m-%d')
    for ticker in data['data']:
        if ticker['last_updated'].split('T')[0] != todaystr:
            res = False
            break
    return res


def main():
    response, delta_t = gettickerslist()
    if response.status_code != 200:
        print('Error {}\n Test failed'.format(response.status_code))
        return 0
    data = response.json()
    write_response_to_file(data)
    datasize = len(response.content)

    print('Время выполнения запроса {} секунд'.format(delta_t))
    print('Размер полученного пакета данных {} байт'.format(datasize))
    if delta_t < 0.5 and datasize < 10240 and check_last_updated(data):
        print('Test passed')
    else:
        print('Test failed')


if __name__ == '__main__':
    main()

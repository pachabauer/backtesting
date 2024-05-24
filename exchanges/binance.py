import typing
import requests
import logging
from typing import *

logger = logging.getLogger()


# por defecto usaremos binance Spot, por eso cuando instanciemos la clase definiremos el boolean
# Pero podría usarse los futuros y traer los precios de los mismos
class BinanceClient:
    def __init__(self, futures=False):

        self.futures = futures

        if self.futures:
            self._base_url = "https://fapi.binance.com"
        else:
            self._base_url = "https://api.binance.com"

        self.symbols = self._get_symbols()

    # hago el request
    def _make_request(self, endpoint: str, query_parameters: typing.Dict):

        try:
            response = requests.get(self._base_url + endpoint, params=query_parameters)
        except Exception as e:
            logger.error("Connection error while making request to %s: %s", endpoint, e)
            return None

        # si está ok (200) else, logueamos error
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making request to %s: %s (status code = %s)", endpoint, response.json()
                         , response.status_code)

        return None

    # traigo la lista de contratos
    def _get_symbols(self) -> List[str]:

        # guardo los parámetros
        params = dict()

        if self.futures:
            endpoint = "/fapi/v1/exchangeInfo"
        else:
            endpoint = "/api/v3/exchangeInfo"

        data = self._make_request(endpoint, params)

        # inline for para de la lista de contratos (con toda la data), crear otra lista solo de símbolos
        # para la lista data['symbols'] (que tiene nombre, otros datos, etc) , creo una lista symbols que itera (x)
        # en cada símbolo de la lista original y saca los symbols
        symbols = [x["symbol"] for x in data['symbols']]

        return symbols

    # traigo las candles: opcional pasarle el start y end, sino trae las mas recientes.
    def get_historical_data(self, symbol: str, start_time: Optional[int] = None, end_time: Optional[int] = None):

        params = dict()

        params['symbol'] = symbol
        params['interval'] = "1m"
        params['limit'] = 1500

        if start_time is not None:
            params['startTime'] = start_time

        if end_time is not None:
            params['endTime'] = end_time

        if self.futures:
            endpoint = "/fapi/v1/klines"
        else:
            endpoint = "/api/v3/klines"

        raw_candles = self._make_request(endpoint, params)

        candles = []

        if raw_candles is not None:
            # itero sobre una lista de tuplas
            # timestamp, open, high, low, close, volume
            for c in raw_candles:
                candles.append((float(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])), )
            return candles
        else:
            return None

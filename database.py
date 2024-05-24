import h5py
import time
import numpy as np
import logging
import pandas as pd
from typing import *

logger = logging.getLogger()


class Hdf5Client:
    def __init__(self, exchange: str):
        # debo definir el nombre del File y su modo (a) sería read and write (de append)
        self.hf = h5py.File(f"data/{exchange}.h5", 'a')
        # necesito mandar el flush, porque la información debe poder guardarse aun si no cierro el file, ya que
        # si hago un proceso y no hago el flush, el file se puede romper.
        self.hf.flush()

    # método para crear el dataset
    def create_dataset(self, symbol: str):
        # si no encuentra el símbolo en el dataset, lo crea (por ejemplo eth.h5), sino no hace nada
        if symbol not in self.hf.keys():
            # defino los parámetros, nombre, filas y columnas, dimensión máxima para filas y columnas
            # 6 columnas por Timestamp, Open, High, Low, Close, Volume
            # y el data type, en este caso float64 es un tipo de la librería Numpy equivalente a Double
            self.hf.create_dataset(symbol, (0, 6), maxshape=(None, 6), dtype="float64")
            self.hf.flush()

    # método para escribir data, en este caso será una lista de tuplas del método data_collector.get_historical_data()
    def write_data(self, symbol: str, data: List[Tuple]):

        # establezco los timestamps minimo y maximo para no re-escribir data y que haya duplicados
        min_ts, max_ts = self.get_first_last_timestamp(symbol)

        # si no tiene datos, le fuerzo el valor para que se pueda cumplir el siguiente if y se agreguen datos al
        # dataset (el loop for)
        if min_ts is None:
            min_ts = float("inf")
            max_ts = 0

        filtered_data = []

        for d in data:
            if d[0] < min_ts:
                filtered_data.append(d)
            elif d[0] > max_ts:
                filtered_data.append(d)

        if len(filtered_data) == 0:
            logger.warning("%s: No data to insert", symbol)
            return

        # convierto a numpy array
        data_array = np.array(filtered_data)

        # accedemos al dataset con la key (como un diccionario)
        # incrementamos las rows del dataset con el número de rows que insertaremos
        # para indicar que solo serán las rows las que incrementaremos indicamos axis=0 (columnas sería axis=1)
        # el nuevo size del dataset será el actual + los datos que insertaremos
        self.hf[symbol].resize(self.hf[symbol].shape[0] + data_array.shape[0], axis=0)
        # vamos a insertar la data
        # selecciono las últimas insertadas hasta el final (con el -data_array.shape[0]:)
        self.hf[symbol][-data_array.shape[0]:] = data_array
        self.hf.flush()

    # para traer data del file h5 y usarlo
    def get_data(self, symbol: str, from_time: int, to_time: int) -> Union[None, pd.DataFrame]:

        # logs para mostrar cuánto demora cada operación
        start_query = time.time()

        existing_data = self.hf[symbol][:]

        # Si no hay data en el h5, devuelve None
        if len(existing_data) == 0:
            return None

        # ordeno la data cronológicamente en base a la key (que representa la primer columna del h5 (timeframe))
        data = sorted(existing_data, key=lambda x: x[0])
        # sorted devuelve una lista, lo convierto a array para luego poder convertirlo a dataframe
        data = np.array(data)

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        # ahora filtro el dataframe para que tome el from_time y el to_time
        df = df[(df['timestamp'] >= from_time) & (df['timestamp'] <= to_time)]
        # convierto la columna timestamp a int en milisegundos y luego la seteo como indice (True para que figure
        # solo como indice)
        df['timestamp'] = pd.to_datetime(df['timestamp'].values.astype(np.int64), unit='ms')
        df.set_index('timestamp', drop=True, inplace=True)

        query_time = round(time.time() - start_query, 2)
        logger.info("Retrieved %s %s data from database in % seconds", len(df.index), symbol, query_time)

        return df

    # para traer el primer y último timestamp para actualizar el h5
    # 2 opciones, o trae None None, porque el dataset podría estar vacío, o trae los valores porque contiene
    def get_first_last_timestamp(self, symbol: str) -> Union[Tuple[None, None], Tuple[float, float]]:

        existing_data = self.hf[symbol][:]

        # si no tiene data, debo hacer el Initial request
        if len(existing_data) == 0:
            return None, None

        # si no está vacío, devuelvo el min y max timestamp
        # para seleccionar la primera columna, uso el key = lambda, y a su vez le agrego un [0] al final
        # para indicar que tomaré la columna de timestamp
        first_ts = min(existing_data, key=lambda x: x[0])[0]
        last_ts = max(existing_data, key=lambda x: x[0])[0]
        return first_ts, last_ts

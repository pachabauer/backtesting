import time
import logging
from utils import *
import typing
from exchanges.binance import BinanceClient
from database import Hdf5Client

logger = logging.getLogger()


# Uso el Union por si más adelante quiero tomar data de otros exchanges. (en el curso usa FTX, pero ya murió)
def collect_all(client: typing.Union[BinanceClient], exchange: str, symbol: str):
    h5_db = Hdf5Client(exchange)
    h5_db.create_dataset(symbol)

    oldest_ts, most_recent_ts = h5_db.get_first_last_timestamp(symbol)

    # Initial request
    if oldest_ts is None:
        # el end_time se expresa en milisegundos (es un timestamp) y resto (1 minuto) 60 segundos * 1000 (milisegundos)
        data = client.get_historical_data(symbol, end_time=int(time.time() * 1000) - 60000)

        # si existe la data pero es 0, entonces el símbolo existe en el exchange pero por alguna razón no tiene data
        if len(data) == 0:
            logging.warning("%s %s: no initial data found", exchange, symbol)
            return
        else:
            # muestra el primer elemento de la lista y sus open, high, low, close, volume y el último
            # con la funcion ms_to_dt convierto a datetime el timestamp
            logger.info("%s %s: Collected %s initial data from %s to %s", exchange, symbol, len(data),
                        ms_to_dt(data[0][0]), ms_to_dt(data[-1][0]))

        oldest_ts = data[0][0]
        most_recent_ts = data[-1][0]

        h5_db.write_data(symbol, data)

    # es una lista que se incrementará progresivamente, en vez de estar llamando al método write_data a cada rato y
    # hacer el programa muy lento.

    data_to_insert = []

    # Insert the data in the database

    # Most recent data
    # en caso que ya tenga alguna data y necesite actualizar la que falta hasta hoy
    while True:
        # traigo la data desde el último timestamp + 60 segundos (* 1000 milisegundos), ya que trae timeframe 1m
        data = client.get_historical_data(symbol, start_time=int(most_recent_ts * 60000))

        # Si no completa el traer toda la data (por ejemplo por un error), espero 4 segundos e intento de nuevo
        if data is None:
            time.sleep(4)
            continue

        # corto el loop del while si recolecté toda la info necesaria hasta 2 minutos atrás.
        if len(data) < 2:
            break

        # copio el dataframe, pero le saco la última vela ya que no estará finalizada aún (está en proceso)
        data = data[:-1]

        data_to_insert = data_to_insert + data

        # si la lista ya acumula más de 10.000 rows, la inserto en la database h5 y la limpio para returlizarla
        # asi no sobrecargo el método write_data
        if len(data_to_insert) > 10000:
            h5_db.write_data(symbol, data_to_insert)
            data_to_insert.clear()

        # actualizo el most_recent_ts con la última data disponible para que si tiene que volver a ejecutarse
        # arranque desde acá (y suma los 60000 milisegundos arriba)
        if data[-1][0] > most_recent_ts:
            most_recent_ts = data[-1][0]

        logger.info("%s %s: Collected %s recent data from %s to %s", exchange, symbol, len(data),
                    ms_to_dt(data[0][0]), ms_to_dt(data[-1][0]))

        # espero 1.1 segundos entre cada petición del get_historical_candles, ya que sino alcanzare el rate limit de
        # Binance y me bloquea.
        time.sleep(1.1)

    # repito el proceso para que no quede ninguna data sin insertar
    h5_db.write_data(symbol, data_to_insert)
    data_to_insert.clear()

    # Older data
    # Traigo data vieja, que no preevi en los 2 métodos anteriores
    while True:
        # traigo la data desde el último timestamp + 60 segundos (* 1000 milisegundos), ya que trae timeframe 1m
        data = client.get_historical_data(symbol, end_time=int(oldest_ts - 60000))

        # Si no completa el traer toda la data (por ejemplo por un error), espero 4 segundos e intento de nuevo
        if data is None:
            time.sleep(4)
            continue

        # corto el loop del while si recolecté toda la info necesaria hasta 2 minutos atrás.
        if len(data) == 0:
            logger.info("%s %s Stopped older data collection because no data was found before %s", exchange, symbol,
                        ms_to_dt(oldest_ts))
            break

        data_to_insert = data_to_insert + data

        # si la lista ya acumula más de 10.000 rows, la inserto en la database h5 y la limpio para returlizarla
        # asi no sobrecargo el método write_data
        if len(data_to_insert) > 10000:
            h5_db.write_data(symbol, data_to_insert)
            data_to_insert.clear()

        # actualizo el most_recent_ts con la última data disponible para que si tiene que volver a ejecutarse
        # arranque desde acá (y suma los 60000 milisegundos arriba)
        if data[0][0] < oldest_ts:
            oldest_ts = data[0][0]

        logger.info("%s %s: Collected %s older data from %s to %s", exchange, symbol, len(data),
                    ms_to_dt(data[0][0]), ms_to_dt(data[-1][0]))

        # espero 1.1 segundos entre cada petición del get_historical_candles, ya que sino alcanzare el rate limit de
        # Binance y me bloquea.
        time.sleep(1.1)

    h5_db.write_data(symbol, data_to_insert)

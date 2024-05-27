import datetime
import logging
import backtester
from exchanges.binance import BinanceClient
from data_collector import collect_all
from utils import TF_EQUIV

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# formato de los mensajes de log
formatter = logging.Formatter("%(asctime)s %(levelname)s :: %(message)s")

# Para visualizar el log mientras se corre el programa
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

# Para guardar la info del log
file_handler = logging.FileHandler("info.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# agrego los handlers al log
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# si estoy llamando a main desde el programa principal (no desde un módulo):
# Ofrecemos una opción al usuario para lo que quiera hacer : traer data, hacer backtest, optimizar el algoritmo
if __name__ == "__main__":
    mode = input("Choose the program mode (data / backtest / optimize): ").lower()

    while True:
        exchange = input("Choose an exchange: ").lower()
        if exchange in ["binance"]:
            break

    if exchange == "binance":
        client = BinanceClient(True)

    while True:
        symbol = input("Choose a symbol: ").upper()
        if symbol in client.symbols:
            break

    if mode == "data":
        collect_all(client, exchange, symbol)

    elif mode == "backtest":

        # Estrategias
        # lista de estrategias disponibles para backtest

        available_strategies = ["obv", "ichimoku", "sup_res"]

        while True:
            strategy = input(f"Choose a strategy ({', '.join(available_strategies)}) : ").lower()
            if strategy in available_strategies:
                break

        # Timeframe

        while True:
            tf = input(f"Choose a timeframe ({', '.join(TF_EQUIV.keys())}) : ").lower()
            if tf in TF_EQUIV.keys():
                break

        # From time

        while True:
            # si presiona Enter, se toma como que quiere toda la data disponible
            from_time = input(f"Backtest from (yyyy-mm-dd or press Enter): ")
            if from_time == "":
                from_time = 0
                break

            try:
                from_time = int(datetime.datetime.strptime(from_time, "%Y-%m-%d").timestamp() * 1000)
                break

            except ValueError:
                continue

        # To time

        while True:
            # si presiona Enter, se toma como que quiere toda la data disponible
            to_time = input(f"Backtest to (yyyy-mm-dd or press Enter): ")
            if to_time == "":
                # paso a timestamp la fecha de hoy
                to_time = int(datetime.datetime.now().timestamp() * 1000)
                break

            try:
                # paso a timestamp
                to_time = int(datetime.datetime.strptime(to_time, "%Y-%m-%d").timestamp() * 1000)
                break

            except ValueError:
                continue

        backtester.run(exchange, symbol, strategy, tf, from_time, to_time)

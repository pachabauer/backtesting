import logging
import backtester
from exchanges.binance import BinanceClient
from data_collector import collect_all

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

        available_strategies = ["obv"]

        while True:
            strategy = input(f"Choose a strategy: ({', '.join(available_strategies)}").lower()
            if strategy in available_strategies:
                break

        # Timeframe

        while True:
            tf = input(f"Choose a timeframe: ({', '.join(TF)}").lower()
            if tf in available_strategies:
                break

        backtester.run()

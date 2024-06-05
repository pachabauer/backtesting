import datetime
import logging
import backtester
import optimizer
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

    elif mode in ["backtest", "optimize"]:

        # Estrategias
        # lista de estrategias disponibles para backtest

        available_strategies = ["obv", "ichimoku", "sup_res", "sma", "psar"]

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
            from_time = input("Backtest from (yyyy-mm-dd or Press Enter): ")
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
            to_time = input("Backtest to (yyyy-mm-dd or Press Enter): ")
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

        if mode == "backtest":
            print(backtester.run(exchange, symbol, strategy, tf, from_time, to_time))

        elif mode == "optimize":
            # Population Size
            # qué tamaño va a tener la muestra para generar optimizaciones

            while True:
                try:
                    pop_size = int(input(f"Choose a population size: "))
                    break
                except ValueError:
                    continue

            # Iterations
            # la cantidad de optimizaciones que queremos hacer.

            while True:
                try:
                    generations = int(input(f"Choose a number of generations: "))
                    break
                except ValueError:
                    continue

            nsga2 = optimizer.Nsga2(exchange, symbol, strategy, tf, from_time, to_time, pop_size)

            # cambio los nombres de variables y los adapto de acuerdo al paper del nsga2
            # p , q , r
            p_population = nsga2.create_initial_population()
            p_population = nsga2.evaluate_population(p_population)
            p_population = nsga2.crowding_distance(p_population)

            g = 0
            while g < generations:

                q_population = nsga2.create_offspring_population(p_population)
                q_population = nsga2.evaluate_population(q_population)

                r_population = p_population + q_population

                nsga2.population_params.clear()

                # va a ir recorriendo cada backtest (individuo) y guardar sus id para luego compararlos en el método
                # non_dominated_sorting() y poder ir determinando quién domina a quien.
                i = 0
                population = dict()
                for bt in r_population:
                    bt.reset_results()
                    nsga2.population_params.append(bt.parameters)
                    population[i] = bt
                    i += 1

                fronts = nsga2.non_dominated_sorting(population)

                # arranca el loop para conformar la población nueva y optimizada
                for j in range(len(fronts)):
                    fronts[j] = nsga2.crowding_distance(fronts[j])

                p_population = nsga2.create_new_population(fronts)

                print(f"\r{int((g + 1) / generations * 100)}%", end='')

                g += 1

            print("\n")

            for individual in p_population:
                print(individual)


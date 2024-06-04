import copy
import random
import typing

import strategies.obv
import strategies.ichimoku
import strategies.support_resistance

from models import BacktestResult
from utils import STRAT_PARAMS, resample_timeframe, get_library
from database import Hdf5Client


# Es la clase que optimiza el backtest
class Nsga2:
    def __init__(self, exchange: str, symbol: str, strategy: str, tf: str, from_time: int, to_time: int,
                 population_size: int):
        self.exchange = exchange
        self.symbol = symbol
        self.strategy = strategy
        self.tf = tf
        self.from_time = from_time
        self.to_time = to_time
        self.population_size = population_size

        self.population_params = []

        # toma los parámetros de la estrategia que seleccionemos para optimizar
        self.params_data = STRAT_PARAMS[strategy]

        # si la estrategia la hicimos en Python:
        if self.strategy in ["obv", "ichimoku", "sup_res"]:
            h5_db = Hdf5Client(exchange)
            self.data = h5_db.get_data(symbol, from_time, to_time)
            self.data = resample_timeframe(self.data, tf)

        # si la estrategia la hicimos en C++:
        elif self.strategy in ["sma", "psar"]:

            self.lib = get_library()

            if self.strategy == "sma":
                self.obj = self.lib.Sma_new(exchange.encode(), symbol.encode(), tf.encode(), from_time, to_time)
            elif self.strategy == "psar":
                self.obj = self.lib.Psar_new(exchange.encode(), symbol.encode(), tf.encode(), from_time, to_time)

    # Armo la población inicial que conformará los "individuos" (backtest) para ir optimizando.
    def create_initial_population(self) -> typing.List[BacktestResult]:

        population = []

        while len(population) < self.population_size:
            backtest = BacktestResult()
            for p_code, p in self.params_data.items():
                if p['type'] == int:
                    backtest.parameters[p_code] = random.randint(p["min"], p["max"])
                elif p['type'] == float:
                    backtest.parameters[p_code] = round(random.uniform(p["min"], p["max"]), p["decimals"])

            # si no se encuentra aún en la lista, la agrego
            if backtest not in population:
                population.append(backtest)
                self.population_params.append(backtest.parameters)

        return population

    # esta función realiza el proceso de reproducción de los individuos. Se elijen 2 parents y se van cruzando
    # sus mejores parámetros a fin de ir logrando individuos mejores, hasta seleccionar los más aptos.
    def create_offspring_population(self, population: typing.List[BacktestResult]) -> typing.List[BacktestResult]:

        offspring_pop = []

        # La population del offspring tiene que ser igual a la population size (Pt = Qt)
        while len(offspring_pop) != self.population_size:

            parents: typing.List[BacktestResult] = []

            # Se itera 2 veces para cruzar 2 parents y salga 1 child
            for i in range(2):
                # toma una muestra aleatoria de 2 parents
                random_parents = random.sample(population, k=2)
                if random_parents[0].rank != random_parents[1].rank:
                    # toma al mejor parent para generar el child
                    best_parent = min(random_parents, key=lambda x:getattr(x, "rank"))
                else:
                    best_parent = max(random_parents, key=lambda x:getattr(x, "crowding_distance"))

                parents.append(best_parent)

            new_child = BacktestResult()
            # los parámetros son, por ejemplo, el int pasado a una media movil (6, 21, etc)
            new_child.parameters = copy.copy(parents[0].parameters)

            # Crossover: se hace el cruce "genético" de parámetros

            # cantidad de parámetros
            number_of_crossovers = random.randint(1, len(self.params_data))
            # parámetros seleccionados que voy a cruzar
            params_to_cross = random.sample(list(self.params_data.keys()), k=number_of_crossovers)

            # el child viene con un parámetros seleccionado del primer parent (parent[0] y uno seleccionado random
            # del segundo parent[1] que se asigna en el loop
            for p in params_to_cross:
                new_child.parameters[p] = copy.copy(parents[1].parameters[p])

            # Mutation : modifica "levemente" los valores de los parámetros del child al azar (por ejemplo una media
            # de 10 la incrementa un 20% , a 12... y así
            # cantidad de mutaciones
            number_of_mutations = random.randint(0, len(self.params_data))
            # parámetros seleccionados que voy a cruzar
            params_to_change = random.sample(list(self.params_data.keys()), k=number_of_mutations)

            for p in params_to_change:
                # "la fuerza" de mutación la establecemos entre -200 y 200 %
                mutation_strength = random.uniform(-2, 2)
                # el self.params_data convierte a tipo int y el new_child adopta el parámetro "modificado"
                # tener en cuenta que esto puede ser mayor al máximo o menor al mínimo que especificamos
                # por ende adoptará el valor max o mín de él mismo o el establecido en su clase
                new_child.parameters[p] = self.params_data[p]["type"](new_child.parameters[p] * (1 + mutation_strength))
                new_child.parameters[p] = max(new_child.parameters[p], self.params_data[p]['min'])
                new_child.parameters[p] = min(new_child.parameters[p], self.params_data[p]['max'])

                # si el self.params_data es un float
                if self.params_data[p]["type"] == float:
                    new_child.parameters[p] = round(new_child.parameters[p], self.params_data[p]["decimals"])

            if new_child.parameters not in self.population_params:
                offspring_pop.append(new_child)
                self.population_params.append(new_child.parameters)

        return offspring_pop



    # Esta función permite medir la distancia entre 2 individuos de la misma Frontera. A mayor distancia, mayor
    # diversidad tienen, lo cual es mejor, mientras que una menor distancia hace que los 2 individuos sean similares,
    # lo cual no viene a aportar a la búsqueda de una mejor diversidad de individuos para considerar el armado y
    # selección de muestras para la optimización genética.
    def crowding_distance(self, population: typing.List[BacktestResult]) -> typing.List[BacktestResult]:

        # voy a tener que seleccionar 1 objetivo de cada individuo para medirlo respecto de otros
        for objective in ["pnl", "max_dd"]:

            # cada x es un objeto de la clase BacktestResult y el objective es el pnl o max_dd
            population = sorted(population, key=lambda x: getattr(x, objective))
            # toma el valor mínimo y máximo de cada objective que elijamos.
            min_value = getattr(min(population, key=lambda x: getattr(x, objective)), objective)
            max_value = getattr(max(population, key=lambda x: getattr(x, objective)), objective)

            # asigno valores infinitos al primer y último individuo ya que será el mejor y el peor, con lo cual no
            # puede medir de nadie. Son los otros los que miden contra ellos.
            population[0].crowding_distance = float("inf")
            population[-1].crowding_distance = float("inf")

            # itero por cada individuo (salvo el primero y último) y mido la distancia entre sus objetivos
            # limito el rango de distancia entre su valor máximo y minimo
            # asigno la distancia al individuo
            for i in range(1, len(population) - 1):
                distance = getattr(population[i + 1], objective) - getattr(population[i - 1], objective)
                distance = distance / (max_value - min_value)
                population[i].crowding_distance += distance

        return population

    # Es la función que irá comparando 1 individuo con otro y en base a sus funciones objetivo (pnl y max_dd)
    # los irá ordenando en las F1, F2 (fronteras) Eso hará que haya dominantes y dominados, a fin de generar los mejores
    # individuos (backtest) que será la base de la optimización.
    def non_dominated_sorting(self, population: typing.Dict[int, BacktestResult]) -> typing.List[
        typing.List[BacktestResult]]:

        fronts = []

        for id_1, indiv_1 in population.items():
            for id_2, indiv_2 in population.items():
                if indiv_1.pnl >= indiv_2.pnl and indiv_1.max_dd <= indiv_2.max_dd \
                        and (indiv_1.pnl > indiv_2.pnl or indiv_1.max_dd < indiv_2.max_dd):
                    indiv_1.dominates.append(id_2)
                elif indiv_2.pnl >= indiv_1.pnl and indiv_2.max_dd <= indiv_1.max_dd \
                        and (indiv_2.pnl > indiv_1.pnl or indiv_2.max_dd < indiv_1.max_dd):
                    indiv_1.dominated_by += 1

            # Si el dominated_by == 0 quiere decir que pertenece al F1, la mejor frontera
            # lo agrego a la lista de la frontera
            # también agrego al mejor rank (en este caso 0 por ser F1, si fuera F2 sería 1 y así...)
            if indiv_1.dominated_by == 0:
                if len(fronts) == 0:
                    fronts.append([])
                fronts[0].append(indiv_1)
                indiv_1.rank = 0

        i = 0

        # loop para incorporar el resto de backtests (individuos) y asignarlos a cada Frontera que corresponda
        # así sugiere el paper de nsga2, ir iterando en el loop para agregar al resto de individuos a fronteras
        while True:
            fronts.append([])

            # traigo los individuos que dominan
            for indiv_1 in fronts[i]:
                # de esos individuos que dominan, tomo el id y lo uso para comparar con los indiv_2 que van a ir a la F1
                for indiv_2_id in indiv_1.dominates:
                    # determino cuántos eran los anteriores y los resto , cuando equivale a 0 lo agrego a la lista F2
                    # y le asigno el rank = 1 (F1 es = 0)
                    population[indiv_2_id].dominated_by -= 1
                    if population[indiv_2_id].dominated_by == 0:
                        fronts[i + 1].append(population[indiv_2_id])
                        population[indiv_2_id].rank = i + 1

            # chequeo si la frontera está vacía o no, si no está vacía incremento para seguir el loop, sino rompo
            if len(fronts[i + 1]) > 0:
                i += 1
            else:
                # borro la lista y rompo el loop si ya no quedan mas individuos (backtest) por evaluar y asignar
                del fronts[-1]
                break

        return fronts

    # va a evaluar cada backtest (individuo) y asignar el pnl y max_dd que corresponda
    def evaluate_population(self, population: typing.List[BacktestResult]) -> typing.List[BacktestResult]:

        if self.strategy == "obv":

            for bt in population:
                bt.pnl, bt.max_dd = strategies.obv.backtest(self.data, ma_period=bt.parameters['ma_period'])

            return population

        elif self.strategy == "ichimoku":

            for bt in population:
                bt.pnl, bt.max_dd = strategies.ichimoku.backtest(self.data, tenkan_period=bt.parameters['tenkan'],
                                                                 kijun_period=bt.parameters['kijun'])

            return population

        elif self.strategy == "sup_res":

            for bt in population:
                bt.pnl, bt.max_dd = strategies.support_resistance.backtest(self.data,
                                                                           min_points=bt.parameters['min_points'],
                                                                           min_diff_points=bt.parameters[
                                                                               'min_diff_points'],
                                                                           rounding_nb=bt.parameters['rounding_nb'],
                                                                           take_profit=bt.parameters['take_profit'],
                                                                           stop_loss=bt.parameters['stop_loss'])

            return population

        elif self.strategy == "sma":
            for bt in population:
                self.lib.Sma_execute_backtest(self.obj, bt.parameters['slow_ma'], bt.parameters['fast_ma'])
                bt.pnl = self.lib.Sma_get_pnl(self.obj)
                bt.max_dd = self.lib.Sma_get_max_dd(self.obj)

            return population

        elif self.strategy == "psar":
            for bt in population:
                self.lib.Psar_execute_backtest(self.obj, bt.parameters['initial_acc'],
                                               bt.parameters['acc_increment'], bt.parameters['max_acc'])
                bt.pnl = self.lib.Psar_get_pnl(self.obj)
                bt.max_dd = self.lib.Psar_get_max_dd(self.obj)

            return population

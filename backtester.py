from ctypes import *
from database import Hdf5Client
from utils import resample_timeframe, STRAT_PARAMS, get_library
import strategies.obv
import strategies.ichimoku
import strategies.support_resistance


# el método que ejecutará la corrida del backtest.
# los time son int porque son timestamp
def run(exchange: str, symbol: str, strategy: str, tf: str, from_time: int, to_time: int):
    # descripción de los parámetros de cada estrategia que se traen de Utils
    params_des = STRAT_PARAMS[strategy]

    params = dict()

    # p_code son los parámetros de cada estrategia y p es el diccionario que tiene dentro cada parámetro
    for p_code, p in params_des.items():
        while True:
            try:
                params[p_code] = p['type'](input(p['name'] + ": "))
                break
            except ValueError:
                continue

    if strategy == "obv":
        h5_db = Hdf5Client(exchange)
        data = h5_db.get_data(symbol, from_time, to_time)
        data = resample_timeframe(data, tf)

        pnl, max_drawdown = strategies.obv.backtest(data, ma_period=params['ma_period'])

        return pnl, max_drawdown

    elif strategy == "ichimoku":
        h5_db = Hdf5Client(exchange)
        data = h5_db.get_data(symbol, from_time, to_time)
        data = resample_timeframe(data, tf)

        pnl, max_drawdown = strategies.ichimoku.backtest(data, tenkan_period=params['tenkan'],
                                                         kijun_period=params['kijun'])

        return pnl, max_drawdown

    # estrategia soporte y resistencia
    elif strategy == "sup_res":
        h5_db = Hdf5Client(exchange)
        data = h5_db.get_data(symbol, from_time, to_time)
        data = resample_timeframe(data, tf)

        pnl, max_drawdown = strategies.support_resistance.backtest(data, min_points=params['min_points'],
                                                                   min_diff_points=params['min_diff_points'],
                                                                   rounding_nb=params['rounding_nb'],
                                                                   take_profit=params['take_profit'],
                                                                   stop_loss=params['stop_loss'])

        return pnl, max_drawdown

    # comienzo a cargar estrategias hechas en C++ (VSCODE), para ello importo librería ctypes
    # SIEMPRE indicar los restype y argtypes, ya que sino la librería funcionará mal
    elif strategy == "sma":
        # indico el path de la librería e indico winmode=0 , ya que sino la librería no se encontrará
        lib = get_library()

        # instanciamos la clase para pasar los métodos
        # a cada parámetro debo pasarlo como string compatible con C, por ello el encode()
        obj = lib.Sma_new(exchange.encode(), symbol.encode(), tf.encode(), from_time, to_time)
        lib.Sma_execute_backtest(obj, params['slow_ma'], params['fast_ma'])
        pnl = lib.Sma_get_pnl(obj)
        max_drawdown = lib.Sma_get_max_dd(obj)

        return pnl, max_drawdown

    elif strategy == "psar":
        lib = get_library()

        obj = lib.Psar_new(exchange.encode(), symbol.encode(), tf.encode(), from_time, to_time)
        lib.Psar_execute_backtest(obj, params['initial_acc'], params['acc_increment'], params['max_acc'])
        pnl = lib.Psar_get_pnl(obj)
        max_drawdown = lib.Psar_get_max_dd(obj)

        return pnl, max_drawdown





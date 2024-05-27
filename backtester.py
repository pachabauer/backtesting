from database import Hdf5Client
from utils import resample_timeframe, STRAT_PARAMS
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

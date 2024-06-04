import datetime
from ctypes import *

import pandas as pd

# constante global con las equivalencias del tf del exchange con como lo toma la función resample() de pandas
TF_EQUIV = {'1m': '1Min', '5m': '5Min', '15m': '15Min', '30m': '30Min', '1h': '1H', '4h': '4H', '12h': '12H', '1d': 'D'}

# constante que almacena los inputs de las estrategias que se irán completando en forma dinámica (en vez de hardcodear
# valores, los ingresaré como inputs en la pantalla
# establezco valores límite mínimos y máximos para los parámetros para luego usarlos en el random generador
# del optimizer y no tener cualquier número en el random (por ejemplo 1.000.000.000, que no serviría de nada)
STRAT_PARAMS = {
    "obv": {
        "ma_period": {"name": "MA Period", "type": int, "min": 2, "max": 200},
    },
    "ichimoku": {
        "kijun": {"name": "Kijun Period", "type": int, "min": 2, "max": 200},
        "tenkan": {"name": "Tenkan Period", "type": int, "min": 2, "max": 200},
    },
    "sup_res": {
        "min_points": {"name": "Min points to generate sup or res", "type": int, "min": 2, "max": 20},
        "min_diff_points": {"name": "Min. difference between points", "type": int, "min": 2, "max": 100},
        "rounding_nb": {"name": "Rounding number", "type": float, "min": 10, "max": 500, "decimals": 2},
        "take_profit": {"name": "Take profit %", "type": float, "min": 1, "max": 40, "decimals": 2},
        "stop_loss": {"name": "Stop loss %", "type": float, "min": 1, "max": 40, "decimals": 2},
    },
    "sma": {
        "slow_ma": {"name": "Slow MA Period", "type": int, "min": 2, "max": 200},
        "fast_ma": {"name": "Fast MA Period", "type": int, "min": 2, "max": 200},
    },
    "psar": {
        "initial_acc": {"name": "Initial Acceleration", "type": float, "min": 0.01, "max": 0.2, "decimals": 2},
        "acc_increment": {"name": "Acceleration increment", "type": float, "min": 0.01, "max": 0.3, "decimals": 2},
        "max_acc": {"name": "Max. Acceleration", "type": float, "min": 0.05, "max": 1, "decimals": 2},
    },
}


# función para convertir de milisegundos a datetime y que sea legible los logs o información
def ms_to_dt(ms: int) -> datetime.datetime:
    return datetime.datetime.utcfromtimestamp(ms / 1000)


# función para convertir los tf de 1 minuto del programa, al tf que queramos (5, 15, 30 min, etc)
def resample_timeframe(data: pd.DataFrame, tf: str) -> pd.DataFrame:
    # resample el timeframe
    return data.resample(TF_EQUIV[tf]).agg(
        # explicamos al aggregate las columnas del dataframe
        {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}
    )


# función para hacer un get de la librería de C++ para usarla en Python
def get_library():
    # SMA
    # indico el path de la librería e indico winmode=0 , ya que sino la librería no se encontrará
    lib = CDLL("backtestingCpp/build/libbacktestingCpp.dll", winmode=0)
    # indico el tipo de return de la clase, en este caso void (VSCODE)
    lib.Sma_new.restype = c_void_p
    # indico el tipo de los argumentos de Sma_new
    lib.Sma_new.argtypes = [c_char_p, c_char_p, c_char_p, c_longlong, c_longlong]
    # indico el tipo de return de la clase, en este caso void (VSCODE)
    lib.Sma_execute_backtest.restype = c_void_p
    # indico el tipo de los argumentos de Sma_execute_backtest (pero el primer argumento debe ser el pointer a la
    # clase Sma_new que es la que lo origina
    lib.Sma_execute_backtest.argtypes = [c_void_p, c_int, c_int]

    # indico lo mismo para los 2 métodos restantes
    lib.Sma_get_pnl.restype = c_double
    lib.Sma_get_pnl.argtypes = [c_void_p]
    lib.Sma_get_max_dd.restype = c_double
    lib.Sma_get_max_dd.argtypes = [c_void_p]

    # PSAR

    lib.Psar_new.restype = c_void_p
    lib.Psar_new.argtypes = [c_char_p, c_char_p, c_char_p, c_longlong, c_longlong]
    lib.Psar_execute_backtest.restype = c_void_p
    lib.Psar_execute_backtest.argtypes = [c_void_p, c_double, c_double, c_double]

    lib.Psar_get_pnl.restype = c_double
    lib.Psar_get_pnl.argtypes = [c_void_p]
    lib.Psar_get_max_dd.restype = c_double
    lib.Psar_get_max_dd.argtypes = [c_void_p]

    return lib

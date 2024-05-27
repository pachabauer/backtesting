import datetime
import pandas as pd

# constante global con las equivalencias del tf del exchange con como lo toma la función resample() de pandas
TF_EQUIV = {'1m': '1Min', '5m': '5Min', '15m': '15Min', '30m': '30Min', '1h': '1H', '4h': '4H', '12h': '12H', '1d': 'D'}

# constante que almacena los inputs de las estrategias que se irán completando en forma dinámica (en vez de hardcodear
# valores, los ingresaré como inputs en la pantalla
STRAT_PARAMS = {
    "obv": {
        "ma_period": {"name": "MA Period", "type": int},
    },
    "ichimoku": {
        "kijun": {"name": "Kijun Period", "type": int},
        "tenkan": {"name": "Tenkan Period", "type": int},
    },
    "sup_res": {
        "min_points": {"name": "Min points to generate sup or res", "type": int},
        "min_diff_points": {"name": "Min. difference between points", "type": int},
        "rounding_nb": {"name": "Rounding number", "type": float},
        "take_profit": {"name": "Take profit %", "type": float},
        "stop_loss": {"name": "Stop loss %", "type": float},
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

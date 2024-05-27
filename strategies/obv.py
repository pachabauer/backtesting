# estrategia obv
# https://www.tradingview.com/scripts/onbalancevolume/

import pandas as pd
import numpy as np

# seteos para ver todas las columnas del df con un ancho correcto
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)

def backtest(df: pd.DataFrame, ma_period: int):

    # comienzo calculando la diferencia entre cada close price
    # lo asigno al sing de numpy, lo que traerá el signo (+1 ,  -1 o 0)
    # a su vez limpio el df de Nan
    # siguiente uso el cumsum() para ir acumulando el valor, así funciona el obv
    df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()

    # ahora calculo la columna del moving average
    # uso la funcion rolling para ello (cantidad de periodos que debo tomar para el calculo) y le calculo el promedio
    df['obv_ma'] = round(df['obv'].rolling(window=ma_period).mean(), 2)

    # genero la señal, que será 1 si es long o -1 si es short
    df['signal'] = np.where(df['obv'] > df['obv_ma'], 1, -1)

    # para calcular el pnl, EXPLICACION:
    # supongamos que en la row -1 (anterior a la actual) se da una señal de short -1
    # el close -1 era de 55519 y el actual 55478, la diferencia porcentual sería de -0.7%
    # al multiplicar ese cambio por la signal shift(1) (el shift indica que la subo 1, es decir voy al close -1
    # eso hace que el -0,7% pase a ser 0,7 (ya que multiplico por la señal short -1) entonces, el pnl será de 0,7%
    df['pnl'] = df['close'].pct_change() * df['signal'].shift(1)

    # Max Drawdown
    df['cum_pnl'] = df['pnl'].cumsum()
    df['max_cum_pnl'] = df['cum_pnl'].cummax()
    df['drawdown'] = df['max_cum_pnl'] - df['cum_pnl']


    # retorno la sumatoria del pnl total en PORCENTAJE de la estrategia
    return df['pnl'].sum(), df['drawdown'].max()
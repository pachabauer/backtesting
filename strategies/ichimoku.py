# estrategia ichimoku
# https://school.stockcharts.com/doku.php?id=trading_strategies:ichimoku_cloud

import pandas as pd
import numpy as np

# seteos para ver todas las columnas del df con un ancho correcto
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)


# en la estrategía original, con esos 2 parámetros obtengo los otros que conforman el indicador, pero si quiero
# personalizarlo, debería cambiar la estrategia y pasar más parámetros.
def backtest(df_original: pd.DataFrame, tenkan_period: int, kijun_period: int):

    # modifico porque se usa en otros backtest y es necesario mantener inalterado el df_original
    df = df_original.copy()
    # Tenkan Sen: short-term signal line

    # rolling hace que se tome varias rows (el período, definido en window=) y calcular algo: minimo, maximo, etc
    # acá saco el mínimo del período y el máximo del período
    df['rolling_min_tenkan'] = df['low'].rolling(window=tenkan_period).min()
    df['rolling_max_tenkan'] = df['high'].rolling(window=tenkan_period).max()

    # el tenkan_sen es el promedio del max y el min
    df['tenkan_sen'] = (df['rolling_max_tenkan'] + df['rolling_min_tenkan']) / 2

    # ya no necesitamos más las 2 columnas , las borro del df (se podría debuggear para ver como se forman)
    df.drop(['rolling_min_tenkan', 'rolling_max_tenkan'], axis=1, inplace=True)

    # Kijun Sen: long-term signal line

    df['rolling_min_kijun'] = df['low'].rolling(window=kijun_period).min()
    df['rolling_max_kijun'] = df['high'].rolling(window=kijun_period).max()

    # el tenkan_sen es el promedio del max y el min
    df['kijun_sen'] = (df['rolling_max_kijun'] + df['rolling_min_kijun']) / 2

    # ya no necesitamos más las 2 columnas , las borro del df (se podría debuggear para ver como se forman)
    df.drop(['rolling_min_kijun', 'rolling_max_kijun'], axis=1, inplace=True)

    # Senkou Span A
    # es el promedio de la tenkan_sen y la kijun_sen y lo proyectamos Y períodos adelante (como un predictor)
    # en este caso tomará el valor de la kijun_period
    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(kijun_period)

    # Senkou Span B
    df['rolling_min_senkou'] = df['low'].rolling(window=kijun_period * 2).min()
    df['rolling_max_senkou'] = df['high'].rolling(window=kijun_period * 2).max()

    # el senkou_span_b es el promedio del max y el min proyectado y periodos adelante (como predictor)
    df['senkou_span_b'] = ((df['rolling_max_senkou'] + df['rolling_min_senkou']) / 2).shift(kijun_period)

    # ya no necesitamos más las 2 columnas , las borro del df (se podría debuggear para ver como se forman)
    df.drop(['rolling_min_senkou', 'rolling_max_senkou'], axis=1, inplace=True)

    # Chikou Span: Es la línea de confirmación
    df['chikou_span'] = df['close'].shift(kijun_period)

    df.dropna(inplace=True)

    # Señal Tenkan - Kijun (corta para arriba o para abajo)

    df['tenkan_minus_kijun'] = df['tenkan_sen'] - df['kijun_sen']
    df['previous_tenkan_minus_kijun'] = df['tenkan_minus_kijun'].shift(1)

    # Si todas estas condiciones son True, marco un 1 que es un long, si se cumplen las siguientes será un -1, short
    # y si no se cumplen, 0: nada
    df['signal'] = np.where((df['tenkan_minus_kijun'] > 0) & (df['previous_tenkan_minus_kijun'] < 0)
                            & (df['close'] > df['senkou_span_a']) & (df['close'] > df['senkou_span_b'])
                            & (df['close'] > df['chikou_span']), 1,

                            np.where((df['tenkan_minus_kijun'] < 0) & (df['previous_tenkan_minus_kijun'] > 0)
                            & (df['close'] < df['senkou_span_a']) & (df['close'] < df['senkou_span_b'])
                            & (df['close'] < df['chikou_span']), -1, 0))


    # armo un df solo con los 1 y -1 que son las señales long y short
    df = df[df['signal'] != 0].copy()
    # calculo la columna pnl del df de signal_data y pongo shift(1) para que calcule el precio de entrada
    # (que es el shift(1)) y el precio de salida (que es el close)
    df['pnl'] = df['close'].pct_change() * df['signal'].shift(1)

    # Max Drawdown
    df['cum_pnl'] = df['pnl'].cumsum()
    df['max_cum_pnl'] = df['cum_pnl'].cummax()
    df['drawdown'] = df['max_cum_pnl'] - df['cum_pnl']

    return df['pnl'].sum(), df['drawdown'].max()

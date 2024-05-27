# estrategia soporte y resistencia
# Clase 27 curso backtesting Vincent Cormier
import time

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf

# seteos para ver todas las columnas del df con un ancho correcto
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", 1000)


# en la estrategía original, con esos 2 parámetros obtengo los otros que conforman el indicador, pero si quiero
# personalizarlo, debería cambiar la estrategia y pasar más parámetros.
# min_points se refiere a la cantidad mínima de veces que tiene que tocar un valor para ser considerado
# soporte o resistencia (idealmente 3 cómo mínimo)
# min_difference_points se refiere a la cantidad de velas que debe de haber de diferencia entre
# un punto y el otro, ya que si se tocan 3 veces pero son 3 velas consecutivas, el soporte o resistencia
# no es tan confiable como si se tocan con un tiempo espaciado, por ejemplo una diferencia de 7, 10 velas.
# rounding_nb se refiere a que valor vamos a redondear (por ejemplo un soporte de 1000, si las velas tocan 998, 1002,
# 1001, 999, etc... todos van a ser 1000)
def backtest(df: pd.DataFrame, min_points: int, min_diff_points: int, rounding_nb: float, take_profit: float,
             stop_loss: float):

    # el tamaño de la vela
    candle_length = df.iloc[1].name - df.iloc[0].name

    pnl = 0
    max_pnl = 0

    # 0 no posicion, 1 long, -1 short
    trade_side = 0
    entry_price = None

    max_drawdown = 0

    df['rounded_high'] = round(df['high'] / rounding_nb) * rounding_nb
    df['rounded_low'] = round(df['low'] / rounding_nb) * rounding_nb

    # almacena un diccionario de precios redondeados de soportes y resistencias.
    prices_group = {"supports": dict(), "resistances": dict()}
    # uso levels para graficar los soportes y resistencias con el paquete mplfinance
    levels = {"supports": [], "resistances": []}
    # Uso last_h_l para guardar los últimos 10 candles y si éstas rompen un soporte o resistencia más de x veces,
    # no guardaré ese soporte o resistencia en el prices_group
    last_h_l = {"supports": [], "resistances": []}
    resistances_supports = {"supports": [], "resistances": []}

    # Convierto los dataframe que necesito a Numpy Arrays para mayor velocidad de backtesting
    highs = np.array(df['high'])
    lows = np.array(df['low'])
    rounded_highs = np.array(df['rounded_high'])
    rounded_lows = np.array(df['rounded_low'])
    closes = np.array(df['close'])
    times = np.array(df.index)

    row = {'high': highs, 'low': lows, 'rounded_high': rounded_highs, 'rounded_low': rounded_lows, 'close': closes}

    # recorro el loop para ir encontrardo soportes y resistencias (fila por fila) y chequear si los mismos no son
    # rotos por precios superiores o inferiores, haciendo inválidos los soportes y resistencias a futuro)
    for i in range(len(highs)):

        index = times[i]

        for side in ['resistances', 'supports']:
            h_l = "high" if side == "resistances" else "low"

            # si la fila del loop encuentra que el soporte o resistencia (rounded_high o rounded_low) está en el dict
            # entonces no hace nada, ya existe el soporte o resistencia, sino lo agrega
            if row['rounded_' + h_l][i] in prices_group[side]:

                # group
                grp = prices_group[side][row['rounded_' + h_l][i]]
                # guardo cuántas veces se rompe un soporte o resistencia
                broken_in_last = 0

                if grp['start_time'] is None:

                    for c in last_h_l[side]:
                        if c > row[h_l][i] and side == "resistances":
                            broken_in_last += 1
                        elif c < row[h_l][i] and side == "supports":
                            broken_in_last += 1

                    if broken_in_last < 3:
                        grp['start_time'] = index

                # acá calcula que si el índice (el timestamp) es mayor a el último timestamp + mas las velas de
                # diferencia que tiene que haber para que se cumpla que puedo agregar otro soporte o resistencia
                # el tamaño de la vela, ahi agrego al nivel, el precio
                if broken_in_last < 3 and (grp['last'] is None or index >= grp['last'] +
                                           min_diff_points * candle_length):

                    grp['prices'].append(row[h_l][i])

                    # si tengo más de los puntos minimos necesarios, ahí podré tener un soporte o resistencia
                    if len(grp['prices']) >= min_points:
                        # otro chequeo es si el soporte o resistencia se rompio o no, haciéndolo válido o no.
                        extreme_price = max(grp['prices']) if side == "resistances" else min(grp['prices'])
                        # defino el start_time y el end_time (que va a ser el index actual) y 2 veces el extreme price
                        # porque queremos una linea horizontal (soporte o resistencia)
                        levels[side].append([(grp['start_time'], extreme_price), (index, extreme_price)])
                        resistances_supports[side].append({'price': extreme_price, 'broken': False})

                    grp['last'] = index

            else:
                # guardo cuántas veces se rompe un soporte o resistencia
                broken_in_last = 0

                for c in last_h_l[side]:
                    if c > row[h_l][i] and side == "resistances":
                        broken_in_last += 1
                    elif c < row[h_l][i] and side == "supports":
                        broken_in_last += 1

                if broken_in_last < 3:
                    # es medio complejo, pero: lo que quiero guardar acá es una lista de los máximos que pertenecen
                    # al nivel (grupo) de resistencia. Es decir, una zona de resistencia que tiene varios valores
                    # agregaré el valor, el start time y el last time (en este caso iguales, pero en la parte del if,
                    # cuando ya existe el nivel, updateo el last
                    prices_group[side][row['rounded_' + h_l][i]] = {'prices': [row[h_l][i]], 'start_time': index,
                                                                    'last': index}

            # Check si el soporte o resistencia dentro de prices_group sigue o no siendo válido (si lo rompió un precio
            # ya no es más válido)
            for key, value in prices_group[side].items():
                if len(value['prices']) > 0:
                    # si es resistencia y el precio rompe para arriba, no sirve más como resistencia y habilita long
                    if side == "resistances" and row[h_l][i] > max(value['prices']):
                        value['prices'].clear()
                        value['start_time'] = None
                        value['last'] = None
                    if side == "supports" and row[h_l][i] < min(value['prices']):
                        value['prices'].clear()
                        value['start_time'] = None
                        value['last'] = None

            last_h_l[side].append(row[h_l][i])
            if len(last_h_l[side]) > 10:
                last_h_l[side].pop(0)

            # Chequeo si se ejecuta un nuevo trade
            for sup_res in resistances_supports[side]:
                # booleano que chequea si el precio de cierre rompe una resistencia o soporte
                entry_condition = row['close'][i] > sup_res['price'] if side == "resistances" else \
                    row['close'][i] < sup_res['price']

                if entry_condition and not sup_res['broken']:
                    sup_res['broken'] = True
                    if trade_side == 0:
                        entry_price = row['close'][i]
                        trade_side = 1 if side == "resistances" else -1

            # Chequeo PNL
            # Long
            if trade_side == 1:
                if row['close'][i] >= entry_price * (1 + take_profit / 100) or row['close'][i] <= entry_price * (
                        1 - stop_loss / 100):
                    pnl += (row['close'][i] / entry_price - 1 * 100)
                    trade_side = 0
                    entry_price = None
            # Sort
            elif trade_side == -1:
                if row['close'][i] <= entry_price * (1 - take_profit / 100) or row['close'][i] >= entry_price * (
                        1 + stop_loss / 100):
                    pnl += (entry_price / row['close'][i] - 1 * 100)
                    trade_side = 0
                    entry_price = None

            max_pnl = max(max_pnl, pnl)
            max_drawdown = max(max_drawdown, max_pnl - pnl)

    # ver documentación de mdf, que es un matplotlib para finanzas
    # https://github.com/matplotlib/mplfinance
    # mpf.plot(df, type="candle", style="charles", alines=dict(alines=levels['resistances'] + levels['supports']))
    # plt.show()

    return pnl, max_drawdown

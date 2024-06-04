#include <numeric>
#include "Psar.h"
#include "../Database.h"
#include "../Utils.h"

/* Uso el DLLEXPORT para Windows nomás, para enviar el programa a algo externo*/
#define DLLEXPORT extern "C" __declspec(dllexport) 

using namespace std;

Psar::Psar(char* exchange_c, char* symbol_c, char* timeframe_c, long long from_time, long long to_time)
{
    exchange = exchange_c;
    symbol = symbol_c;
    timeframe = timeframe_c;

    Database db(exchange);
    int array_size = 0;
    double** res = db.get_data(symbol, exchange, array_size);
    db.close_file();
    std::tie(ts, open, high, low, close, volume) = rearrange_candles(res, timeframe, from_time, to_time, array_size);
}

void Psar::execute_backtest(double initial_acc, double acc_increment, double max_acc)
{
    /* defino las variables que me ayudan a calcular el pnl y el drawdown para la estrategia*/
    pnl = 0.0;
    max_dd = 0.0;

    double max_pnl = 0.0;
    int current_position = 0;
    double entry_price;

    /* defino otras variables específicas del indicador
    llevan un [2] porque indican que guardarán 2 valores
    trend lleva la tendencia 1 y -1, siendo long o short respectivamente
    sar es el valor del indicador
    ep es el extreme point
    af es el factor de aceleración*/

    int trend[2] = {0, 0};
    double sar[2] = {0.0, 0.0};
    double ep[2] = {0.0, 0.0};
    double af[2] = {0.0, 0.0};
    double temp_sar = 0.0;

    /* defino los valores iniciales de algunas variables
    con inline if*/

    trend[0] = close[1] > close[0] ? 1 : -1;
    sar[0] = trend[0] > 0 ? high[0] : low[0];
    ep[0] = trend[0] > 0 ? high[1] : low[1];
    af[0] = initial_acc;

    /* comienzo a iterar por las velas y calcular el Parabolic Sar*/

    for (int i = 2; i < ts.size(); i++)
    {

        // Trend

        temp_sar = sar[0] + af[0] * (ep[0] - sar[0]);

        // Downtrend
        if (trend[0] < 0)
        {

            if (trend[0] <= -2)
            {
                temp_sar = max(temp_sar, max(high[i - 1], high[i - 2]));
            }
            trend[1] = temp_sar < high[i] ? 1 : trend[0] - 1;
        }

        // Uptrend
        else
        {

            if (trend[0] >= 2)
            {
                temp_sar = min(temp_sar, min(low[i - 1], low[i - 2]));
            }
            trend[1] = temp_sar > low[i] ? -1 : trend[0] + 1;
        }

        // Extreme Point

        if (trend[1] < 0)
        {
            ep[1] = trend[1] != -1 ? min(low[i], ep[0]) : low[i];
        }
        else
        {
            ep[1] = trend[1] != 1 ? max(high[i], ep[0]) : high[i];
        }

        // Acceleration Factor y SAR

        /* si cambia la tendencia*/
        if (abs(trend[1]) == 1)
        {
            sar[1] = ep[0];
            af[1] = initial_acc;
        }
        else
        {
            sar[1] = temp_sar;
            if (ep[1] == ep[0])
            {
                af[1] = af[0];
            }
            else
            {
                af[1] = min(max_acc, af[0] + acc_increment);
            }
        }

        // Long signal
        if (trend[1] == 1 && trend[0] < 0) { 

            if (current_position == -1) { 
                double pnl_temp = (entry_price / close[i] - 1) * 100;
                pnl += pnl_temp;
                max_pnl = max(max_pnl, pnl);
                max_dd = max(max_dd, max_pnl - pnl);
                if (max_dd > 100) max_dd = 100;
            }

            current_position = 1;
            entry_price = close[i];

        }

        // Short signal
        else if (trend[1] == -1 && trend[0] > 0) {

             if (current_position == 1) { 
                double pnl_temp = (close[i] / entry_price - 1) * 100;
                pnl += pnl_temp;
                max_pnl = max(max_pnl, pnl);
                max_dd = max(max_dd, max_pnl - pnl);
                if (max_dd > 100) max_dd = 100;
            }

            current_position = -1;
            entry_price = close[i];
        }

        // Actualizo valores de variables

        trend[0] = trend[1];
        sar[0] = sar[1];
        ep[0] = ep[1];
        af[0] = af[1];
    }
}

/* Genero interfaces para las funciones para pasarlas y que se puedan usar en Python*/
DLLEXPORT Psar* Psar_new(char* exchange, char* symbol, char* timeframe, long long from_time, long long to_time) {
    return new Psar(exchange, symbol, timeframe, from_time, to_time);
}
DLLEXPORT void Psar_execute_backtest(Psar* psar, double initial_acc, double acc_increment, double max_acc) { 
    return psar->execute_backtest(initial_acc, acc_increment, max_acc);
}
/* También tendrá interfaces para generar los métodos para el pnl y el max_dd*/
DLLEXPORT double Psar_get_pnl(Psar* psar) {return psar->pnl;}
DLLEXPORT double Psar_get_max_dd(Psar* psar) {return psar->max_dd;}


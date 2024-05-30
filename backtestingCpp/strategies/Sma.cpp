#include <numeric>
#include "Sma.h"
#include "../Database.h"
#include "../Utils.h"

using namespace std;

Sma::Sma(char* exchange_c, char* symbol_c, char* timeframe_c, long long from_time, long long to_time)
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

void Sma::execute_backtest(int slow_ma, int fast_ma) 
{
    /* defino las variables que me ayudan a calcular el pnl y el drawdown para la estrategia*/
    pnl = 0.0;
    max_dd = 0.0;

    double max_pnl = 0.0;
    int current_position = 0;
    double entry_price;

    vector<double> slow_ma_closes = {};
    vector<double> fast_ma_closes = {};

    for (int i = 0; i < ts.size(); i++) {
        /* comienzo a acumular cada precio de cierre para formar las ma*/
        slow_ma_closes.push_back(close[i]);
        fast_ma_closes.push_back(close[i]);

        /* determino el tamaño que tiene la ma (si ya acumuló los suficientes datos para formarse)
        Si tiene datos de más, los borra*/
        if (slow_ma_closes.size() > slow_ma) { 
            slow_ma_closes.erase(slow_ma_closes.begin());
        }
        if (fast_ma_closes.size() > fast_ma) { 
            fast_ma_closes.erase(fast_ma_closes.begin());
        }
         if (slow_ma_closes.size() < slow_ma) { 
            continue;
        }

        /*calculo la sumatoria para la señal*/
        double sum_slow = accumulate(slow_ma_closes.begin(), slow_ma_closes.end(), 0.0);
        double sum_fast = accumulate(fast_ma_closes.begin(), fast_ma_closes.end(), 0.0);

        /*calculo la media*/
        double mean_slow = sum_slow / slow_ma;
        double mean_fast = sum_fast / fast_ma;

        // Long Signal
        /* si la media rápida es mayor a la lenta y la posición actual es neutra o short, chequeo si es short, cierro la posición, calculo el pnl y el drawdown
        y cambio la posición a 1 (long) y guardo el precio entrada*/
        if (mean_fast > mean_slow && current_position <=0) {

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

         // Short Signal
        if (mean_fast < mean_slow && current_position >=0) {

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
    }
}
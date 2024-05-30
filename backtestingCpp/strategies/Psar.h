#include <string>
#include <vector>

class Psar {
    public:
        /* debo definir el constructor con char en vez de string, ya que debo usar C (en vez de C++) para linkearlo con Python. (la _c final es para indicar que la variable es char)
        se usa 2 veces long, para indicar que es un valor muy alto.*/
        Psar(char* exchange_c, char* symbol_c, char* timeframe_c, long long from_time, long long to_time);
        /* el initial_acc, habitualmente es de 0.02*/
        void execute_backtest(double initial_acc, double acc_increment, double max_acc);

        /* declaro variables*/
        std::string exchange;
        std::string symbol;
        std::string timeframe;

        std::vector<double> ts, open, high, low, close, volume;

        double pnl = 0.0;
        double max_dd = 0.0;


};
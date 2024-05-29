#include <stdio.h>
#include "Database.h"
#include "Utils.h"

int main(int, char**){
    Database db("binance");
    int array_size = 0;
    double** res = db.get_data("BTCUSDT", "binance", array_size);

    std::vector<double> ts, open, high, low, close, volume;
    std::tie(ts, open, high, low, close, volume) = rearrange_candles(res, "5m", array_size);

    /* loop para mostrar los elementos*/
    for (int i = 0; i < 100; i++) {
        printf("%f %f %f %f %f %f\n", ts[i], open[i], high[i], low[i], close[i], volume[i]);
    }
    printf("%i\n", ts.size());
    db.close_file();
}

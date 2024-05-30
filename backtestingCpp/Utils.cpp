#include <math.h>
#include "Utils.h"

using namespace std;

/*Método para establecer otros timeframes a partir de las velas que obtengo en 1 minuto
La función va a devolver vectores, que se asemejarían a listas en python
Y para que devuelva múltiples vectores, uso tuplas.*/
tuple<vector<double>, vector<double>, vector<double>, vector<double>, vector<double>, vector<double>>
rearrange_candles(double **candles, string tf, long long from_time, long long to_time, int array_size)
{
    /*establezco el vector que se encontrará que contiene los nombres de las columnas
    y el ts en milisegundos*/
    vector<double> ts, open, high, low, close, volume;
    double tf_ms;

    /*Ahora debo tomar como viene el timeframe. Si es en minutos (1, 5, 15, 30) tendrá una m al final, si es 1h , 4h o 1d, tendrá otras letras
    y extraigo el número solamente (sin la m)*/
    if (tf.find("m") != string::npos)
    {
        string minutes = tf.substr(0, tf.find("m"));
        /* convierto el minuto a double con stod y luego a milisegundos*/
        tf_ms = stod(minutes) * 60.0 * 1000.0;
    }
    else if (tf.find("h") != string::npos)
    {
        string hours = tf.substr(0, tf.find("h"));
        /* convierto la hora a double con stod y luego a milisegundos*/
        tf_ms = stod(hours) * 60.0 * 60.0 * 1000.0;
    }
    else if (tf.find("d") != string::npos)
    {
        string day = tf.substr(0, tf.find("d"));
        /* convierto el dia a double con stod y luego a milisegundos*/
        tf_ms = stod(day) * 24.0 * 60.0 * 60.0 * 1000.0;
    }
    else
    {
        /*Si no obtengo datos*/
        printf("Parsing timeframe failed for %s\n", tf.c_str());
        return make_tuple(ts, open, high, low, close, volume);
    }

    /*Pueblo las velas usando las de 1 minuto y luego las convierto a demanda al resto de los timeframes
    Uso los timestamps para saber si las necesito updatear o crear una nueva
    el fmod() trae el resto de una división. En este caso si por ejemplo mi primera data es una candle de 5.13pm y estoy laburando con timeframe 5m, la redondea a 5.10pm
    Así actuará con el resto de los timeframes también*/
    double current_ts = 0.0;
    double current_o;
    double current_h;
    double current_l;
    double current_c;
    double current_v;

    /* loop para saber si debo crear una vela nueva o actualizar la del timeframe actual
    también debo considerar actualizar máximos y mínimos, en caso de tener valores mayores o menores al actual*/
    for (int i = 0; i < array_size; i++)
    {
        if (candles[i][0] < from_time) {
            continue;
        }
        /* Acá actualiza por única vez si el timestamp comienza justo en el from_time, ahí es == 0.0 y actualiza los valores, luego continua el loop */
        else if (current_ts == 0.0) {
            current_ts = candles[i][0] - fmod(candles[i][0], tf_ms);
            current_o = candles[i][1];
            current_h = candles[i][2];
            current_l = candles[i][3];
            current_c = candles[i][4];
            current_v = candles[i][5];
        }

        if (candles[i][0] > to_time) {
            break;
        }
        /* creo nueva vela : ejemplo tf = 60 -> candles[i][0] = 130 , current_ts = 60 , tf_ms = 60, */
        if (candles[i][0] > current_ts + tf_ms)
        {
            /* es como el método append de python, para agregar la candle al vector*/
            ts.push_back(current_ts);
            open.push_back(current_o);
            high.push_back(current_h);
            low.push_back(current_l);
            close.push_back(current_c);
            volume.push_back(current_v);

            /*Considero si tengo velas perdidas y las genero para agregarlas*/
            int missing_candles = (candles[i][0] - current_ts) / tf_ms - 1;

            if (missing_candles > 0) { 
                printf("Missing %i candle(s) from %f\n", missing_candles, current_ts);

                for (int u = 0; u < missing_candles; u++) {
                    /*las missing candles, serán con volumen 0 y tendrán una línea plana donde figura el útimo close conocido (de vela/s anteriores) ya que no tienen data*/
                    ts.push_back(current_ts + tf_ms * (u + 1));
                    open.push_back(current_c);
                    high.push_back(current_c);
                    low.push_back(current_c);
                    close.push_back(current_c);
                    volume.push_back(0);
                }
            }


            /* actualizo el valor de la vela*/
            current_ts = candles[i][0] - fmod(candles[i][0], tf_ms);
            current_o = candles[i][1];
            current_h = candles[i][2];
            current_l = candles[i][3];
            current_c = candles[i][4];
            current_v = candles[i][5];
            
        }
        else
        {

            if (candles[i][2] > current_h)
            {
                current_h = candles[i][2];
            }

             if (candles[i][3] < current_l)
            {
                current_l = candles[i][3];
            }

            current_c = candles[i][4];
            /* actualizo el volumen siempre sumando el acumulado*/
            current_v += candles[i][5];
        }
    }

    return make_tuple(ts, open, high, low, close, volume);
}
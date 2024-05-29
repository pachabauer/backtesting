#include <string>
#include <tuple>
#include <vector>

/*Método para establecer otros timeframes a partir de las velas que obtengo en 1 minuto
La función va a devolver vectores, que se asemejarían a listas en python
Y para que devuelva múltiples vectores, uso tuplas.*/
std::tuple< std::vector<double>, std::vector<double>, std::vector<double>, std::vector<double>,
std::vector<double>, std::vector<double>> rearrange_candles(double** candles, std::string tf, int array_size);
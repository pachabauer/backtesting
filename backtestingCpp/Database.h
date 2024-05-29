/*Así se declaran los imports. Acá traigo de la standard library, los string*/
#include <string>
#include <hdf5.h>


class Database
{
public:
/*Declaro el type de la variable file_name así. Aparte el & es para indicar que pasa como referencia, no permite crear nuevas instancias de la variable*/
    Database(const std::string& file_name);
    void close_file();
    
    /*Defino el método para traer data. Como debo saber el size de la data (y no lo sé) debo crearlo dinámicamente. Para ello, necesito un array bidimesional
     (el cual tiene filas y columnas (timestamp, open... etc)) Eso se representa con double***/
    double** get_data(const std::string& symbol, const std::string& exchange, int& array_size);

    /*Representa el ID del file que abro. Entonces, podré usar ese ID con los métodos de la clase para ejecutarlos sobre el File*/
    hid_t h5_file;
};

/*método que permite comparar las filas, para ordenarlas alfabéticamente*/
int compare(const void* pa, const void* pb);


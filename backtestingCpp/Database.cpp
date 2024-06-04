#include "Database.h"
#include <chrono>
#include <cstdlib>

/*Me sirve para no tener que poner el tipo de cada variable que sea standard*/
using namespace std;

/*Defino el comportamiento de la clase*/
Database::Database(const string& file_name)
{
    /*Especifico esa ruta, ya que acá está en el build, subo a backtestingCPP y luego a la carpeta de Python que contiene la database.h5 de binance*/
    string FILE_NAME = "../../data/" + file_name + ".h5";
    /*Establezco una lista de propiedades que necesita el file para abrirse*/
    hid_t fapl = H5Pcreate(H5P_FILE_ACCESS);

    /*Más propiedad de acceso*/
    herr_t status = H5Pset_libver_bounds(fapl, H5F_LIBVER_LATEST, H5F_LIBVER_LATEST);
    /*Indica si H5Pset_libver_bounds se ejecutó correctamente o no*/
    status = H5Pset_fclose_degree(fapl, H5F_CLOSE_STRONG);

    /*como printf es una función de C y no de C++ debo convertir a c.str()*/
    printf("Opening %s\n", FILE_NAME.c_str());

    /* establezco el archivo a abrir con un parámetro en C string y en solo lectura */
    h5_file = H5Fopen(FILE_NAME.c_str(), H5F_ACC_RDONLY, fapl);

    /*Si existe un error al abrir el file, dará un número negativo, con lo cual puedo identificarlo y disparar un mensaje de error
    previo al mensaje, puedo llamar a que abra con la ruta de python (sin el ../..) ya que python abre directamente, sin ir a la raiz del directorio*/
    if (h5_file < 0) {
        FILE_NAME = "data/" + file_name + ".h5";
        h5_file = H5Fopen(FILE_NAME.c_str(), H5F_ACC_RDONLY, fapl);
        if (h5_file < 0) {
            printf("Error while opening %s \n", FILE_NAME.c_str());
        }
    }
}

/* Siempre que abra el file, debo cerrarlo ya que sino puede corromper el file y chau, hay que hacerlo de nuevo*/
void Database::close_file()
{
    H5Fclose(h5_file);
}

double** Database::get_data(const string& symbol, const string& exchange, int& array_size)
{
    /*Array vacío*/
    double** results = {};

    /*Abro el dataset*/
    hid_t dataset = H5Dopen2(h5_file, symbol.c_str(), H5P_DEFAULT);
    /* Si el dataset se abre correctamente el ID será positivo*/
    if (dataset == -1) 
    { 
        return results;
    }

    /* mido cuánto tiempo lleva al programa hacer las operaciones*/
    auto start_ts = chrono::high_resolution_clock::now();

    /* Acceder al espacio del dataset y especifico las dimensiones del dataset con el tipo de variable hsize_t*/
    hid_t dspace = H5Dget_space(dataset);
    hsize_t dims[2];

    H5Sget_simple_extent_dims(dspace, dims, NULL);

    array_size = (int)dims[0];

    /*Array of pointers to array [0] contiene la información del número de filas*/
    results = new double*[dims[0]];
    
    /*el tipo size_t es un integer*/
    for (size_t i = 0; i< dims[0]; i++) 
    {
        /*le asigno a cada iteración (row) el número de columnas que sale de dims[1] (6 columnas)*/
        results[i] = new double[dims[1]];
    }

    /* establezco el array unidimensional (fila con 6 columnas) que leeré en la siguiente función, para luego ir poblando el results con el loop for*/
    double* candles_arr = new double[dims[0] * dims[1]];

    /*Leo el dataset*/
    H5Dread(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, candles_arr);

    /* loop para poblar results*/
    int j = 0;

    for (int i = 0; i < dims[0] * dims[1]; i+=6)
    {
        results [j][0] =  candles_arr[i];
        results [j][1] =  candles_arr[i+1];
        results [j][2] =  candles_arr[i+2];
        results [j][3] =  candles_arr[i+3];
        results [j][4] =  candles_arr[i+4];
        results [j][5] =  candles_arr[i+5];

        j++;
    }

    /*cada vez que creo una variable con un new , debería delete para liberar y hacer el programa rápido*/
    delete[] candles_arr;

    qsort(results, dims[0], sizeof(results[0]), compare);

    H5Sclose(dspace);
    H5Dclose(dataset);

    
    /* mido cuánto tiempo lleva al programa hacer las operaciones*/
    auto end_ts = chrono::high_resolution_clock::now();

    /*diferencia entre inicio y fin, mido tiempo del programa*/
    auto read_duration = chrono::duration_cast<chrono::milliseconds> (end_ts - start_ts);

    /* imprimo el número de candles, por eso es %i (integer)*/
    printf("Fetched %i %s %s data in %i ms\n", (int)dims[0], exchange.c_str(), symbol.c_str(), (int) read_duration.count());

    return results;

}

int compare(const void* pa, const void* pb) 
{
    const double* a = *(const double**)pa;
    const double* b = *(const double**)pb;

    if (a[0] == b[0]) {
        return 0;
    }
    else if (a[0] < b[0]) {
        return -1;
    }
    else {
        return 1;
    }    
}
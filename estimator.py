import pandas as pd
import numpy as np
import os

def cargar_y_analizar_historico(ruta_csv="consumo_historico.csv"):
    """
    Carga el histórico de consumo diario desde un archivo CSV y calcula 
    la media muestral (mu) y la desviación estándar muestral (sigma).

    Parámetros:
    - ruta_csv (str): Ruta al archivo CSV con los datos históricos.

    Retorna:
    - tuple[float, float]: Una tupla con (media, desviacion_estandar).
    """
    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(
            f"El archivo '{ruta_csv}' no existe. Asegúrese de generar los datos históricos primero."
        )
    
    # Leer el archivo CSV
    df = pd.read_csv(ruta_csv)
    
    # Validar que la columna 'Consumo_Kg' esté presente
    if 'Consumo_Kg' not in df.columns:
        raise ValueError(
            f"El archivo CSV '{ruta_csv}' no contiene la columna obligatoria 'Consumo_Kg'."
        )
        
    consumos = df['Consumo_Kg'].values
    
    # Calcular la media y desviación estándar muestral (grados de libertad ddof=1)
    media = float(np.mean(consumos))
    desviacion = float(np.std(consumos, ddof=1))
    
    return media, desviacion

if __name__ == "__main__":
    # Prueba rápida del módulo
    try:
        media, desviacion = cargar_y_analizar_historico()
        print(f"Prueba del Estimador:")
        print(f"  Media (mu): {media:.2f} kg")
        print(f"  Desviación Estándar (sigma): {desviacion:.2f} kg")
    except FileNotFoundError as e:
        print(e)

import pandas as pd
import numpy as np

def generar_consumo_historico(dias=200, media=330.0, desviacion=40.0, ruta_csv="consumo_historico.csv"):
    """
    Genera datos históricos simulados del consumo diario de masa (en kg)
    basado en una distribución gaussiana (normal) y los guarda en un archivo CSV.

    Parámetros:
    - dias (int): Número de días históricos a generar.
    - media (float): Media del consumo diario en kg (mu).
    - desviacion (float): Desviación estándar del consumo diario en kg (sigma).
    - ruta_csv (str): Ruta del archivo CSV de salida.
    
    Retorna:
    - pd.DataFrame: El DataFrame generado con los consumos históricos.
    """
    # Fijar semilla para que las simulaciones sean reproducibles
    np.random.seed(42)
    
    # Generar valores aleatorios gaussianos
    consumo = np.random.normal(loc=media, scale=desviacion, size=dias)
    
    # El consumo de masa no puede ser negativo, limitamos a 0
    consumo = np.clip(consumo, 0, None)
    
    # Redondear a 2 decimales para simular mediciones reales
    consumo = np.round(consumo, 2)
    
    # Crear el DataFrame
    df = pd.DataFrame({
        'Dia': np.arange(1, dias + 1),
        'Consumo_Kg': consumo
    })
    
    # Guardar en archivo CSV
    df.to_csv(ruta_csv, index=False)
    return df

if __name__ == "__main__":
    # Generar un archivo inicial de prueba con los datos por defecto si se ejecuta el script directamente
    generar_consumo_historico()

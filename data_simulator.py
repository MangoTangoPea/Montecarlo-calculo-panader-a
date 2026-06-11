import pandas as pd
import numpy as np

def generar_consumo_historico(dias=200, media=62.5, desviacion=12.5, ruta_csv=None, seed=None):
    """
    Genera datos históricos simulados del consumo diario de masa (en kg)
    basado en una distribución gaussiana (normal) y los guarda en un archivo CSV.

    Parámetros:
    - dias (int): Número de días históricos a generar.
    - media (float): Media del consumo diario en kg (mu).
    - desviacion (float): Desviación estándar del consumo diario en kg (sigma).
    - ruta_csv (str): Ruta del archivo CSV de salida. Si es None, no se guarda a disco.
    - seed (int): Semilla para reproducibilidad. Si es None, se genera de forma aleatoria.
    
    Retorna:
    - pd.DataFrame: El DataFrame generado con los consumos históricos.
    """
    rng = np.random.default_rng(seed)
    
    # Generar valores aleatorios gaussianos
    consumo = rng.normal(loc=media, scale=desviacion, size=dias)
    
    # El consumo de masa no puede ser negativo, limitamos a 0
    consumo = np.clip(consumo, 0, None)
    
    # Redondear a 2 decimales para simular mediciones reales
    consumo = np.round(consumo, 2)
    
    # Generar un rango de fechas consecutivas que terminan hoy
    fechas = pd.date_range(end=pd.Timestamp.now().normalize(), periods=dias, freq='D')
    fechas_str = fechas.strftime('%Y-%m-%d')
    
    # Crear el DataFrame
    df = pd.DataFrame({
        'Fecha': fechas_str,
        'Consumo_Kg': consumo
    })
    
    # Guardar en archivo CSV si se especifica una ruta
    if ruta_csv is not None:
        df.to_csv(ruta_csv, index=False)
    return df


if __name__ == "__main__":
    # Generar un archivo inicial de prueba con los datos por defecto si se ejecuta el script directamente
    generar_consumo_historico()

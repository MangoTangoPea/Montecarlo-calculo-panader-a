import numpy as np

def simular_dias_agotamiento(inventario_objetivo=600.0, media=330.0, desviacion=40.0, iteraciones=10000):
    """
    Ejecuta una simulación de Montecarlo para estimar cuántos días tomará
    agotar un inventario determinado de masa, basándose en la media y desviación
    estándar del consumo diario.

    Parámetros:
    - inventario_objetivo (float): Cantidad total de masa en kg a evaluar (ej. 600 kg).
    - media (float): Consumo diario medio (mu).
    - desviacion (float): Desviación estándar del consumo diario (sigma).
    - iteraciones (int): Número de simulaciones independientes a realizar (por defecto 10,000).

    Retorna:
    - dict: Diccionario con estadísticas agregadas de la simulación y el historial completo.
    """
    # Semilla fija para consistencia en pruebas
    np.random.seed(123)
    
    resultados_dias = []
    
    for _ in range(iteraciones):
        inventario_restante = inventario_objetivo
        dias = 0
        while inventario_restante > 0:
            # Obtener una muestra aleatoria de la distribución normal
            consumo_diario = np.random.normal(loc=media, scale=desviacion)
            # Asegurar que el consumo no sea negativo (física y lógicamente imposible)
            consumo_diario = max(0.0, consumo_diario)
            
            # Si la media es muy baja o cero, evitamos bucles infinitos
            if consumo_diario == 0 and media <= 0:
                # Caso extremo: no hay consumo, rompemos simulación para evitar bucles infinitos
                dias = float('inf')
                break
                
            inventario_restante -= consumo_diario
            dias += 1
            
        resultados_dias.append(dias)
        
    resultados_dias = np.array(resultados_dias)
    
    # Calcular estadísticas agregadas
    dias_promedio = float(np.mean(resultados_dias))
    dias_mediana = float(np.median(resultados_dias))
    dias_min = int(np.min(resultados_dias))
    dias_max = int(np.max(resultados_dias))
    
    # Percentiles (por ejemplo, percentil 5 y 95 para intervalos de confianza)
    p5 = float(np.percentile(resultados_dias, 5))
    p95 = float(np.percentile(resultados_dias, 95))
    
    # Frecuencias para construir la probabilidad acumulada / histograma en UI
    valores, conteos = np.unique(resultados_dias, return_counts=True)
    distribucion_probabilidad = {int(val): float(count) / iteraciones for val, count in zip(valores, conteos)}
    
    return {
        "dias_promedio": round(dias_promedio, 2),
        "dias_mediana": round(dias_mediana, 2),
        "dias_min": dias_min,
        "dias_max": dias_max,
        "p5": round(p5, 2),
        "p95": round(p95, 2),
        "distribucion_probabilidad": distribucion_probabilidad,
        "historial_dias": resultados_dias.tolist()
    }

if __name__ == "__main__":
    # Prueba rápida del simulador de Montecarlo
    print("Prueba del Motor de Montecarlo (600 kg con consumo medio de 330 kg y sd de 40 kg):")
    res = simular_dias_agotamiento(inventario_objetivo=600.0, media=330.0, desviacion=40.0, iteraciones=1000)
    print(f"  Promedio: {res['dias_promedio']} días")
    print(f"  Mínimo: {res['dias_min']} días")
    print(f"  Máximo: {res['dias_max']} días")
    print(f"  Percentil 5: {res['p5']} días")
    print(f"  Percentil 95: {res['p95']} días")
    print(f"  Distribución de Probabilidad de Días:")
    for dia, prob in res['distribucion_probabilidad'].items():
        print(f"    {dia} días: {prob * 100:.2f}% de probabilidad")

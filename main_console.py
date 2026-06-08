import sys
from data_simulator import generar_consumo_historico
from estimator import cargar_y_analizar_historico
from monte_carlo import simular_dias_agotamiento

def ejecutar_flujo_completo(inventario=600.0, dias_historicos=200, iteraciones=10000):
    print("=" * 65)
    print("   SISTEMA DE PREDICCIÓN DE INVENTARIO - PANADERÍA MONTECARLO   ")
    print("=" * 65)
    
    # 1. Generación de datos históricos simulados (Simulador - Tarea 1)
    print(f"\n[1] Generando {dias_historicos} dias de consumo historico (CSV)...")
    generar_consumo_historico(
        dias=dias_historicos, 
        media=330.0, 
        desviacion=40.0, 
        ruta_csv="consumo_historico.csv"
    )
    print("    -> Datos generados y guardados en 'consumo_historico.csv'")
    
    # 2. Estimación estadística (Estimador - Tarea 2)
    print("\n[2] Analizando comportamiento historico...")
    try:
        media, desviacion = cargar_y_analizar_historico("consumo_historico.csv")
        print(f"    -> Consumo Diario Promedio (media): {media:.2f} kg de masa")
        print(f"    -> Desviacion Estandar (std): {desviacion:.2f} kg")
    except Exception as e:
        print(f"    Error al cargar y analizar el historico: {e}")
        return

    # 3. Motor de Montecarlo (Simulación - Tarea 3)
    print(f"\n[3] Ejecutando Simulacion de Montecarlo ({iteraciones:,} iteraciones)...")
    print(f"    -> Inventario Objetivo: {inventario} kg de masa")
    
    res = simular_dias_agotamiento(
        inventario_objetivo=inventario,
        media=media,
        desviacion=desviacion,
        iteraciones=iteraciones
    )
    
    # 4. Mostrar resultados e informe agregado
    print("\n" + "=" * 65)
    print("                     INFORME DE PREDICCION                      ")
    print("=" * 65)
    print(f"  • Tiempo Promedio para Agotar:  {res['dias_promedio']} dias")
    print(f"  • Mediana del Tiempo:           {res['dias_mediana']} dias")
    print(f"  • Rango Absoluto Observado:     De {res['dias_min']} a {res['dias_max']} dias")
    print(f"  • Rango de Certeza (90%):       De {res['p5']} a {res['p95']} dias")
    
    print("\n  Distribucion de Probabilidad:")
    for dias, prob in sorted(res['distribucion_probabilidad'].items()):
        progreso = "#" * int(round(prob * 30))
        print(f"    {dias:2d} dias: {prob * 100:6.2f}% {progreso}")
        
    print("\n  Interpretacion:")
    prob_bajo_2 = res['distribucion_probabilidad'].get(1, 0.0) + res['distribucion_probabilidad'].get(2, 0.0)
    print(f"  -> Hay un {prob_bajo_2 * 100:.2f}% de probabilidad de que el inventario")
    print(f"     de {inventario} kg se agote en 2 dias o menos.")
    print("=" * 65)

if __name__ == "__main__":
    inventario_inicial = 600.0
    if len(sys.argv) > 1:
        try:
            inventario_inicial = float(sys.argv[1])
        except ValueError:
            print("El argumento de inventario debe ser numérico. Usando 600.0 kg por defecto.")
            
    ejecutar_flujo_completo(inventario=inventario_inicial)

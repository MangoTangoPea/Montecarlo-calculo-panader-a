import os
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Importar los módulos del backend provistos
from data_simulator import generar_consumo_historico
from estimator import cargar_y_analizar_historico
from monte_carlo import simular_dias_agotamiento

# Configuración básica de CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")  # Tema base, que luego personalizaremos con colores específicos

class MonteCarloGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración de la Ventana Principal
        self.title("Panadería Montecarlo - Predicción y Simulación de Inventario")
        self.geometry("1280x820")
        self.minsize(1024, 768)
        self.configure(fg_color='#1A1412')  # Fondo carbón oscuro / cálido
        
        # Configuración de la rejilla principal
        self.columnconfigure(0, weight=0)  # Columna 0: Panel lateral de control (Ancho fijo)
        self.columnconfigure(1, weight=1)  # Columna 1: Panel principal (Expansible)
        self.rowconfigure(0, weight=1)
        
        # Inicializar componentes
        self.inicializar_sidebar()
        self.inicializar_main_panel()
        
        # Intentar cargar datos históricos iniciales al iniciar si ya existen
        self.cargar_historico_inicial()
        
    def set_status(self, message, is_error=False):
        """Actualiza el texto y color del panel de estado del sistema."""
        color = "#D98880" if is_error else "#AFA196"
        self.lbl_status.configure(text=message, text_color=color)
        
    def inicializar_sidebar(self):
        """Crea el panel lateral izquierdo con todos los campos de entrada y controles."""
        self.sidebar_frame = ctk.CTkFrame(
            self, 
            width=330, 
            corner_radius=0, 
            fg_color='#231B19', 
            border_color='#3D302C', 
            border_width=1
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar_frame.grid_propagate(False)  # Impedir que se achique el panel lateral
        
        # Contenedor interno con márgenes (padding)
        content_frame = ctk.CTkFrame(self.sidebar_frame, fg_color='transparent')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=25)
        
        # Cabecera de la Aplicación
        title_label = ctk.CTkLabel(
            content_frame, 
            text="MONTECARLO", 
            font=ctk.CTkFont(family="Georgia", size=26, weight="bold"), 
            text_color='#D4AF37'  # Dorado premium
        )
        title_label.pack(anchor="w", pady=(0, 2))
        
        subtitle_label = ctk.CTkLabel(
            content_frame, 
            text="Simulación de Inventario de Masa", 
            font=ctk.CTkFont(family="Arial", size=13, slant="italic"), 
            text_color='#AFA196'
        )
        subtitle_label.pack(anchor="w", pady=(0, 15))
        
        # Línea divisoria elegante
        line = ctk.CTkFrame(content_frame, height=2, fg_color='#3D302C')
        line.pack(fill=tk.X, pady=(0, 20))
        
        # SECCIÓN 1: Configuración de Datos Históricos
        sec1_title = ctk.CTkLabel(
            content_frame, 
            text="1. CONSUMO HISTÓRICO", 
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"), 
            text_color='#D4AF37'
        )
        sec1_title.pack(anchor="w", pady=(0, 10))
        
        # Entradas de la sección histórica
        self.crear_label_entry(content_frame, "Días Históricos a Analizar (N):", "200", "_dias_hist")
        self.crear_label_entry(content_frame, "Consumo Promedio Base (kg):", "330.0", "_media_gen")
        self.crear_label_entry(content_frame, "Desviación Estándar Base (kg):", "40.0", "_desv_gen")
        
        # Botón de Cargar/Generar datos históricos
        self.btn_cargar_datos = ctk.CTkButton(
            content_frame,
            text="Generar y Cargar Datos",
            fg_color='#D4AF37',
            hover_color='#B2902C',
            text_color='#1A1412',
            font=ctk.CTkFont(family="Arial", size=13, weight="bold"),
            height=36,
            command=self.accion_generar_y_cargar
        )
        self.btn_cargar_datos.pack(fill=tk.X, pady=(15, 25))
        
        # Línea divisoria 2
        line2 = ctk.CTkFrame(content_frame, height=1, fg_color='#3D302C')
        line2.pack(fill=tk.X, pady=(0, 20))
        
        # SECCIÓN 2: Configuración de Simulación
        sec2_title = ctk.CTkLabel(
            content_frame, 
            text="2. SIMULACIÓN MONTECARLO", 
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"), 
            text_color='#D4AF37'
        )
        sec2_title.pack(anchor="w", pady=(0, 10))
        
        # Entradas de la sección de simulación
        self.crear_label_entry(content_frame, "Cantidad de Masa a Evaluar (kg):", "600.0", "_masa")
        self.crear_label_entry(content_frame, "Iteraciones de Montecarlo:", "10000", "_iter")
        
        # Botón de ejecutar simulación
        self.btn_simular = ctk.CTkButton(
            content_frame,
            text="Ejecutar Simulación",
            fg_color='#D4AF37',
            hover_color='#B2902C',
            text_color='#1A1412',
            font=ctk.CTkFont(family="Arial", size=13, weight="bold"),
            height=36,
            command=self.accion_simular
        )
        self.btn_simular.pack(fill=tk.X, pady=(15, 25))
        
        # Línea divisoria 3
        line3 = ctk.CTkFrame(content_frame, height=1, fg_color='#3D302C')
        line3.pack(fill=tk.X, pady=(0, 15))
        
        # SECCIÓN 3: Estado de la Aplicación
        lbl_status_title = ctk.CTkLabel(
            content_frame, 
            text="ESTADO DEL SISTEMA:", 
            font=ctk.CTkFont(family="Arial", size=10, weight="bold"), 
            text_color='#AFA196'
        )
        lbl_status_title.pack(anchor="w", pady=(0, 2))
        
        self.lbl_status = ctk.CTkLabel(
            content_frame, 
            text="Inicializando...", 
            font=ctk.CTkFont(family="Arial", size=11), 
            text_color='#AFA196',
            justify="left",
            anchor="w",
            wraplength=280
        )
        self.lbl_status.pack(fill=tk.X, anchor="w", pady=0)
        
    def crear_label_entry(self, parent, label_text, default_value, attribute_suffix):
        """Función auxiliar para generar etiquetas e inputs uniformes."""
        lbl = ctk.CTkLabel(
            parent, 
            text=label_text, 
            font=ctk.CTkFont(family="Arial", size=11), 
            text_color='#AFA196'
        )
        lbl.pack(anchor="w", pady=(0, 2))
        
        entry = ctk.CTkEntry(
            parent,
            fg_color='#2D2320',
            text_color='#F4F0EA',
            border_color='#4A3B37',
            border_width=1,
            corner_radius=6,
            height=30,
            font=ctk.CTkFont(family="Arial", size=12)
        )
        entry.insert(0, default_value)
        entry.pack(fill=tk.X, pady=(0, 12))
        
        setattr(self, f"entry{attribute_suffix}", entry)
        
    def inicializar_main_panel(self):
        """Crea el área principal del frontend: tarjetas de métricas en la fila superior, y gráficos en la inferior."""
        self.main_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=25)
        
        self.main_frame.columnconfigure((0, 1, 2, 3), weight=1)
        self.main_frame.rowconfigure(0, weight=0)  # Fila de Tarjetas (KPIs)
        self.main_frame.rowconfigure(1, weight=1)  # Fila de Gráficos
        
        # Crear 4 Tarjetas de Métricas Estadísticas (KPI Cards)
        self.card_hist, self.lbl_hist_media, self.lbl_hist_desv = self.crear_tarjeta_metrica(
            self.main_frame, "Histórico Consumo", "Promedio: --", "Desviación: --"
        )
        self.card_sim_tiempo, self.lbl_sim_prom, self.lbl_sim_mediana = self.crear_tarjeta_metrica(
            self.main_frame, "Agotamiento Estimado", "Promedio: --", "Mediana: --"
        )
        self.card_sim_certeza, self.lbl_sim_certeza, self.lbl_sim_rango = self.crear_tarjeta_metrica(
            self.main_frame, "Rangos y Confianza", "Certeza (90%): --", "Absoluto: --"
        )
        self.card_sim_riesgo, self.lbl_sim_riesgo, self.lbl_sim_nivel_riesgo = self.crear_tarjeta_metrica(
            self.main_frame, "Alerta de Inventario", "Agotamiento ≤ 2 Días: --", "Nivel: --"
        )
        
        # Posicionar Tarjetas en la fila 0
        self.card_hist.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 15))
        self.card_sim_tiempo.grid(row=0, column=1, sticky="nsew", padx=6, pady=(0, 15))
        self.card_sim_certeza.grid(row=0, column=2, sticky="nsew", padx=6, pady=(0, 15))
        self.card_sim_riesgo.grid(row=0, column=3, sticky="nsew", padx=(6, 0), pady=(0, 15))
        
        # Área de Gráficos (Fila 1)
        self.plots_frame = ctk.CTkFrame(self.main_frame, fg_color='transparent')
        self.plots_frame.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=0)
        self.plots_frame.columnconfigure((0, 1), weight=1)
        self.plots_frame.rowconfigure(0, weight=1)
        
        # Contenedor para Gráfico 1 (Izquierdo)
        self.plot_frame_left = ctk.CTkFrame(
            self.plots_frame, 
            fg_color='#2D2320', 
            border_color='#3D302C', 
            border_width=1, 
            corner_radius=8
        )
        self.plot_frame_left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        
        # Contenedor para Gráfico 2 (Derecho)
        self.plot_frame_right = ctk.CTkFrame(
            self.plots_frame, 
            fg_color='#2D2320', 
            border_color='#3D302C', 
            border_width=1, 
            corner_radius=8
        )
        self.plot_frame_right.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)
        
        # Inicializar y embeber gráficos vacíos de Matplotlib
        self.inicializar_graficos()
        
    def crear_tarjeta_metrica(self, master, titulo, val1_init, val2_init):
        """Crea una tarjeta KPI premium con tipografía limpia y bordes sutiles."""
        frame = ctk.CTkFrame(
            master, 
            fg_color='#2D2320', 
            border_color='#3D302C', 
            border_width=1, 
            corner_radius=8
        )
        
        lbl_title = ctk.CTkLabel(
            frame, 
            text=titulo.upper(), 
            font=ctk.CTkFont(family="Arial", size=10, weight="bold"), 
            text_color='#AFA196'
        )
        lbl_title.pack(anchor="w", padx=15, pady=(12, 4))
        
        lbl_val1 = ctk.CTkLabel(
            frame, 
            text=val1_init, 
            font=ctk.CTkFont(family="Georgia", size=18, weight="bold"), 
            text_color='#F4F0EA'
        )
        lbl_val1.pack(anchor="w", padx=15, pady=(0, 2))
        
        lbl_val2 = ctk.CTkLabel(
            frame, 
            text=val2_init, 
            font=ctk.CTkFont(family="Arial", size=12), 
            text_color='#AFA196'
        )
        lbl_val2.pack(anchor="w", padx=15, pady=(0, 12))
        
        return frame, lbl_val1, lbl_val2
        
    def inicializar_graficos(self):
        """Crea los objetos de figuras de Matplotlib y los embebe en Tkinter con layouts iniciales."""
        # Gráfico 1: Consumo Histórico
        self.fig1, self.ax1 = plt.subplots(figsize=(5, 4.2), dpi=100)
        self.configurar_estilo_plot(self.fig1, self.ax1)
        self.ax1.text(0.5, 0.5, "Esperando datos históricos...", 
                     color='#AFA196', ha='center', va='center', transform=self.ax1.transAxes)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.plot_frame_left)
        self.canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Gráfico 2: Resultados Montecarlo
        self.fig2, self.ax2 = plt.subplots(figsize=(5, 4.2), dpi=100)
        self.configurar_estilo_plot(self.fig2, self.ax2)
        self.ax2.text(0.5, 0.5, "Esperando simulación...", 
                     color='#AFA196', ha='center', va='center', transform=self.ax2.transAxes)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.plot_frame_right)
        self.canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def configurar_estilo_plot(self, fig, ax):
        """Estiliza los gráficos de Matplotlib para que coincidan con la estética oscura y dorada."""
        fig.patch.set_facecolor('#2D2320')
        ax.set_facecolor('#2D2320')
        
        # Ocultar bordes innecesarios
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#4A3C37')
        ax.spines['bottom'].set_color('#4A3C37')
        
        # Colores de fuentes y etiquetas
        ax.tick_params(colors='#AFA196', labelsize=9)
        ax.xaxis.label.set_color('#AFA196')
        ax.xaxis.label.set_size(10)
        ax.yaxis.label.set_color('#AFA196')
        ax.yaxis.label.set_size(10)
        
        # Grid tenue y punteada
        ax.grid(True, color='#3D302C', linestyle=':', alpha=0.6)
        
    def cargar_historico_inicial(self):
        """Carga y grafica en el inicio los consumos en caso de que exista 'consumo_historico.csv'."""
        ruta_csv = "consumo_historico.csv"
        if os.path.exists(ruta_csv):
            try:
                self.actualizar_historico(ruta_csv)
                self.set_status("Histórico de consumos cargado con éxito al iniciar.")
            except Exception as e:
                self.set_status(f"Error al cargar histórico inicial: {e}", is_error=True)
        else:
            self.set_status("Listo. Genere o cargue consumos históricos para comenzar.")
            
    def validar_entero(self, valor, nombre, min_val=1):
        """Valida que una entrada de texto sea un entero válido mayor que min_val."""
        try:
            val = int(valor)
            if val < min_val:
                raise ValueError()
            return val
        except ValueError:
            raise ValueError(f"El campo '{nombre}' debe ser un número entero mayor o igual a {min_val}.")

    def validar_flotante(self, valor, nombre, min_val=0.01):
        """Valida que una entrada de texto sea un número decimal válido mayor que min_val."""
        try:
            val = float(valor)
            if val < min_val:
                raise ValueError()
            return val
        except ValueError:
            raise ValueError(f"El campo '{nombre}' debe ser un número decimal mayor o igual a {min_val:.2f}.")

    def actualizar_historico(self, ruta_csv):
        """Lee el CSV y calcula la media y desviación estándar para poblar tarjetas y Gráfico 1."""
        media, desviacion = cargar_y_analizar_historico(ruta_csv)
        self.media = media
        self.desviacion = desviacion
        
        # Actualizar tarjeta de métricas históricas
        self.lbl_hist_media.configure(text=f"Promedio: {media:.2f} kg")
        self.lbl_hist_desv.configure(text=f"Desviación: {desviacion:.2f} kg")
        
        # Cargar los datos crudos para graficar la distribución empírica
        df = pd.read_csv(ruta_csv)
        consumos = df['Consumo_Kg'].values
        
        # Dibujar Gráfico 1
        self.actualizar_plot_historico(consumos, media, desviacion)
        
    def actualizar_plot_historico(self, consumos, media, desviacion):
        """Dibuja el histograma de consumos históricos con la curva de distribución normal superpuesta."""
        self.ax1.clear()
        self.configurar_estilo_plot(self.fig1, self.ax1)
        
        # Histograma de datos empíricos de consumo diario
        count, bins, ignored = self.ax1.hist(
            consumos, 
            bins=25, 
            density=True, 
            alpha=0.5, 
            color='#C5A059',  # Dorado mate
            edgecolor='#2D2320',
            label='Consumo Empírico'
        )
        
        # Curva de distribución normal gaussiana utilizando la media y desviación estándar
        xmin, xmax = self.ax1.get_xlim()
        x = np.linspace(xmin, xmax, 100)
        # Ecuación de la densidad normal: y = 1/(std * sqrt(2*pi)) * exp(-0.5 * ((x-mean)/std)**2)
        p = (1.0 / (desviacion * np.sqrt(2.0 * np.pi))) * np.exp(-0.5 * ((x - media) / desviacion) ** 2)
        self.ax1.plot(x, p, color='#D4AF37', linewidth=2.5, label='Distribución Normal')
        
        # Agregar línea indicando la media calculada
        self.ax1.axvline(media, color='#F4F0EA', linestyle='--', linewidth=1.5, label=f'Media: {media:.1f} kg')
        
        self.ax1.set_title("Distribución del Consumo Diario de Masa", color='#F4F0EA', fontsize=12, pad=10, weight='bold')
        self.ax1.set_xlabel("Consumo diario (kg)", color='#AFA196')
        self.ax1.set_ylabel("Densidad de Probabilidad", color='#AFA196')
        self.ax1.legend(facecolor='#2D2320', edgecolor='#4A3C37', labelcolor='#F4F0EA', fontsize=8)
        self.fig1.tight_layout()
        self.canvas1.draw()
        
    def actualizar_plot_simulacion(self, res):
        """Dibuja el gráfico de barras indicando las probabilidades para cada día de agotamiento."""
        self.ax2.clear()
        self.configurar_estilo_plot(self.fig2, self.ax2)
        
        # Obtener valores ordenados de días
        valores = sorted(list(res["distribucion_probabilidad"].keys()))
        probabilidades = [res["distribucion_probabilidad"][v] * 100 for v in valores]
        
        # Graficar barras
        self.ax2.bar(
            valores, 
            probabilidades, 
            color='#D4AF37', 
            alpha=0.6, 
            edgecolor='#2D2320',
            width=0.6,
            label='Probabilidad'
        )
        
        # Extraer métricas clave para trazar las líneas verticales
        mean_val = res["dias_promedio"]
        p5_val = res["p5"]
        p95_val = res["p95"]
        
        self.ax2.axvline(mean_val, color='#F4F0EA', linestyle='-', linewidth=2, label=f'Promedio ({mean_val} d)')
        self.ax2.axvline(p5_val, color='#E67E22', linestyle='--', linewidth=1.5, label=f'P5 ({p5_val} d)')
        self.ax2.axvline(p95_val, color='#2ECC71', linestyle='--', linewidth=1.5, label=f'P95 ({p95_val} d)')
        
        # Sombrear el área de certeza del 90%
        self.ax2.axvspan(p5_val, p95_val, color='#D4AF37', alpha=0.1, label='Intervalo Certeza 90%')
        
        self.ax2.set_title("Probabilidad de Agotamiento de Inventario", color='#F4F0EA', fontsize=12, pad=10, weight='bold')
        self.ax2.set_xlabel("Días hasta agotar masa", color='#AFA196')
        self.ax2.set_ylabel("Probabilidad (%)", color='#AFA196')
        self.ax2.legend(facecolor='#2D2320', edgecolor='#4A3C37', labelcolor='#F4F0EA', fontsize=8, loc='upper right')
        
        # Configurar las etiquetas del eje X como números enteros
        self.ax2.set_xticks(valores)
        
        self.fig2.tight_layout()
        self.canvas2.draw()

    def actualizar_estadisticas_simulacion(self, res, masa):
        """Actualiza los valores de las tarjetas KPI del simulador basándose en los resultados de Montecarlo."""
        # 1. Agotamiento promedio
        self.lbl_sim_prom.configure(text=f"Promedio: {res['dias_promedio']} días")
        self.lbl_sim_mediana.configure(text=f"Mediana: {res['dias_mediana']} días")
        
        # 2. Rangos de confianza
        self.lbl_sim_certeza.configure(text=f"Certeza: {res['p5']} a {res['p95']} días")
        self.lbl_sim_rango.configure(text=f"Absoluto: {res['dias_min']} a {res['dias_max']} días")
        
        # 3. Calcular probabilidad de agotarse en 2 días o menos (riesgo de stockout)
        prob_bajo_2 = res['distribucion_probabilidad'].get(1, 0.0) + res['distribucion_probabilidad'].get(2, 0.0)
        prob_riesgo = prob_bajo_2 * 100
        self.lbl_sim_riesgo.configure(text=f"≤ 2 Días: {prob_riesgo:.2f}%")
        
        # 4. Determinar nivel de alerta visual
        if prob_riesgo > 50:
            riesgo_text = "CRÍTICO"
            riesgo_color = "#E74C3C"  # Rojo
        elif prob_riesgo > 20:
            riesgo_text = "ALTO"
            riesgo_color = "#E67E22"  # Naranja
        elif prob_riesgo > 5:
            riesgo_text = "MEDIO"
            riesgo_color = "#F1C40F"  # Amarillo
        else:
            riesgo_text = "BAJO"
            riesgo_color = "#2ECC71"  # Verde
            
        self.lbl_sim_nivel_riesgo.configure(text=f"Nivel: {riesgo_text}", text_color=riesgo_color)

    def accion_generar_y_cargar(self):
        """Genera nuevos consumos históricos y los carga inmediatamente en el visor."""
        try:
            dias = self.validar_entero(self.entry_dias_hist.get(), "Días Históricos")
            media_gen = self.validar_flotante(self.entry_media_gen.get(), "Consumo Promedio Base")
            desv_gen = self.validar_flotante(self.entry_desv_gen.get(), "Desviación Estándar Base")
            
            self.set_status("Generando y analizando consumo histórico...")
            self.update_idletasks()
            
            ruta_csv = "consumo_historico.csv"
            # Llama a la función del backend para generar
            generar_consumo_historico(dias=dias, media=media_gen, desviacion=desv_gen, ruta_csv=ruta_csv)
            
            # Cargar en el frontend
            self.actualizar_historico(ruta_csv)
            self.set_status("Datos históricos generados y analizados correctamente.")
        except Exception as e:
            self.set_status(f"Error: {e}", is_error=True)
            messagebox.showerror("Error de Entrada", str(e))
            
    def accion_simular(self):
        """Ejecuta la simulación de Montecarlo basándose en el consumo histórico."""
        try:
            # Validar campos de entrada
            masa = self.validar_flotante(self.entry_masa.get(), "Cantidad de Masa a Evaluar")
            iteraciones = self.validar_entero(self.entry_iter.get(), "Iteraciones Montecarlo")
            
            # Si no hay histórico cargado, intentar generar uno base
            if not hasattr(self, 'media') or not hasattr(self, 'desviacion'):
                ruta_csv = "consumo_historico.csv"
                if not os.path.exists(ruta_csv):
                    self.set_status("Histórico ausente. Generando valores por defecto primero...")
                    self.update_idletasks()
                    generar_consumo_historico(dias=200, media=330.0, desviacion=40.0, ruta_csv=ruta_csv)
                
                self.actualizar_historico(ruta_csv)
                
            self.set_status(f"Simulando agotamiento con {iteraciones:,} iteraciones...")
            self.update_idletasks()
            
            # Ejecutar simulación Montecarlo desde el backend
            res = simular_dias_agotamiento(
                inventario_objetivo=masa,
                media=self.media,
                desviacion=self.desviacion,
                iteraciones=iteraciones
            )
            
            # Actualizar interfaz de usuario con estadísticas y gráficos
            self.actualizar_estadisticas_simulacion(res, masa)
            self.actualizar_plot_simulacion(res)
            
            self.set_status("Simulación completada con éxito.")
        except Exception as e:
            self.set_status(f"Error: {e}", is_error=True)
            messagebox.showerror("Error de Simulación", str(e))

if __name__ == "__main__":
    app = MonteCarloGUI()
    app.mainloop()

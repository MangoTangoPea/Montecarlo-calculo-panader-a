import os
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from data_simulator import generar_consumo_historico
from estimator import cargar_y_analizar_historico
from monte_carlo import simular_dias_agotamiento

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MonteCarloGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Panadería Montecarlo — Predicción y Simulación de Inventario")
        self.geometry("1380x860")
        self.minsize(1100, 720)
        self.configure(fg_color='#1A1412')

        # Rejilla principal: sidebar | área de tabs
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.inicializar_sidebar()
        self.inicializar_tabs()
        self.cargar_historico_inicial()
        self.protocol("WM_DELETE_WINDOW", self._cerrar_sistema)

    # ──────────────────────────────────────────────────────────
    # SIDEBAR
    # ──────────────────────────────────────────────────────────

    def inicializar_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(
            self, width=310, corner_radius=0,
            fg_color='#231B19', border_color='#3D302C', border_width=1
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        cf = ctk.CTkFrame(self.sidebar_frame, fg_color='transparent')
        cf.pack(fill=tk.BOTH, expand=True, padx=20, pady=25)

        # Título
        ctk.CTkLabel(cf, text="MONTECARLO",
            font=ctk.CTkFont(family="Georgia", size=26, weight="bold"),
            text_color='#D4AF37').pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(cf, text="Simulación de Inventario de Masa",
            font=ctk.CTkFont(family="Arial", size=12, slant="italic"),
            text_color='#AFA196').pack(anchor="w", pady=(0, 15))

        ctk.CTkFrame(cf, height=2, fg_color='#3D302C').pack(fill=tk.X, pady=(0, 20))

        # Sección 1: Histórico
        ctk.CTkLabel(cf, text="1. CONSUMO HISTÓRICO",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            text_color='#D4AF37').pack(anchor="w", pady=(0, 10))

        self.lbl_info_media = ctk.CTkLabel(cf, text="Media (µ): -- kg",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            text_color='#F4F0EA')
        self.lbl_info_media.pack(anchor="w", pady=(0, 4))

        self.lbl_info_desv = ctk.CTkLabel(cf, text="Desv. Est. (σ): -- kg",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            text_color='#F4F0EA')
        self.lbl_info_desv.pack(anchor="w", pady=(0, 12))

        # Botón "Ver Datos" → cambia al tab de datos
        ctk.CTkButton(cf, text="Ver / Editar Datos",
            fg_color='#D4AF37', hover_color='#B2902C', text_color='#1A1412',
            font=ctk.CTkFont(family="Arial", size=13, weight="bold"),
            height=36, command=self._ir_tab_datos
        ).pack(fill=tk.X, pady=(0, 8))

        ctk.CTkButton(cf, text="Subir Archivo CSV",
            fg_color='#AFA196', hover_color='#8C7E74', text_color='#1A1412',
            font=ctk.CTkFont(family="Arial", size=13, weight="bold"),
            height=36, command=self.accion_subir_csv
        ).pack(fill=tk.X, pady=(0, 8))

        ctk.CTkButton(cf, text="Quitar CSV Cargado",
            fg_color='#4A1E1E', hover_color='#611A1A', text_color='#E74C3C',
            font=ctk.CTkFont(family="Arial", size=13, weight="bold"),
            height=36, command=self.accion_quitar_csv
        ).pack(fill=tk.X, pady=(0, 22))

        ctk.CTkFrame(cf, height=1, fg_color='#3D302C').pack(fill=tk.X, pady=(0, 18))

        # Sección 2: Simulación
        ctk.CTkLabel(cf, text="2. SIMULACIÓN MONTECARLO",
            font=ctk.CTkFont(family="Arial", size=12, weight="bold"),
            text_color='#D4AF37').pack(anchor="w", pady=(0, 10))

        self._crear_entry(cf, "Masa a evaluar (kg):", "300.0", "_masa")
        self._crear_entry(cf, "Iteraciones:", "10000", "_iter")

        ctk.CTkButton(cf, text="Ejecutar Simulación",
            fg_color='#D4AF37', hover_color='#B2902C', text_color='#1A1412',
            font=ctk.CTkFont(family="Arial", size=13, weight="bold"),
            height=36, command=self.accion_simular
        ).pack(fill=tk.X, pady=(12, 22))

        ctk.CTkFrame(cf, height=1, fg_color='#3D302C').pack(fill=tk.X, pady=(0, 14))

        # Estado
        ctk.CTkLabel(cf, text="ESTADO DEL SISTEMA:",
            font=ctk.CTkFont(family="Arial", size=10, weight="bold"),
            text_color='#AFA196').pack(anchor="w", pady=(0, 2))

        self.lbl_status = ctk.CTkLabel(cf, text="Inicializando...",
            font=ctk.CTkFont(family="Arial", size=11), text_color='#AFA196',
            justify="left", anchor="w", wraplength=265)
        self.lbl_status.pack(fill=tk.X, anchor="w")

        # Separador final
        ctk.CTkFrame(cf, height=1, fg_color='#3D302C').pack(fill=tk.X, pady=(18, 12))

        # Botón cerrar sistema
        ctk.CTkButton(cf, text="✕  Cerrar Sistema",
            fg_color='#4A1E1E', hover_color='#6B1F1F', text_color='#E74C3C',
            font=ctk.CTkFont(family="Arial", size=13, weight="bold"),
            border_color='#6B1F1F', border_width=1,
            height=36, command=self._cerrar_sistema
        ).pack(fill=tk.X)

    def _crear_entry(self, parent, label_text, default, suffix):
        ctk.CTkLabel(parent, text=label_text,
            font=ctk.CTkFont(family="Arial", size=11),
            text_color='#AFA196').pack(anchor="w", pady=(0, 2))
        e = ctk.CTkEntry(parent, fg_color='#2D2320', text_color='#F4F0EA',
            border_color='#4A3B37', border_width=1, corner_radius=6,
            height=30, font=ctk.CTkFont(family="Arial", size=12))
        e.insert(0, default)
        e.pack(fill=tk.X, pady=(0, 10))
        setattr(self, f"entry{suffix}", e)

    def _cerrar_sistema(self):
        """Cierra de forma limpia todos los recursos y termina el proceso."""
        try:
            plt.close('all')
        except Exception:
            pass
        try:
            self.quit()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def set_status(self, message, is_error=False):
        color = "#D98880" if is_error else "#AFA196"
        self.lbl_status.configure(text=message, text_color=color)

    # ──────────────────────────────────────────────────────────
    # TABS
    # ──────────────────────────────────────────────────────────

    def inicializar_tabs(self):
        self.tabview = ctk.CTkTabview(
            self, fg_color='#1A1412',
            segmented_button_fg_color='#231B19',
            segmented_button_selected_color='#D4AF37',
            segmented_button_selected_hover_color='#B2902C',
            segmented_button_unselected_color='#231B19',
            segmented_button_unselected_hover_color='#2D2320',
            text_color='#F4F0EA',
            text_color_disabled='#AFA196',
            border_color='#3D302C', border_width=1,
        )
        self.tabview.grid(row=0, column=1, sticky="nsew", padx=14, pady=14)

        self.tabview.add("Panel Principal")
        self.tabview.add("Datos Historicos")
        self.tabview.add("Resultados Simulación")
 
        self._build_tab_principal(self.tabview.tab("Panel Principal"))
        self._build_tab_datos(self.tabview.tab("Datos Historicos"))
        self._build_tab_simulacion_inicial(self.tabview.tab("Resultados Simulación"))
        self._decorate_tabview_buttons(self.tabview)

    # ── Tab 1: Panel Principal ────────────────────────────────

    def _build_tab_principal(self, tab):
        tab.columnconfigure((0, 1, 2, 3), weight=1)
        tab.rowconfigure(0, weight=0)
        tab.rowconfigure(1, weight=1)

        # 4 KPI cards
        self.card_hist, self.lbl_hist_media, self.lbl_hist_desv = self._kpi_card(
            tab, "Histórico Consumo", "Promedio: --", "Desviación: --")
        self.card_sim_tiempo, self.lbl_sim_prom, self.lbl_sim_mediana = self._kpi_card(
            tab, "Agotamiento Estimado", "Promedio: --", "Mediana: --")
        self.card_sim_certeza, self.lbl_sim_certeza, self.lbl_sim_rango = self._kpi_card(
            tab, "Rangos y Confianza", "Certeza (90%): --", "Absoluto: --")
        self.card_sim_riesgo, self.lbl_sim_riesgo, self.lbl_sim_nivel_riesgo = self._kpi_card(
            tab, "Alerta de Inventario", "Agotamiento ≤ 2 Días: --", "Nivel: --")

        for col, card in enumerate([self.card_hist, self.card_sim_tiempo,
                                    self.card_sim_certeza, self.card_sim_riesgo]):
            card.grid(row=0, column=col, sticky="nsew",
                      padx=(0 if col == 0 else 5, 5 if col < 3 else 0), pady=(0, 12))

        # Gráficos
        plots = ctk.CTkFrame(tab, fg_color='transparent')
        plots.grid(row=1, column=0, columnspan=4, sticky="nsew")
        plots.columnconfigure((0, 1), weight=1)
        plots.rowconfigure(0, weight=1)

        self.plot_frame_left = ctk.CTkFrame(plots, fg_color='#2D2320',
            border_color='#3D302C', border_width=1, corner_radius=8)
        self.plot_frame_left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.plot_frame_right = ctk.CTkFrame(plots, fg_color='#2D2320',
            border_color='#3D302C', border_width=1, corner_radius=8)
        self.plot_frame_right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self._inicializar_graficos()

    def _decorate_tabview_buttons(self, tabview):
        button_group = tabview._segmented_button
        original_command = button_group._command

        def wrapped_command(selected_name):
            if original_command:
                original_command(selected_name)
            self._refresh_segmented_button_text_colors(button_group)

        button_group.configure(command=wrapped_command)
        self._refresh_segmented_button_text_colors(button_group)

    def _refresh_segmented_button_text_colors(self, button_group):
        selected_name = button_group.get()
        for name, button in button_group._buttons_dict.items():
            button.configure(text_color='#1A1412' if name == selected_name else '#F4F0EA')

    def _kpi_card(self, master, titulo, v1, v2):
        f = ctk.CTkFrame(master, fg_color='#2D2320',
            border_color='#3D302C', border_width=1, corner_radius=8)
        ctk.CTkLabel(f, text=titulo.upper(),
            font=ctk.CTkFont(family="Arial", size=10, weight="bold"),
            text_color='#AFA196').pack(anchor="w", padx=15, pady=(12, 4))
        l1 = ctk.CTkLabel(f, text=v1,
            font=ctk.CTkFont(family="Georgia", size=18, weight="bold"),
            text_color='#F4F0EA')
        l1.pack(anchor="w", padx=15, pady=(0, 2))
        l2 = ctk.CTkLabel(f, text=v2,
            font=ctk.CTkFont(family="Arial", size=12), text_color='#AFA196')
        l2.pack(anchor="w", padx=15, pady=(0, 12))
        return f, l1, l2

    def _inicializar_graficos(self):
        self.fig1, self.ax1 = plt.subplots(figsize=(5, 4.2), dpi=100)
        self._estilo_ax(self.fig1, self.ax1)
        self.ax1.text(0.5, 0.5, "Esperando datos históricos...",
                      color='#AFA196', ha='center', va='center',
                      transform=self.ax1.transAxes)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.plot_frame_left)
        self.canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.fig2, self.ax2 = plt.subplots(figsize=(5, 4.2), dpi=100)
        self._estilo_ax(self.fig2, self.ax2)
        self.ax2.text(0.5, 0.5, "Esperando simulación...",
                      color='#AFA196', ha='center', va='center',
                      transform=self.ax2.transAxes)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.plot_frame_right)
        self.canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # ── Tab 2: Datos Históricos ───────────────────────────────

    def _build_tab_datos(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        from ventana_datos import VentanaDatos
        self.frame_datos = VentanaDatos(tab, on_save_callback=self.actualizar_historico)
        self.frame_datos.grid(row=0, column=0, sticky="nsew")

    # ── Tab 3: Resultados de Simulación Inicial ───────────────

    def _build_tab_simulacion_inicial(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        self.tab_sim_container = tab

        self.lbl_no_sim = ctk.CTkLabel(
            tab,
            text="Ejecute una simulación en el panel izquierdo para ver los resultados aquí.",
            font=ctk.CTkFont(family="Georgia", size=14, slant="italic"),
            text_color='#AFA196'
        )
        self.lbl_no_sim.grid(row=0, column=0)

    def _ir_tab_datos(self):
        self.tabview.set("Datos Historicos")

    # ──────────────────────────────────────────────────────────
    # ESTILO DE GRÁFICOS
    # ──────────────────────────────────────────────────────────

    def _estilo_ax(self, fig, ax):
        fig.patch.set_facecolor('#2D2320')
        ax.set_facecolor('#2D2320')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#4A3C37')
        ax.spines['bottom'].set_color('#4A3C37')
        ax.tick_params(colors='#AFA196', labelsize=9)
        ax.xaxis.label.set_color('#AFA196')
        ax.xaxis.label.set_size(10)
        ax.yaxis.label.set_color('#AFA196')
        ax.yaxis.label.set_size(10)
        ax.grid(True, color='#3D302C', linestyle=':', alpha=0.6)

    # ──────────────────────────────────────────────────────────
    # LÓGICA DE DATOS
    # ──────────────────────────────────────────────────────────

    def cargar_historico_inicial(self):
        self.media = None
        self.desviacion = None
        self.lbl_info_media.configure(text="Media (µ): -- kg")
        self.lbl_info_desv.configure(text="Desv. Est. (σ): -- kg")
        self.lbl_hist_media.configure(text="Promedio: --")
        self.lbl_hist_desv.configure(text="Desviación: --")
        self.set_status("Listo. Cargue un archivo CSV manualmente para comenzar.")

    def actualizar_historico(self, ruta_csv):
        media, desviacion = cargar_y_analizar_historico(ruta_csv)
        self.media = media
        self.desviacion = desviacion

        self.lbl_hist_media.configure(text=f"Promedio: {media:.2f} kg")
        self.lbl_hist_desv.configure(text=f"Desviación: {desviacion:.2f} kg")
        self.lbl_info_media.configure(text=f"Media (µ): {media:.2f} kg")
        self.lbl_info_desv.configure(text=f"Desv. Est. (σ): {desviacion:.2f} kg")

        df = pd.read_csv(ruta_csv)
        consumos = df['Consumo_Kg'].values
        self._plot_historico(consumos, media, desviacion)

    def _plot_historico(self, consumos, media, desviacion):
        self.ax1.clear()
        self._estilo_ax(self.fig1, self.ax1)

        self.ax1.hist(consumos, bins=25, density=True, alpha=0.5,
                      color='#C5A059', edgecolor='#2D2320', label='Consumo Empírico')
        xmin, xmax = self.ax1.get_xlim()
        x = np.linspace(xmin, xmax, 100)
        p = (1.0 / (desviacion * np.sqrt(2.0 * np.pi))) * np.exp(-0.5 * ((x - media) / desviacion) ** 2)
        self.ax1.plot(x, p, color='#D4AF37', linewidth=2.5, label='Dist. Normal')
        self.ax1.axvline(media, color='#F4F0EA', linestyle='--', linewidth=1.5,
                         label=f'Media: {media:.1f} kg')
        self.ax1.set_title("Distribución del Consumo Diario",
                           color='#F4F0EA', fontsize=12, pad=10, weight='bold')
        self.ax1.set_xlabel("Consumo diario (kg)")
        self.ax1.set_ylabel("Densidad")
        self.ax1.legend(facecolor='#2D2320', edgecolor='#4A3C37',
                        labelcolor='#F4F0EA', fontsize=8)
        self.fig1.tight_layout()
        self.canvas1.draw()

    def _plot_simulacion(self, res):
        self.ax2.clear()
        self._estilo_ax(self.fig2, self.ax2)

        valores = sorted(res["distribucion_probabilidad"].keys())
        probs   = [res["distribucion_probabilidad"][v] * 100 for v in valores]

        self.ax2.bar(valores, probs, color='#D4AF37', alpha=0.6,
                     edgecolor='#2D2320', width=0.6, label='Probabilidad')

        prom = res["dias_promedio"]
        p5   = res["p5"]
        p95  = res["p95"]
        self.ax2.axvline(prom, color='#F4F0EA', linestyle='-', linewidth=2,
                         label=f'Promedio ({prom} d)')
        self.ax2.axvline(p5,  color='#E67E22', linestyle='--', linewidth=1.5,
                         label=f'P5 ({p5} d)')
        self.ax2.axvline(p95, color='#2ECC71', linestyle='--', linewidth=1.5,
                         label=f'P95 ({p95} d)')
        self.ax2.axvspan(p5, p95, color='#D4AF37', alpha=0.1, label='Certeza 90%')

        self.ax2.set_title("Probabilidad de Agotamiento",
                           color='#F4F0EA', fontsize=12, pad=10, weight='bold')
        self.ax2.set_xlabel("Días hasta agotar masa")
        self.ax2.set_ylabel("Probabilidad (%)")
        self.ax2.set_xticks(valores)
        self.ax2.legend(facecolor='#2D2320', edgecolor='#4A3C37',
                        labelcolor='#F4F0EA', fontsize=8)
        self.fig2.tight_layout()
        self.canvas2.draw()

    def _actualizar_kpis_simulacion(self, res, masa):
        self.lbl_sim_prom.configure(text=f"Promedio: {res['dias_promedio']} días")
        self.lbl_sim_mediana.configure(text=f"Mediana: {res['dias_mediana']} días")
        self.lbl_sim_certeza.configure(text=f"Certeza: {res['p5']} a {res['p95']} días")
        self.lbl_sim_rango.configure(text=f"Absoluto: {res['dias_min']} a {res['dias_max']} días")

        prob_bajo_2 = (res['distribucion_probabilidad'].get(1, 0.0) +
                       res['distribucion_probabilidad'].get(2, 0.0))
        prob_riesgo = prob_bajo_2 * 100
        self.lbl_sim_riesgo.configure(text=f"≤ 2 Días: {prob_riesgo:.2f}%")

        if prob_riesgo > 50:
            t, c = "CRÍTICO", "#E74C3C"
        elif prob_riesgo > 20:
            t, c = "ALTO", "#E67E22"
        elif prob_riesgo > 5:
            t, c = "MEDIO", "#F1C40F"
        else:
            t, c = "BAJO", "#2ECC71"
        self.lbl_sim_nivel_riesgo.configure(text=f"Nivel: {t}", text_color=c)

    # ──────────────────────────────────────────────────────────
    # ACCIONES
    # ──────────────────────────────────────────────────────────

    def accion_subir_csv(self):
        try:
            ruta = filedialog.askopenfilename(
                title="Seleccionar CSV de Consumo",
                filetypes=[("Archivos CSV", "*.csv")]
            )
            if not ruta:
                return
            self.set_status("Validando archivo...")
            self.update_idletasks()
            media, desviacion = cargar_y_analizar_historico(ruta)
            self.actualizar_historico(ruta)
            # Recargar frame de datos si ya está creado
            if hasattr(self, 'frame_datos'):
                self.frame_datos.cargar_csv(ruta)
            self.set_status("CSV cargado y procesado correctamente.")
        except Exception as e:
            self.set_status(f"Error: {e}", is_error=True)
            messagebox.showerror("Error al Cargar CSV", str(e))

    def accion_quitar_csv(self):
        self.media = None
        self.desviacion = None
        self.lbl_info_media.configure(text="Media (µ): -- kg")
        self.lbl_info_desv.configure(text="Desv. Est. (σ): -- kg")
        self.lbl_hist_media.configure(text="Promedio: --")
        self.lbl_hist_desv.configure(text="Desviación: --")

        # Limpiar gráficos principales
        self.ax1.clear()
        self._estilo_ax(self.fig1, self.ax1)
        self.ax1.text(0.5, 0.5, "Esperando datos históricos...",
                      color='#AFA196', ha='center', va='center',
                      transform=self.ax1.transAxes)
        self.canvas1.draw()

        self.ax2.clear()
        self._estilo_ax(self.fig2, self.ax2)
        self.ax2.text(0.5, 0.5, "Esperando simulación...",
                      color='#AFA196', ha='center', va='center',
                      transform=self.ax2.transAxes)
        self.canvas2.draw()

        # Limpiar pestaña de simulación si tiene un frame activo
        for child in self.tab_sim_container.winfo_children():
            if child != self.lbl_no_sim:
                child.destroy()
        self.lbl_no_sim.grid(row=0, column=0)

        # Limpiar frame de datos si existe
        if hasattr(self, 'frame_datos'):
            self.frame_datos.current_csv_path = None
            for item in self.frame_datos.tree.get_children():
                self.frame_datos.tree.delete(item)
            for key in self.frame_datos.stat_labels:
                self.frame_datos.stat_labels[key].configure(text="--")
            self.frame_datos.ax_dist.clear()
            self.frame_datos._estilizar_ax(self.frame_datos.fig_dist, self.frame_datos.ax_dist)
            self.frame_datos.ax_dist.text(0.5, 0.5, "Sin datos cargados", color='#AFA196',
                                          ha='center', va='center', transform=self.frame_datos.ax_dist.transAxes, fontsize=10)
            self.frame_datos.canvas_dist.draw()

        self.set_status("CSV quitado. Sistema en blanco.")

    def accion_simular(self):
        try:
            masa = float(self.entry_masa.get())
            if masa <= 0:
                raise ValueError("La masa debe ser mayor a 0.")
            iteraciones = int(self.entry_iter.get())
            if iteraciones < 1:
                raise ValueError("Las iteraciones deben ser ≥ 1.")

            if getattr(self, 'media', None) is None or getattr(self, 'desviacion', None) is None:
                messagebox.showwarning("Falta Histórico", "Debe cargar un archivo CSV de consumos históricos antes de ejecutar una simulación.", parent=self)
                self.set_status("Error: No se ha cargado ningún histórico.", is_error=True)
                return

            self.set_status(f"Simulando con {iteraciones:,} iteraciones...")
            self.update_idletasks()

            res = simular_dias_agotamiento(
                inventario_objetivo=masa,
                media=self.media,
                desviacion=self.desviacion,
                iteraciones=iteraciones
            )

            self._actualizar_kpis_simulacion(res, masa)
            self._plot_simulacion(res)

            # Limpiar pestaña de simulación
            for child in self.tab_sim_container.winfo_children():
                child.destroy()

            # Instanciar el nuevo frame de resultados de simulación dentro del tab
            from ventana_simulacion import VentanaSimulacionFrame
            self.frame_simulacion = VentanaSimulacionFrame(self.tab_sim_container, res, masa, iteraciones)
            self.frame_simulacion.grid(row=0, column=0, sticky='nsew')

            # Cambiar a la pestaña de simulación
            self.tabview.set("Resultados Simulación")

            self.set_status("Simulación completada.")
        except Exception as e:
            self.set_status(f"Error: {e}", is_error=True)
            messagebox.showerror("Error de Simulación", str(e))


if __name__ == "__main__":
    app = MonteCarloGUI()
    app.mainloop()

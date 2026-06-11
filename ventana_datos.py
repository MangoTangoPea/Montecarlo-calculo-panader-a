"""
ventana_datos.py
Frame embebible (no CTkToplevel) para ver, generar y editar
los datos históricos de consumo diario de masa.
Puede usarse directamente dentro de un CTkTabview en gui.py.
"""
import os
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import customtkinter as ctk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from data_simulator import generar_consumo_historico


class VentanaDatos(ctk.CTkFrame):
    """Frame embebible: tabla editable + estadísticas + explicación de Montecarlo."""

    def __init__(self, master, on_save_callback=None, **kwargs):
        kwargs.setdefault('fg_color', '#1A1412')
        super().__init__(master, **kwargs)
        self.on_save_callback = on_save_callback
        self.current_csv_path = None
        self._build_ui()

    # ──────────────────────────────────────────────────────────
    # CONSTRUCCIÓN DE INTERFAZ
    # ──────────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(0, weight=5)
        self.columnconfigure(1, weight=4)
        self.rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color='#231B19', corner_radius=10,
                            border_color='#3D302C', border_width=1)
        left.grid(row=0, column=0, sticky='nsew', padx=(15, 6), pady=15)

        right = ctk.CTkScrollableFrame(self, fg_color='#231B19', corner_radius=10,
                                       border_color='#3D302C', border_width=1)
        right.grid(row=0, column=1, sticky='nsew', padx=(6, 15), pady=15)

        self._build_left(left)
        self._build_right(right)

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

    # ── Panel izquierdo: controles + tabla ───────────────────

    def _build_left(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        # Crear Tabview interno
        self.left_tabview = ctk.CTkTabview(
            parent, fg_color='transparent',
            segmented_button_fg_color='#2D2320',
            segmented_button_selected_color='#D4AF37',
            segmented_button_selected_hover_color='#B2902C',
            segmented_button_unselected_color='#2D2320',
            segmented_button_unselected_hover_color='#3D302C',
            text_color='#F4F0EA',
            text_color_disabled='#AFA196',
        )
        self.left_tabview.grid(row=0, column=0, sticky='nsew', padx=8, pady=8)

        tab_hist = self.left_tabview.add("Consumo Histórico")
        tab_gen = self.left_tabview.add("Generar Datos")

        self._build_tab_historico(tab_hist)
        self._build_tab_generador(tab_gen)
        self._decorate_tabview_buttons(self.left_tabview)

    def _build_tab_historico(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)  # La tabla se expande

        # Encabezado
        ctk.CTkLabel(tab, text="TABLA DE CONSUMO HISTÓRICO",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            text_color='#D4AF37'
        ).grid(row=0, column=0, sticky='w', padx=10, pady=(10, 2))

        ctk.CTkLabel(tab,
            text="Doble clic en 'Consumo (kg)' para editar un valor histórico directamente.",
            font=ctk.CTkFont(size=10), text_color='#6E5E58', wraplength=450, justify='left'
        ).grid(row=1, column=0, sticky='w', padx=10, pady=(0, 8))

        # Treeview
        tree_outer = tk.Frame(tab, bg='#2D2320')
        tree_outer.grid(row=2, column=0, sticky='nsew', padx=8, pady=4)

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('VD.Treeview',
            background='#2D2320', foreground='#F4F0EA',
            rowheight=26, fieldbackground='#2D2320', font=('Arial', 11))
        style.configure('VD.Treeview.Heading',
            background='#3D302C', foreground='#D4AF37', font=('Arial', 11, 'bold'))
        style.map('VD.Treeview', background=[('selected', '#4A3B37')])

        self.tree = ttk.Treeview(tree_outer, columns=('Index', 'Fecha', 'Consumo_Kg'),
                                 show='headings', style='VD.Treeview')
        self.tree.heading('Index', text='Nº')
        self.tree.heading('Fecha', text='Fecha')
        self.tree.heading('Consumo_Kg', text='Consumo (kg)')
        self.tree.column('Index', width=50, anchor='center')
        self.tree.column('Fecha', width=150, anchor='center')
        self.tree.column('Consumo_Kg', width=140, anchor='center')

        vsb = ttk.Scrollbar(tree_outer, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', self._on_double_click)

        # Panel inferior de controles: Añadir, Eliminar, Guardar Cambios
        btn_frame = ctk.CTkFrame(tab, fg_color='transparent')
        btn_frame.grid(row=3, column=0, sticky='ew', padx=8, pady=(8, 10))

        ctk.CTkButton(btn_frame, text="Añadir Datos...",
            fg_color='#2D4A2D', hover_color='#3A613A', text_color='#7CFC00',
            font=ctk.CTkFont(size=12, weight="bold"), border_color='#3A613A',
            border_width=1, height=32, command=self._abrir_popup_añadir_datos
        ).pack(side=tk.LEFT, padx=(0, 6), fill=tk.X, expand=True)


        ctk.CTkButton(btn_frame, text="Eliminar Fila",
            fg_color='#4A1E1E', hover_color='#611A1A', text_color='#E74C3C',
            font=ctk.CTkFont(size=12, weight="bold"), border_color='#611A1A',
            border_width=1, height=32, command=self._eliminar_fila_historico
        ).pack(side=tk.LEFT, padx=(0, 6), fill=tk.X, expand=True)

        ctk.CTkButton(btn_frame, text="Guardar Cambios",
            fg_color='#D4AF37', hover_color='#B2902C', text_color='#1A1412',
            font=ctk.CTkFont(size=12, weight="bold"), height=32,
            command=self._guardar_y_cargar
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _build_tab_generador(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(3, weight=1)  # La tabla de vista previa se expande

        # Encabezado
        ctk.CTkLabel(tab, text="GENERADOR DE DATOS DE CONSUMO",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            text_color='#D4AF37'
        ).grid(row=0, column=0, sticky='w', padx=10, pady=(10, 2))

        ctk.CTkLabel(tab,
            text="Simule datos gaussianos y edite la vista previa antes de guardarla.",
            font=ctk.CTkFont(size=10), text_color='#6E5E58', wraplength=450, justify='left'
        ).grid(row=1, column=0, sticky='w', padx=10, pady=(0, 8))

        # Panel de parámetros (Fila 2)
        params_frame = ctk.CTkFrame(tab, fg_color='#2D2320', corner_radius=6)
        params_frame.grid(row=2, column=0, sticky='ew', padx=8, pady=(0, 6))

        # Formato de los campos
        ctk.CTkLabel(params_frame, text="Registros:", font=ctk.CTkFont(size=11), text_color='#AFA196').grid(row=0, column=0, padx=(8, 2), pady=8, sticky='w')
        self.entry_cantidad = ctk.CTkEntry(params_frame, width=50, fg_color='#1A1412', text_color='#F4F0EA', border_color='#4A3B37', font=ctk.CTkFont(size=11))
        self.entry_cantidad.insert(0, "200")
        self.entry_cantidad.grid(row=0, column=1, padx=2, pady=8)

        ctk.CTkLabel(params_frame, text="µ:", font=ctk.CTkFont(size=11), text_color='#AFA196').grid(row=0, column=2, padx=(8, 2), pady=8, sticky='w')
        self.entry_media_base = ctk.CTkEntry(params_frame, width=50, fg_color='#1A1412', text_color='#F4F0EA', border_color='#4A3B37', font=ctk.CTkFont(size=11))
        self.entry_media_base.insert(0, "62.5")
        self.entry_media_base.grid(row=0, column=3, padx=2, pady=8)

        ctk.CTkLabel(params_frame, text="σ:", font=ctk.CTkFont(size=11), text_color='#AFA196').grid(row=0, column=4, padx=(8, 2), pady=8, sticky='w')
        self.entry_desv_base = ctk.CTkEntry(params_frame, width=50, fg_color='#1A1412', text_color='#F4F0EA', border_color='#4A3B37', font=ctk.CTkFont(size=11))
        self.entry_desv_base.insert(0, "12.5")
        self.entry_desv_base.grid(row=0, column=5, padx=2, pady=8)

        btn_generar = ctk.CTkButton(params_frame, text="Simular", command=self._generar_datos_vista_previa,
            fg_color='#D4AF37', hover_color='#B2902C', text_color='#1A1412',
            font=ctk.CTkFont(size=11, weight="bold"), width=75, height=26)
        btn_generar.grid(row=0, column=6, padx=(10, 8), pady=8)

        # Fila 3: Tabla de vista previa
        tree_outer = tk.Frame(tab, bg='#2D2320')
        tree_outer.grid(row=3, column=0, sticky='nsew', padx=8, pady=4)

        self.preview_tree = ttk.Treeview(tree_outer, columns=('Index', 'Fecha', 'Consumo_Kg'),
                                         show='headings', style='VD.Treeview')
        self.preview_tree.heading('Index', text='Nº')
        self.preview_tree.heading('Fecha', text='Fecha (Vista Previa)')
        self.preview_tree.heading('Consumo_Kg', text='Consumo (kg)')
        self.preview_tree.column('Index', width=50, anchor='center')
        self.preview_tree.column('Fecha', width=150, anchor='center')
        self.preview_tree.column('Consumo_Kg', width=140, anchor='center')

        p_vsb = ttk.Scrollbar(tree_outer, orient='vertical', command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=p_vsb.set)
        p_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_tree.pack(fill=tk.BOTH, expand=True)
        self.preview_tree.bind('<Double-1>', self._on_double_click)

        # Fila 4: Conteo de vista previa y botones de edición de vista previa
        preview_ctrl = ctk.CTkFrame(tab, fg_color='transparent')
        preview_ctrl.grid(row=4, column=0, sticky='ew', padx=8, pady=(4, 4))

        self.lbl_preview_count = ctk.CTkLabel(preview_ctrl, text="Registros en vista previa: 0",
            font=ctk.CTkFont(size=11, slant="italic"), text_color='#AFA196')
        self.lbl_preview_count.pack(side=tk.LEFT, padx=(2, 10))

        ctk.CTkButton(preview_ctrl, text="Añadir Día",
            fg_color='#2D4A2D', hover_color='#3A613A', text_color='#7CFC00',
            font=ctk.CTkFont(size=10, weight="bold"), border_color='#3A613A',
            border_width=1, width=85, height=24, command=self._añadir_fila_preview
        ).pack(side=tk.RIGHT, padx=(0, 4))

        ctk.CTkButton(preview_ctrl, text="Eliminar Fila",
            fg_color='#4A1E1E', hover_color='#611A1A', text_color='#E74C3C',
            font=ctk.CTkFont(size=10, weight="bold"), border_color='#611A1A',
            border_width=1, width=85, height=24, command=self._eliminar_fila_preview
        ).pack(side=tk.RIGHT)

        # Fila 5: Botones de guardar integrados
        integration_frame = ctk.CTkFrame(tab, fg_color='transparent')
        integration_frame.grid(row=5, column=0, sticky='ew', padx=8, pady=(6, 10))

        ctk.CTkButton(integration_frame, text="Anexar al Histórico",
            fg_color='#231B19', hover_color='#2D2320', text_color='#D4AF37',
            font=ctk.CTkFont(size=12, weight="bold"), border_color='#D4AF37',
            border_width=1, height=36, command=self._anexar_al_historico
        ).pack(side=tk.LEFT, padx=(0, 6), fill=tk.X, expand=True)

        ctk.CTkButton(integration_frame, text="Reemplazar Histórico",
            fg_color='#D4AF37', hover_color='#B2902C', text_color='#1A1412',
            font=ctk.CTkFont(size=12, weight="bold"), height=36,
            command=self._reemplazar_historico
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    # ── Panel derecho: estadísticas + gráfico + explicación ──

    def _build_right(self, parent):
        # ─ Estadísticas ─
        ctk.CTkLabel(parent, text="ESTADÍSTICAS DEL HISTÓRICO",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            text_color='#D4AF37'
        ).pack(anchor='w', padx=5, pady=(10, 6))

        stats_outer = ctk.CTkFrame(parent, fg_color='transparent')
        stats_outer.pack(fill=tk.X, padx=5, pady=(0, 12))
        stats_outer.columnconfigure((0, 1), weight=1)

        self.stat_labels = {}
        stats_config = [
            ("μ  (Media)",      "mean",   "1er momento estadístico.\nConsumo diario esperado."),
            ("σ  (Desv. Est.)", "std",    "Dispersión del consumo\nalrededor de la media."),
            ("Mediana",         "median", "Valor central. Resistente\na valores extremos."),
            ("Mínimo",          "min",    "Menor consumo registrado."),
            ("Máximo",          "max",    "Mayor consumo registrado."),
            ("Percentil 25",    "p25",    "El 25 % de días consume\nmenos que este valor."),
            ("Percentil 75",    "p75",    "El 75 % de días consume\nmenos que este valor."),
            ("Asimetría",       "skew",   "> 0: cola derecha.\n< 0: cola izquierda."),
            ("Curtosis",        "kurt",   "> 0: más picuda.\n< 0: más plana que normal."),
            ("N (Registros)",   "n",      "Total de días en\nel histórico de consumo."),
        ]

        for idx, (nombre, key, desc) in enumerate(stats_config):
            r, c = divmod(idx, 2)
            card = ctk.CTkFrame(stats_outer, fg_color='#2D2320', corner_radius=6,
                                border_color='#3D302C', border_width=1)
            card.grid(row=r, column=c, padx=3, pady=3, sticky='nsew')

            ctk.CTkLabel(card, text=nombre.upper(),
                font=ctk.CTkFont(size=9, weight="bold"), text_color='#AFA196'
            ).pack(anchor='w', padx=10, pady=(8, 0))

            lbl = ctk.CTkLabel(card, text="--",
                font=ctk.CTkFont(family="Georgia", size=16, weight="bold"),
                text_color='#F4F0EA')
            lbl.pack(anchor='w', padx=10, pady=(2, 2))

            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=10),
                text_color='#6E5E58', justify='left'
            ).pack(anchor='w', padx=10, pady=(0, 8))

            self.stat_labels[key] = lbl

        # ─ Gráfico de distribución ─
        ctk.CTkLabel(parent, text="DISTRIBUCIÓN EMPÍRICA DEL CONSUMO",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            text_color='#D4AF37'
        ).pack(anchor='w', padx=5, pady=(8, 6))

        chart_frame = ctk.CTkFrame(parent, fg_color='#2D2320', corner_radius=8,
                                   border_color='#3D302C', border_width=1)
        chart_frame.pack(fill=tk.X, padx=5, pady=(0, 14))

        self.fig_dist, self.ax_dist = plt.subplots(figsize=(5, 2.8), dpi=90)
        self._estilizar_ax(self.fig_dist, self.ax_dist)
        self.ax_dist.text(0.5, 0.5, "Sin datos cargados", color='#AFA196',
                          ha='center', va='center', transform=self.ax_dist.transAxes, fontsize=10)
        self.canvas_dist = FigureCanvasTkAgg(self.fig_dist, master=chart_frame)
        self.canvas_dist.get_tk_widget().pack(fill=tk.X, padx=8, pady=8)

        # ─ Explicación Montecarlo ─
        self._build_montecarlo_section(parent)

    def _build_montecarlo_section(self, parent):
        """Construye el panel de explicación de la simulación Montecarlo con fórmulas y simbología."""
        ctk.CTkLabel(parent, text="¿CÓMO FUNCIONA LA SIMULACIÓN MONTECARLO?",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            text_color='#D4AF37'
        ).pack(anchor='w', padx=5, pady=(6, 6))

        exp_frame = ctk.CTkFrame(parent, fg_color='#2D2320', corner_radius=8,
                                 border_color='#3D302C', border_width=1)
        exp_frame.pack(fill=tk.X, padx=5, pady=(0, 10))

        # ── Figura matplotlib: fórmulas con mathtext ──
        self.fig_latex, self.ax_latex = plt.subplots(figsize=(6.2, 7.3), dpi=92)
        self.fig_latex.patch.set_facecolor('#2D2320')
        self.ax_latex.set_facecolor('#2D2320')
        self.ax_latex.axis('off')
        self.ax_latex.set_xlim(0, 1)
        self.ax_latex.set_ylim(0, 1)

        GOLD  = '#D4AF37'
        CREAM = '#C8B89A'
        LITE  = '#F4F0EA'
        DIM   = '#7E7068'
        TEAL  = '#5DADE2'

        # ══ TÍTULO ══
        self.ax_latex.text(0.5, 0.985, "Fundamentos de la Simulación Montecarlo",
            color=GOLD, fontsize=11, weight='bold', ha='center', va='top',
            transform=self.ax_latex.transAxes)

        # ══ PASO 1 ══
        y = 0.925
        self.ax_latex.text(0.02, y, "① Estimación de Parámetros del Histórico",
            color=LITE, fontsize=9.5, weight='bold', va='top', transform=self.ax_latex.transAxes)
        y -= 0.065
        self.ax_latex.text(0.06, y,
            r"$\mu = \dfrac{1}{N}\sum_{i=1}^{N} x_i$",
            color=CREAM, fontsize=11.5, va='top', transform=self.ax_latex.transAxes)
        self.ax_latex.text(0.52, y,
            r"$\sigma = \sqrt{\dfrac{1}{N-1}\sum_{i=1}^{N}(x_i - \mu)^2}$",
            color=CREAM, fontsize=11.5, va='top', transform=self.ax_latex.transAxes)
        y -= 0.082   # espacio ampliado entre fórmula y simbología
        # Simbología paso 1
        simbolos_1 = [
            (r"$\mu$",   "= Media del consumo diario (kg/día)"),
            (r"$\sigma$","= Desv. estándar — mide la variabilidad"),
            (r"$x_i$",   "= Registro de consumo del día i"),
            (r"$N$",     "= Total de días en el histórico"),
        ]
        for sym, desc in simbolos_1:
            self.ax_latex.text(0.06, y, sym, color=TEAL, fontsize=9, va='top',
                transform=self.ax_latex.transAxes)
            self.ax_latex.text(0.14, y, desc, color=DIM, fontsize=8, va='top',
                transform=self.ax_latex.transAxes)
            y -= 0.036

        # Separador
        y -= 0.008
        self.ax_latex.axhline(y + 0.012, color='#3D302C', linewidth=0.7, xmin=0.01, xmax=0.99)

        # ══ PASO 2 ══
        y -= 0.005
        self.ax_latex.text(0.02, y, "② Muestreo Aleatorio (Distribución Normal)",
            color=LITE, fontsize=9.5, weight='bold', va='top', transform=self.ax_latex.transAxes)
        y -= 0.06
        self.ax_latex.text(0.06, y,
            r"$X_j \sim \mathcal{N}(\mu,\;\sigma^2)$",
            color=CREAM, fontsize=12, va='top', transform=self.ax_latex.transAxes)
        y -= 0.048
        simbolos_2 = [
            (r"$X_j$",          "= Consumo simulado en el día j de la iteración"),
            (r"$\mathcal{N}$",  "= Distribución Normal (campana de Gauss)"),
            (r"$\sigma^2$",     "= Varianza (desv. estándar al cuadrado)"),
        ]
        for sym, desc in simbolos_2:
            self.ax_latex.text(0.06, y, sym, color=TEAL, fontsize=9, va='top',
                transform=self.ax_latex.transAxes)
            self.ax_latex.text(0.17, y, desc, color=DIM, fontsize=8, va='top',
                transform=self.ax_latex.transAxes)
            y -= 0.036

        y -= 0.008
        self.ax_latex.axhline(y + 0.012, color='#3D302C', linewidth=0.7, xmin=0.01, xmax=0.99)

        # ══ PASO 3 ══
        y -= 0.005
        self.ax_latex.text(0.02, y, "③ Simulación del Agotamiento de Inventario",
            color=LITE, fontsize=9.5, weight='bold', va='top', transform=self.ax_latex.transAxes)
        y -= 0.06
        self.ax_latex.text(0.06, y,
            r"$I_0 - X_1 - X_2 - \cdots - X_n \;\leq\; 0$",
            color=CREAM, fontsize=12, va='top', transform=self.ax_latex.transAxes)
        y -= 0.048
        simbolos_3 = [
            (r"$I_0$", "= Inventario inicial disponible (kg)"),
            (r"$n$",   "= Día en que el inventario llega a cero"),
        ]
        for sym, desc in simbolos_3:
            self.ax_latex.text(0.06, y, sym, color=TEAL, fontsize=9, va='top',
                transform=self.ax_latex.transAxes)
            self.ax_latex.text(0.14, y, desc, color=DIM, fontsize=8, va='top',
                transform=self.ax_latex.transAxes)
            y -= 0.036

        y -= 0.008
        self.ax_latex.axhline(y + 0.012, color='#3D302C', linewidth=0.7, xmin=0.01, xmax=0.99)

        # ══ PASO 4 ══
        y -= 0.005
        self.ax_latex.text(0.02, y, "④ Cálculo de Probabilidad (K iteraciones)",
            color=LITE, fontsize=9.5, weight='bold', va='top', transform=self.ax_latex.transAxes)
        y -= 0.065
        self.ax_latex.text(0.06, y,
            r"$P(\mathrm{stock} \geq n\;\mathrm{d\acute{i}as}) = \dfrac{\mathrm{Conteo}(n_k \geq n)}{K}$",
            color=CREAM, fontsize=11.5, va='top', transform=self.ax_latex.transAxes)
        y -= 0.055
        simbolos_4 = [
            (r"$K$",  "= Número total de iteraciones (ej: 10 000)"),
            (r"$n_k$","= Días hasta agotar el stock en la iteración k"),
            (r"$P$",  "= Probabilidad estimada de durar ≥ n días"),
        ]
        for sym, desc in simbolos_4:
            self.ax_latex.text(0.06, y, sym, color=TEAL, fontsize=9, va='top',
                transform=self.ax_latex.transAxes)
            self.ax_latex.text(0.14, y, desc, color=DIM, fontsize=8, va='top',
                transform=self.ax_latex.transAxes)
            y -= 0.036

        y -= 0.008
        self.ax_latex.axhline(y + 0.012, color='#3D302C', linewidth=0.7, xmin=0.01, xmax=0.99)

        # ══ NOTA AL PIE ══
        y -= 0.005
        self.ax_latex.text(0.5, y,
            "El proceso se repite K veces. El resultado es la distribución de probabilidad\n"
            "del tiempo de agotamiento dada la variabilidad histórica del consumo.",
            color=DIM, fontsize=8, ha='center', va='top',
            transform=self.ax_latex.transAxes, linespacing=1.5)

        self.fig_latex.tight_layout(pad=0.4)
        self.canvas_latex = FigureCanvasTkAgg(self.fig_latex, master=exp_frame)
        self.canvas_latex.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.canvas_latex.draw()

    # ──────────────────────────────────────────────────────────
    # LÓGICA
    # ──────────────────────────────────────────────────────────

    def _estilizar_ax(self, fig, ax):
        fig.patch.set_facecolor('#2D2320')
        ax.set_facecolor('#2D2320')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#4A3C37')
        ax.spines['bottom'].set_color('#4A3C37')
        ax.tick_params(colors='#AFA196', labelsize=8)
        ax.grid(True, color='#3D302C', linestyle=':', alpha=0.6)

    def cargar_csv(self, ruta):
        self.current_csv_path = ruta
        if ruta and os.path.exists(ruta):
            try:
                df = pd.read_csv(ruta)
                if 'Fecha' in df.columns and 'Consumo_Kg' in df.columns:
                    self._poblar_tabla(df)
                    self._actualizar_estadisticas(df['Consumo_Kg'].values)
                    media = df['Consumo_Kg'].mean()
                    std = df['Consumo_Kg'].std(ddof=1)
                    self.entry_media_base.delete(0, 'end')
                    self.entry_media_base.insert(0, f"{media:.2f}")
                    self.entry_desv_base.delete(0, 'end')
                    self.entry_desv_base.insert(0, f"{std:.2f}")
            except Exception:
                pass

    def _poblar_tabla(self, df):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, (_, row) in enumerate(df.iterrows()):
            self.tree.insert('', tk.END, values=(idx + 1, row['Fecha'], f"{float(row['Consumo_Kg']):.2f}"))

    def _actualizar_estadisticas(self, datos: np.ndarray):
        if len(datos) < 2:
            return
        media   = np.mean(datos)
        std     = np.std(datos, ddof=1)
        mediana = np.median(datos)
        minimo  = np.min(datos)
        maximo  = np.max(datos)
        p25     = np.percentile(datos, 25)
        p75     = np.percentile(datos, 75)
        skewness = np.mean(((datos - media) / std) ** 3) if std > 0 else 0.0
        kurtosis = np.mean(((datos - media) / std) ** 4) - 3 if std > 0 else 0.0
        n = len(datos)

        self.stat_labels['mean'].configure(text=f"{media:.2f} kg")
        self.stat_labels['std'].configure(text=f"{std:.2f} kg")
        self.stat_labels['median'].configure(text=f"{mediana:.2f} kg")
        self.stat_labels['min'].configure(text=f"{minimo:.2f} kg")
        self.stat_labels['max'].configure(text=f"{maximo:.2f} kg")
        self.stat_labels['p25'].configure(text=f"{p25:.2f} kg")
        self.stat_labels['p75'].configure(text=f"{p75:.2f} kg")
        self.stat_labels['skew'].configure(text=f"{skewness:.4f}")
        self.stat_labels['kurt'].configure(text=f"{kurtosis:.4f}")
        self.stat_labels['n'].configure(text=str(n))

        self._actualizar_grafico(datos, media, std)

    def _actualizar_grafico(self, datos, media, std):
        self.ax_dist.clear()
        self._estilizar_ax(self.fig_dist, self.ax_dist)
        self.ax_dist.hist(datos, bins=20, density=True, alpha=0.5,
                          color='#C5A059', edgecolor='#2D2320', label='Empírico')
        xmin, xmax = self.ax_dist.get_xlim()
        x = np.linspace(xmin, xmax, 200)
        if std > 0:
            p = (1.0 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - media) / std) ** 2)
            self.ax_dist.plot(x, p, color='#D4AF37', linewidth=2, label='N(μ, σ²)')
        self.ax_dist.axvline(media, color='#F4F0EA', linestyle='--',
                             linewidth=1.2, label=f'μ = {media:.1f}')
        self.ax_dist.set_xlabel("Consumo diario (kg)", color='#AFA196', fontsize=8)
        self.ax_dist.legend(facecolor='#2D2320', edgecolor='#4A3C37',
                            labelcolor='#F4F0EA', fontsize=7)
        self.fig_dist.tight_layout()
        self.canvas_dist.draw()

    def _generar_datos_vista_previa(self):
        try:
            cantidad   = int(self.entry_cantidad.get())
            media_base = float(self.entry_media_base.get())
            desv_base  = float(self.entry_desv_base.get())
            if cantidad < 1 or desv_base <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error de entrada",
                "Verifica: Registros (entero > 0), µ (número) y σ (número > 0).",
                parent=self.winfo_toplevel())
            return

        # Generar DataFrame en memoria
        df = generar_consumo_historico(dias=cantidad, media=media_base,
                                       desviacion=desv_base, ruta_csv=None)
        
        # Poblar la tabla de vista previa
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        for idx, (_, row) in enumerate(df.iterrows()):
            self.preview_tree.insert('', tk.END, values=(idx + 1, row['Fecha'], f"{float(row['Consumo_Kg']):.2f}"))
        
        self.lbl_preview_count.configure(text=f"Registros en vista previa: {len(df)}")

    def _on_double_click(self, event):
        treeview = event.widget
        region = treeview.identify_region(event.x, event.y)
        if region != 'cell':
            return
        col    = treeview.identify_column(event.x)
        row_id = treeview.identify_row(event.y)
        if not row_id or col != '#3':
            return

        bbox = treeview.bbox(row_id, col)
        if not bbox:
            return
        x, y, w, h = bbox
        val = treeview.set(row_id, 'Consumo_Kg')

        entry_edit = tk.Entry(treeview, font=('Arial', 11),
            bg='#4A3B37', fg='#F4F0EA', insertbackground='#F4F0EA',
            relief='flat', bd=0)
        entry_edit.insert(0, val)
        entry_edit.place(x=x, y=y, width=w, height=h)
        entry_edit.focus_set()
        entry_edit.select_range(0, tk.END)

        def confirmar(e=None):
            nuevo = entry_edit.get().strip()
            try:
                v = float(nuevo)
                if v < 0:
                    raise ValueError()
                treeview.set(row_id, 'Consumo_Kg', f"{v:.2f}")
                if treeview == self.tree:
                    self._persistir_csv_silencioso()
                    self._recalcular_todo_desde_tabla()
            except ValueError:
                messagebox.showwarning("Valor inválido",
                    "El consumo debe ser un número ≥ 0.",
                    parent=self.winfo_toplevel())
            entry_edit.destroy()

        entry_edit.bind('<Return>', confirmar)
        entry_edit.bind('<Escape>', lambda e: entry_edit.destroy())
        entry_edit.bind('<FocusOut>', confirmar)

    def _guardar_y_cargar(self):
        filas = self.tree.get_children()
        if not filas:
            messagebox.showwarning("Sin datos",
                "No hay registros en el histórico para guardar.",
                parent=self.winfo_toplevel())
            return

        registros = []
        for item in filas:
            vals = self.tree.item(item, 'values')
            try:
                registros.append({'Fecha': vals[1], 'Consumo_Kg': float(vals[2])})
            except (ValueError, IndexError):
                continue

        df_final = pd.DataFrame(registros)
        df_final.to_csv(self.current_csv_path, index=False)
 
        if self.on_save_callback:
            self.on_save_callback(self.current_csv_path)

        messagebox.showinfo("Guardado",
            f"Datos guardados correctamente ({len(registros)} registros).",
            parent=self.winfo_toplevel())

    def _recalcular_todo_desde_tabla(self):
        filas = self.tree.get_children()
        if not filas:
            for key in self.stat_labels:
                self.stat_labels[key].configure(text="--")
            self.ax_dist.clear()
            self._estilizar_ax(self.fig_dist, self.ax_dist)
            self.ax_dist.text(0.5, 0.5, "Sin datos cargados", color='#AFA196',
                              ha='center', va='center', transform=self.ax_dist.transAxes, fontsize=10)
            self.canvas_dist.draw()
            return

        datos = []
        for item in filas:
            vals = self.tree.item(item, 'values')
            try:
                datos.append(float(vals[2]))
            except (ValueError, IndexError):
                continue

        if datos:
            self._actualizar_estadisticas(np.array(datos))

    def _get_next_date(self, treeview):
        filas = treeview.get_children()
        if filas:
            ultimo_item = filas[-1]
            fecha_str = treeview.item(ultimo_item, 'values')[1]
            try:
                nueva_fecha = (pd.to_datetime(fecha_str) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                return nueva_fecha
            except Exception:
                pass
        return pd.Timestamp.now().strftime('%Y-%m-%d')

    def _añadir_fila_historico(self):
        nueva_fecha = self._get_next_date(self.tree)
        try:
            cons_defecto = float(self.entry_media_base.get())
        except ValueError:
            cons_defecto = 62.5

        idx = len(self.tree.get_children()) + 1
        nuevo_id = self.tree.insert('', tk.END, values=(idx, nueva_fecha, f"{cons_defecto:.2f}"))
        self.tree.selection_set(nuevo_id)
        self.tree.see(nuevo_id)
        self._persistir_csv_silencioso(es_adicion=True)
        self._recalcular_todo_desde_tabla()

    def _abrir_popup_añadir_datos(self):
        # Calcular media y desv. estándar sugeridos con base en datos actuales
        filas = self.tree.get_children()
        media_sug = 62.5
        desv_sug = 12.5

        if filas:
            datos = []
            for item in filas:
                vals = self.tree.item(item, 'values')
                try:
                    datos.append(float(vals[2]))
                except (ValueError, IndexError):
                    continue
            if len(datos) >= 2:
                media_sug = float(np.mean(datos))
                desv_sug = float(np.std(datos, ddof=1))
            elif len(datos) == 1:
                media_sug = float(datos[0])

        # Obtener última fecha para continuar de forma correlativa
        ultima_fecha = pd.Timestamp.now().strftime('%Y-%m-%d')
        if filas:
            ultima_fecha = self.tree.item(filas[-1], 'values')[1]

        def confirmar_y_anexar(datos_nuevos):
            # Anexar cada fila a la tabla histórica principal
            for fecha, valor in datos_nuevos:
                main_idx = len(self.tree.get_children()) + 1
                self.tree.insert('', tk.END, values=(main_idx, fecha, f"{valor:.2f}"))
            self._persistir_csv_silencioso(es_adicion=True)
            self._recalcular_todo_desde_tabla()

        # Abrir popup modal
        popup = VentanaAñadirDatos(self.winfo_toplevel(), ultima_fecha, media_sug, desv_sug, confirmar_y_anexar)

    def _eliminar_fila_historico(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección",
                "Selecciona una o más filas de la tabla histórica para eliminar.",
                parent=self.winfo_toplevel())
            return

        for item in seleccion:
            self.tree.delete(item)

        # Reindexar las filas restantes
        for idx, item in enumerate(self.tree.get_children()):
            vals = self.tree.item(item, 'values')
            self.tree.item(item, values=(idx + 1, vals[1], vals[2]))

        self._persistir_csv_silencioso()
        self._recalcular_todo_desde_tabla()

    def _añadir_fila_preview(self):
        nueva_fecha = self._get_next_date(self.preview_tree)
        try:
            cons_defecto = float(self.entry_media_base.get())
        except ValueError:
            cons_defecto = 62.5

        idx = len(self.preview_tree.get_children()) + 1
        nuevo_id = self.preview_tree.insert('', tk.END, values=(idx, nueva_fecha, f"{cons_defecto:.2f}"))
        self.preview_tree.selection_set(nuevo_id)
        self.preview_tree.see(nuevo_id)
        
        cant = len(self.preview_tree.get_children())
        self.lbl_preview_count.configure(text=f"Registros en vista previa: {cant}")

    def _eliminar_fila_preview(self):
        seleccion = self.preview_tree.selection()
        if not seleccion:
            messagebox.showwarning("Sin selección",
                "Selecciona una o más filas de la vista previa para eliminar.",
                parent=self.winfo_toplevel())
            return

        for item in seleccion:
            self.preview_tree.delete(item)
        
        # Reindexar las filas restantes de vista previa
        for idx, item in enumerate(self.preview_tree.get_children()):
            vals = self.preview_tree.item(item, 'values')
            self.preview_tree.item(item, values=(idx + 1, vals[1], vals[2]))

        cant = len(self.preview_tree.get_children())
        self.lbl_preview_count.configure(text=f"Registros en vista previa: {cant}")

    def _anexar_al_historico(self):
        preview_items = self.preview_tree.get_children()
        if not preview_items:
            messagebox.showwarning("Sin datos",
                "No hay registros en la vista previa para anexar.",
                parent=self.winfo_toplevel())
            return

        # Obtener la fecha siguiente a la última del histórico real
        ultima_fecha = self._get_next_date(self.tree)
        
        # Anexar las filas correlativamente
        for idx, item in enumerate(preview_items):
            vals = self.preview_tree.item(item, 'values')
            try:
                fecha_ajustada = (pd.to_datetime(ultima_fecha) + pd.Timedelta(days=idx)).strftime('%Y-%m-%d')
            except Exception:
                fecha_ajustada = pd.Timestamp.now().strftime('%Y-%m-%d')
            
            main_idx = len(self.tree.get_children()) + 1
            self.tree.insert('', tk.END, values=(main_idx, fecha_ajustada, vals[2]))

        # Limpiar la vista previa
        for item in list(preview_items):
            self.preview_tree.delete(item)
        self.lbl_preview_count.configure(text="Registros en vista previa: 0")

        # Guardar, recalcular e informar
        self._persistir_csv_silencioso(es_adicion=True)
        self._recalcular_todo_desde_tabla()
        
        # Cambiar a pestaña del histórico
        self.left_tabview.set("Consumo Histórico")
        
        messagebox.showinfo("Datos Anexados",
            "Los registros de la vista previa fueron anexados correlativamente al histórico.",
            parent=self.winfo_toplevel())

    def _reemplazar_historico(self):
        preview_items = self.preview_tree.get_children()
        if not preview_items:
            messagebox.showwarning("Sin datos",
                "No hay registros en la vista previa para reemplazar el histórico.",
                parent=self.winfo_toplevel())
            return

        confirmacion = messagebox.askyesno("Confirmar reemplazo",
            "¿Estás seguro de que deseas reemplazar TODO el histórico con los datos de vista previa?\n"
            "Esta acción no se puede deshacer.",
            parent=self.winfo_toplevel())
        
        if not confirmacion:
            return

        # Limpiar histórico
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Reemplazar con los registros de la vista previa
        for idx, item in enumerate(preview_items):
            vals = self.preview_tree.item(item, 'values')
            self.tree.insert('', tk.END, values=(idx + 1, vals[1], vals[2]))

        # Limpiar la vista previa
        for item in list(preview_items):
            self.preview_tree.delete(item)
        self.lbl_preview_count.configure(text="Registros en vista previa: 0")

        # Guardar, recalcular e informar
        self._persistir_csv_silencioso(es_adicion=True)
        self._recalcular_todo_desde_tabla()
        
        # Cambiar a pestaña del histórico
        self.left_tabview.set("Consumo Histórico")
        
        messagebox.showinfo("Histórico Reemplazado",
            "El histórico de consumo fue completamente reemplazado con los registros de vista previa.",
            parent=self.winfo_toplevel())

    def _obtener_nueva_ruta_alterna(self):
        counter = 1
        while True:
            nombre = f"consumo_historico_alterno_{counter}.csv"
            if not os.path.exists(nombre):
                return nombre
            counter += 1

    def _persistir_csv_silencioso(self, es_adicion=False):
        """Guarda el estado actual del Treeview histórico en un archivo CSV."""
        filas = self.tree.get_children()
        if not filas:
            return
        registros = []
        for item in filas:
            vals = self.tree.item(item, 'values')
            try:
                registros.append({'Fecha': vals[1], 'Consumo_Kg': float(vals[2])})
            except (ValueError, IndexError):
                continue
        if registros:
            df_final = pd.DataFrame(registros)
            if es_adicion and (self.current_csv_path == "consumo_historico.csv" or self.current_csv_path is None):
                self.current_csv_path = self._obtener_nueva_ruta_alterna()
                messagebox.showinfo("Archivo Alterno Generado",
                    f"Se ha generado un nuevo archivo alterno para conservar el histórico base intacto:\n{self.current_csv_path}",
                    parent=self.winfo_toplevel())
            elif self.current_csv_path is None:
                self.current_csv_path = self._obtener_nueva_ruta_alterna()
            df_final.to_csv(self.current_csv_path, index=False)
            if self.on_save_callback:
                self.on_save_callback(self.current_csv_path)


class VentanaAñadirDatos(ctk.CTkToplevel):
    """Ventana emergente modal para generar y previsualizar múltiples registros históricos de consumo."""

    def __init__(self, master, ultima_fecha, media_defecto, desv_defecto, on_confirm_callback):
        super().__init__(master)
        self.title("Añadir Varios Registros Históricos")
        self.geometry("540x570")
        self.configure(fg_color='#1A1412')
        self.resizable(False, False)

        # Modal setup
        self.transient(master)
        self.grab_set()

        self.ultima_fecha = ultima_fecha
        self.media_defecto = media_defecto
        self.desv_defecto = desv_defecto
        self.on_confirm_callback = on_confirm_callback

        self._build_ui()
        self._generar_datos()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)  # Tabla de vista previa expandible

        # Encabezado
        header_frame = ctk.CTkFrame(self, fg_color='transparent')
        header_frame.grid(row=0, column=0, sticky='ew', padx=15, pady=(15, 5))
        ctk.CTkLabel(header_frame, text="GENERACIÓN RÁPIDA DE CONSUMO",
                     font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
                     text_color='#D4AF37').pack(anchor='w')
        ctk.CTkLabel(header_frame, text="Especifique los parámetros para generar múltiples días de consumo consecutivos.",
                     font=ctk.CTkFont(size=10), text_color='#6E5E58').pack(anchor='w')

        # Formulario de parámetros
        form_frame = ctk.CTkFrame(self, fg_color='#2D2320', corner_radius=8,
                                  border_color='#3D302C', border_width=1)
        form_frame.grid(row=1, column=0, sticky='ew', padx=15, pady=5)

        # Controles de entrada
        ctk.CTkLabel(form_frame, text="Días:", font=ctk.CTkFont(size=11), text_color='#AFA196').grid(row=0, column=0, padx=(10, 2), pady=10, sticky='w')
        self.entry_dias = ctk.CTkEntry(form_frame, width=50, fg_color='#1A1412', text_color='#F4F0EA', border_color='#4A3B37', font=ctk.CTkFont(size=11))
        self.entry_dias.insert(0, "30")
        self.entry_dias.grid(row=0, column=1, padx=2, pady=10)

        ctk.CTkLabel(form_frame, text="Media (µ):", font=ctk.CTkFont(size=11), text_color='#AFA196').grid(row=0, column=2, padx=(10, 2), pady=10, sticky='w')
        self.entry_media = ctk.CTkEntry(form_frame, width=60, fg_color='#1A1412', text_color='#F4F0EA', border_color='#4A3B37', font=ctk.CTkFont(size=11))
        self.entry_media.insert(0, f"{self.media_defecto:.2f}")
        self.entry_media.grid(row=0, column=3, padx=2, pady=10)

        ctk.CTkLabel(form_frame, text="Desv. (σ):", font=ctk.CTkFont(size=11), text_color='#AFA196').grid(row=0, column=4, padx=(10, 2), pady=10, sticky='w')
        self.entry_desv = ctk.CTkEntry(form_frame, width=60, fg_color='#1A1412', text_color='#F4F0EA', border_color='#4A3B37', font=ctk.CTkFont(size=11))
        self.entry_desv.insert(0, f"{self.desv_defecto:.2f}")
        self.entry_desv.grid(row=0, column=5, padx=2, pady=10)

        # Botón Previsualizar
        btn_sim = ctk.CTkButton(form_frame, text="Previsualizar", command=self._generar_datos,
                                fg_color='#D4AF37', hover_color='#B2902C', text_color='#1A1412',
                                font=ctk.CTkFont(size=11, weight="bold"), width=85, height=26)
        btn_sim.grid(row=0, column=6, padx=(10, 10), pady=10)

        # Tabla de vista previa
        tree_outer = tk.Frame(self, bg='#2D2320')
        tree_outer.grid(row=2, column=0, sticky='nsew', padx=15, pady=5)

        self.tree = ttk.Treeview(tree_outer, columns=('Index', 'Fecha', 'Consumo_Kg'),
                                 show='headings', style='VD.Treeview')
        self.tree.heading('Index', text='Nº')
        self.tree.heading('Fecha', text='Fecha (Consecutiva)')
        self.tree.heading('Consumo_Kg', text='Consumo Simulado (kg)')
        self.tree.column('Index', width=50, anchor='center')
        self.tree.column('Fecha', width=200, anchor='center')
        self.tree.column('Consumo_Kg', width=200, anchor='center')

        vsb = ttk.Scrollbar(tree_outer, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Botones inferiores de confirmación / cancelación
        ctrl_frame = ctk.CTkFrame(self, fg_color='transparent')
        ctrl_frame.grid(row=3, column=0, sticky='ew', padx=15, pady=(5, 15))

        ctk.CTkButton(ctrl_frame, text="Cancelar",
                      fg_color='#4A1E1E', hover_color='#611A1A', text_color='#E74C3C',
                      font=ctk.CTkFont(size=12, weight="bold"), border_color='#611A1A',
                      border_width=1, height=36, command=self.destroy
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        ctk.CTkButton(ctrl_frame, text="Aceptar y Anexar",
                      fg_color='#2D4A2D', hover_color='#3A613A', text_color='#7CFC00',
                      font=ctk.CTkFont(size=12, weight="bold"), border_color='#3A613A',
                      border_width=1, height=36, command=self._confirmar
        ).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))

    def _generar_datos(self):
        try:
            dias = int(self.entry_dias.get())
            media = float(self.entry_media.get())
            desv = float(self.entry_desv.get())
            if dias < 1 or desv <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error de entrada",
                                 "Verifica: Días (entero > 0), Media (número) y Desviación (número > 0).",
                                 parent=self)
            return

        # Generar fechas consecutivas empezando desde ultima_fecha + 1 día
        try:
            inicio = pd.to_datetime(self.ultima_fecha) + pd.Timedelta(days=1)
        except Exception:
            inicio = pd.Timestamp.now()

        fechas = pd.date_range(start=inicio, periods=dias, freq='D')
        fechas_str = fechas.strftime('%Y-%m-%d')

        # Generar consumos aleatorios (usamos generador dinámico)
        rng = np.random.default_rng()
        consumos = rng.normal(loc=media, scale=desv, size=dias)
        consumos = np.clip(consumos, 0, None)
        consumos = np.round(consumos, 2)

        self.datos_generados = list(zip(fechas_str, consumos))

        # Limpiar y rellenar tabla de vista previa
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, (fecha, cons) in enumerate(self.datos_generados):
            self.tree.insert('', tk.END, values=(idx + 1, fecha, f"{cons:.2f}"))

    def _confirmar(self):
        if not hasattr(self, 'datos_generados') or not self.datos_generados:
            messagebox.showwarning("Sin datos", "Por favor, genere o previsualice los datos primero.", parent=self)
            return

        self.on_confirm_callback(self.datos_generados)
        self.destroy()

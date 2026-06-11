"""
ventana_simulacion.py
Ventana independiente (CTkToplevel) para los resultados de la
simulación de Montecarlo.
Layout:
  Fila superior  →  60% gráfico  |  40% KPIs + tabla de resumen
  Fila inferior  →  Textbox de interpretación narrativa
"""
import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class VentanaSimulacionFrame(ctk.CTkFrame):
    """Frame de resultados de la simulación Montecarlo."""

    def __init__(self, master, resultados, masa, iteraciones, **kwargs):
        kwargs.setdefault('fg_color', '#1A1412')
        super().__init__(master, **kwargs)

        self.resultados  = resultados
        self.masa        = masa
        self.iteraciones = iteraciones

        self._build_ui()
        self._cargar_resultados()

    # ──────────────────────────────────────────────────────────
    # INTERFAZ
    # ──────────────────────────────────────────────────────────

    def _build_ui(self):
        # Rejilla principal
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=3)   # zona superior
        self.rowconfigure(1, weight=2)   # zona inferior (texto)

        # ── Zona superior ─────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color='transparent')
        top.grid(row=0, column=0, sticky='nsew', padx=14, pady=(14, 6))
        top.columnconfigure(0, weight=6)   # gráfico 60 %
        top.columnconfigure(1, weight=4)   # tabla   40 %
        top.rowconfigure(0, weight=1)

        # Panel gráfico (izquierda, 60 %)
        self.frame_chart = ctk.CTkFrame(top, fg_color='#231B19',
            corner_radius=10, border_color='#3D302C', border_width=1)
        self.frame_chart.grid(row=0, column=0, sticky='nsew', padx=(0, 6))
        self.frame_chart.columnconfigure(0, weight=1)
        self.frame_chart.rowconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_chart, text="DISTRIBUCIÓN DE PROBABILIDAD",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            text_color='#D4AF37'
        ).grid(row=0, column=0, sticky='w', padx=14, pady=(12, 6))

        chart_inner = ctk.CTkFrame(self.frame_chart, fg_color='#2D2320',
            corner_radius=8, border_color='#3D302C', border_width=1)
        chart_inner.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))

        self.fig, self.ax = plt.subplots(figsize=(5.5, 4.0), dpi=100)
        self._estilo_ax(self.fig, self.ax)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_inner)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Panel tabla (derecha, 40 %)
        self.frame_table = ctk.CTkFrame(top, fg_color='#231B19',
            corner_radius=10, border_color='#3D302C', border_width=1)
        self.frame_table.grid(row=0, column=1, sticky='nsew', padx=(6, 0))
        self._build_right_panel(self.frame_table)

        # ── Zona inferior: interpretación ─────────────────────
        bot = ctk.CTkFrame(self, fg_color='#231B19',
            corner_radius=10, border_color='#3D302C', border_width=1)
        bot.grid(row=1, column=0, sticky='nsew', padx=14, pady=(6, 14))
        bot.columnconfigure(0, weight=1)
        bot.columnconfigure(1, weight=1)
        bot.rowconfigure(1, weight=1)

        ctk.CTkLabel(bot, text="Análisis Simulación",
            font=ctk.CTkFont(family="Georgia", size=16, weight="bold"),
            text_color='#D4AF37'
        ).grid(row=0, column=0, columnspan=2, sticky='w', padx=14, pady=(12, 6))

        # Columna Izquierda: Informe de Duración
        self.text_interp = ctk.CTkTextbox(bot,
            fg_color='#2D2320', text_color='#C8B89A',
            border_color='#3D302C', border_width=1,
            font=ctk.CTkFont(family="Courier New", size=13, weight="bold"),
            corner_radius=6)
        self.text_interp.grid(row=1, column=0, sticky='nsew', padx=(10, 5), pady=(0, 10))

        # Columna Derecha: Recomendaciones Operativas
        self.text_recom = ctk.CTkTextbox(bot,
            fg_color='#2D2320', text_color='#C8B89A',
            border_color='#3D302C', border_width=1,
            font=ctk.CTkFont(family="Courier New", size=13, weight="bold"),
            corner_radius=6)
        self.text_recom.grid(row=1, column=1, sticky='nsew', padx=(5, 10), pady=(0, 10))

    def _build_right_panel(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        ctk.CTkLabel(parent, text="RESUMEN DE RESULTADOS",
            font=ctk.CTkFont(family="Georgia", size=13, weight="bold"),
            text_color='#D4AF37'
        ).grid(row=0, column=0, sticky='w', padx=14, pady=(12, 8))

        # ── KPI cards compactas ──
        kpi_frame = ctk.CTkFrame(parent, fg_color='transparent')
        kpi_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 8))
        kpi_frame.columnconfigure((0, 1), weight=1)

        self._kpi_mini(kpi_frame, 0, 0, "DURACIÓN PROM.", "-- días", "val_prom")
        self._kpi_mini(kpi_frame, 0, 1, "MEDIANA",        "-- días", "val_med")
        self._kpi_mini(kpi_frame, 1, 0, "P5 (pesimista)", "-- días", "val_p5")
        self._kpi_mini(kpi_frame, 1, 1, "P95 (optimista)","-- días", "val_p95")
        self._kpi_mini(kpi_frame, 2, 0, "NIVEL DE RIESGO","--",      "val_nivel")
        self._kpi_mini(kpi_frame, 2, 1, "RIESGO ≤2 días", "--%",     "val_riesgo")

        # ── Treeview tabla de resumen ──
        ctk.CTkLabel(parent, text="TABLA DE DATOS CLAVE",
            font=ctk.CTkFont(family="Arial", size=10, weight="bold"),
            text_color='#AFA196'
        ).grid(row=2, column=0, sticky='w', padx=14, pady=(4, 4))

        tree_outer = tk.Frame(parent, bg='#2D2320')
        tree_outer.grid(row=3, column=0, sticky='nsew', padx=10, pady=(0, 10))
        parent.rowconfigure(3, weight=1)

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('VS.Treeview',
            background='#2D2320', foreground='#F4F0EA',
            rowheight=24, fieldbackground='#2D2320', font=('Arial', 10))
        style.configure('VS.Treeview.Heading',
            background='#3D302C', foreground='#D4AF37', font=('Arial', 10, 'bold'))
        style.map('VS.Treeview', background=[('selected', '#3D302C')])

        self.tree = ttk.Treeview(tree_outer, columns=('Métrica', 'Valor'),
                                 show='headings', style='VS.Treeview')
        self.tree.heading('Métrica', text='Métrica')
        self.tree.heading('Valor',   text='Valor')
        self.tree.column('Métrica', width=155, anchor='w')
        self.tree.column('Valor',   width=90,  anchor='center')

        vsb = ttk.Scrollbar(tree_outer, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def _kpi_mini(self, parent, row, col, title, init_val, attr):
        card = ctk.CTkFrame(parent, fg_color='#2D2320',
            corner_radius=6, border_color='#3D302C', border_width=1)
        card.grid(row=row, column=col, padx=2, pady=2, sticky='nsew')
        ctk.CTkLabel(card, text=title,
            font=ctk.CTkFont(size=8, weight="bold"), text_color='#AFA196'
        ).pack(anchor='w', padx=8, pady=(6, 0))
        lbl = ctk.CTkLabel(card, text=init_val,
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            text_color='#F4F0EA')
        lbl.pack(anchor='w', padx=8, pady=(1, 6))
        setattr(self, attr, lbl)

    # ──────────────────────────────────────────────────────────
    # CARGA DE RESULTADOS
    # ──────────────────────────────────────────────────────────

    def _cargar_resultados(self):
        res       = self.resultados
        masa      = self.masa
        iters     = self.iteraciones

        prom     = res['dias_promedio']
        mediana  = res['dias_mediana']
        p5       = res['p5']
        p95      = res['p95']
        dias_min = res['dias_min']
        dias_max = res['dias_max']

        consumo_aprox = masa / prom if prom > 0 else 0

        prob_bajo_2 = (res['distribucion_probabilidad'].get(1, 0.0) +
                       res['distribucion_probabilidad'].get(2, 0.0))
        prob_riesgo = prob_bajo_2 * 100

        if prob_riesgo > 50:
            nivel, nivel_color = "CRÍTICO", "#E74C3C"
        elif prob_riesgo > 20:
            nivel, nivel_color = "ALTO", "#E67E22"
        elif prob_riesgo > 5:
            nivel, nivel_color = "MEDIO", "#F1C40F"
        else:
            nivel, nivel_color = "BAJO", "#2ECC71"

        # KPI minis
        self.val_prom.configure(text=f"{prom} días")
        self.val_med.configure(text=f"{mediana} días")
        self.val_p5.configure(text=f"{p5} días")
        self.val_p95.configure(text=f"{p95} días")
        self.val_nivel.configure(text=nivel, text_color=nivel_color)
        self.val_riesgo.configure(text=f"{prob_riesgo:.1f}%")

        # Tabla de resumen
        filas = [
            ("Masa evaluada",          f"{masa:.1f} kg"),
            ("Duración esperada",       f"{prom} días"),
            ("Mediana de duración",     f"{mediana} días"),
            ("Intervalo certeza 90%",   f"{p5}–{p95} días"),
            ("Mínimo simulado",         f"{dias_min} días"),
            ("Máximo simulado",         f"{dias_max} días"),
            ("Consumo estimado/día",    f"~{consumo_aprox:.1f} kg"),
            ("Riesgo stockout ≤2 días", f"{prob_riesgo:.2f}%"),
            ("Nivel de riesgo",         nivel),
            ("Iteraciones",             f"{iters:,}"),
        ]
        for fila in filas:
            tag = 'riesgo' if fila[0] == "Nivel de riesgo" else ''
            self.tree.insert('', tk.END, values=fila)

        # Gráfico
        self._dibujar_grafica(res)

        # Interpretación
        self._generar_interpretacion(res, masa, iters, prob_riesgo, nivel,
                                     consumo_aprox, dias_min, dias_max)

    # ──────────────────────────────────────────────────────────
    # GRÁFICA
    # ──────────────────────────────────────────────────────────

    def _estilo_ax(self, fig, ax):
        fig.patch.set_facecolor('#2D2320')
        ax.set_facecolor('#2D2320')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#4A3C37')
        ax.spines['bottom'].set_color('#4A3C37')
        ax.tick_params(colors='#AFA196', labelsize=8)
        ax.grid(True, color='#3D302C', linestyle=':', alpha=0.6)

    def _dibujar_grafica(self, res):
        self.ax.clear()
        self._estilo_ax(self.fig, self.ax)

        valores = sorted(res["distribucion_probabilidad"].keys())
        probs   = [res["distribucion_probabilidad"][v] * 100 for v in valores]

        self.ax.bar(valores, probs, color='#D4AF37', alpha=0.65,
                    edgecolor='#2D2320', width=0.6, label='Probabilidad')

        prom = res["dias_promedio"]
        p5   = res["p5"]
        p95  = res["p95"]

        self.ax.axvline(prom, color='#F4F0EA', linestyle='-',  linewidth=2,
                        label=f'Promedio ({prom} d)')
        self.ax.axvline(p5,  color='#E67E22', linestyle='--', linewidth=1.5,
                        label=f'P5 ({p5} d)')
        self.ax.axvline(p95, color='#2ECC71', linestyle='--', linewidth=1.5,
                        label=f'P95 ({p95} d)')
        self.ax.axvspan(p5, p95, color='#D4AF37', alpha=0.10,
                        label='Intervalo Certeza 90%')

        self.ax.set_xlabel("Días hasta agotar el inventario", color='#AFA196')
        self.ax.set_ylabel("Probabilidad (%)", color='#AFA196')
        self.ax.set_title("Distribución de Probabilidad del Agotamiento",
                          color='#F4F0EA', fontsize=11, pad=8, weight='bold')
        self.ax.set_xticks(valores)
        self.ax.legend(facecolor='#2D2320', edgecolor='#4A3C37',
                       labelcolor='#F4F0EA', fontsize=8)
        self.fig.tight_layout()
        self.canvas.draw()

    # ──────────────────────────────────────────────────────────
    # TEXTO NARRATIVO
    # ──────────────────────────────────────────────────────────

    def _generar_interpretacion(self, res, masa, iters, prob_riesgo,
                                nivel, consumo_aprox, dias_min, dias_max):
        prom    = res["dias_promedio"]
        mediana = res["dias_mediana"]
        p5      = res["p5"]
        p95     = res["p95"]

        self.text_interp.configure(state="normal")
        self.text_recom.configure(state="normal")
        self.text_interp.delete("0.0", tk.END)
        self.text_recom.delete("0.0", tk.END)

        texto_duracion = (
            f"═════════════════════════════════════════════\n"
            f"  REPORTES DE DURACIÓN Y CONSUMO\n"
            f"═════════════════════════════════════════════\n\n"
            f"  ► CONCLUSIÓN PRINCIPAL:\n"
            f"    Los {masa:.1f} kg de masa alcanzarán para\n"
            f"    aprox. {prom} días (promedio).\n"
            f"    Consumo diario: ~{consumo_aprox:.1f} kg/día.\n"
            f"    La mediana de agotamiento es el día {mediana}.\n\n"
            f"  ► RANGOS ESTIMADOS (Intervalo 90%):\n"
            f"    • Optimista  : hasta {dias_max} días.\n"
            f"    • Pesimista  : tan pronto como el día {dias_min}.\n"
            f"    • Certeza 90%: entre el día {p5} y el {p95}.\n"
            f"      → 5% prob. de durar MÁS de {p95} días.\n"
            f"      → 5% prob. de durar MENOS de {p5} días."
        )

        texto_riesgo = (
            f"═════════════════════════════════════════════\n"
            f"  EVALUACIÓN DE RIESGO Y RECOMENDACIÓN\n"
            f"═════════════════════════════════════════════\n\n"
            f"  ► RIESGO DE DESABASTECIMIENTO:\n"
            f"    • Stockout ≤ 2 días: {prob_riesgo:.2f}%\n"
            f"    • Nivel de Alerta  : {nivel}\n\n"
            f"  ► RECOMENDACIÓN OPERATIVA:\n"
        )

        if nivel == "CRÍTICO":
            texto_riesgo += (
                "    [ALERTA MÁXIMA] Harina crítica.\n"
                "    Riesgo extremadamente alto de desabastecerse.\n"
                "    ¡Realice un pedido de harina INMEDIATAMENTE!\n"
                "    El stock no cubre la demanda de los próximos dos días."
            )
        elif nivel == "ALTO":
            texto_riesgo += (
                "    [ATENCIÓN] Riesgo inminente a corto plazo.\n"
                "    Programe una reposición urgente de harina hoy\n"
                "    o a primera hora de la mañana."
            )
        elif nivel == "MEDIO":
            texto_riesgo += (
                "    [PRECAUCIÓN] Nivel moderadamente seguro.\n"
                "    Planifique el siguiente abastecimiento de harina\n"
                "    en un plazo de 24 a 48 horas."
            )
        else:
            texto_riesgo += (
                "    [ESTADO SEGURO] Inventario suficiente.\n"
                "    No se requieren acciones inmediatas.\n"
                "    Planifique compras bajo el esquema ordinario."
            )

        self.text_interp.insert("0.0", texto_duracion)
        self.text_recom.insert("0.0", texto_riesgo)
        
        self.text_interp.configure(state="disabled")
        self.text_recom.configure(state="disabled")

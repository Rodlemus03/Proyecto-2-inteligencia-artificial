import tkinter as tk
from tkinter import ttk, messagebox, font
import itertools
import random
import time
from typing import List, Tuple, Set, Dict, Optional, Any
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Definir SentenceType como un tipo genérico para evitar errores de referencia circular
SentenceType = Any

# Colores disponibles en el juego
COLORES = ["azul", "rojo", "blanco", "negro", "verde", "purpura"]
COLOR_RGB = {
    "azul": "#0080FF",
    "rojo": "#FF0000",
    "blanco": "#FFFFFF",
    "negro": "#000000",
    "verde": "#00C000",
    "purpura": "#800080"
}

# Clases para los operadores lógicos
@dataclass
class Symbol:
    name: str
    
    def __repr__(self):
        return self.name
    
    def evaluate(self, model: Dict[str, bool]) -> bool:
        try:
            return bool(model[self.name])
        except KeyError:
            raise Exception(f"variable {self.name} not in model")
    
    def symbols(self) -> Set[str]:
        return {self.name}

@dataclass
class Not:
    operand: SentenceType
    
    def __repr__(self):
        return f"Not({self.operand})"
    
    def evaluate(self, model: Dict[str, bool]) -> bool:
        return not self.operand.evaluate(model)
    
    def symbols(self) -> Set[str]:
        return self.operand.symbols()

@dataclass
class And:
    conjuncts: List[SentenceType]
    
    def __repr__(self):
        conjunctions = ", ".join([str(conjunct) for conjunct in self.conjuncts])
        return f"And({conjunctions})"
    
    def add(self, conjunct: 'SentenceType') -> None:
        self.conjuncts.append(conjunct)
    
    def evaluate(self, model: Dict[str, bool]) -> bool:
        return all(conjunct.evaluate(model) for conjunct in self.conjuncts)
    
    def symbols(self) -> Set[str]:
        if not self.conjuncts:
            return set()
        return set().union(*[conjunct.symbols() for conjunct in self.conjuncts])

@dataclass
class Or:
    disjuncts: List[SentenceType]
    
    def __repr__(self):
        disjuncts = ", ".join([str(disjunct) for disjunct in self.disjuncts])
        return f"Or({disjuncts})"
    
    def evaluate(self, model: Dict[str, bool]) -> bool:
        return any(disjunct.evaluate(model) for disjunct in self.disjuncts)
    
    def symbols(self) -> Set[str]:
        if not self.disjuncts:
            return set()
        return set().union(*[disjunct.symbols() for disjunct in self.disjuncts])

@dataclass
class Implication:
    antecedent: SentenceType
    consequent: SentenceType
    
    def __repr__(self):
        return f"Implication({self.antecedent}, {self.consequent})"
    
    def evaluate(self, model: Dict[str, bool]) -> bool:
        return not self.antecedent.evaluate(model) or self.consequent.evaluate(model)
    
    def symbols(self) -> Set[str]:
        return self.antecedent.symbols().union(self.consequent.symbols())

@dataclass
class Biconditional:
    left: SentenceType
    right: SentenceType
    
    def __repr__(self):
        return f"Biconditional({self.left}, {self.right})"
    
    def evaluate(self, model: Dict[str, bool]) -> bool:
        return self.left.evaluate(model) == self.right.evaluate(model)
    
    def symbols(self) -> Set[str]:
        return self.left.symbols().union(self.right.symbols())

# Clase para la base de conocimiento del Mastermind
@dataclass
class MastermindKB:
    todas_combinaciones: List[Tuple[str, str, str, str]] = field(default_factory=lambda: list(itertools.product(COLORES, repeat=4)))
    combinaciones_posibles: Set[Tuple[str, str, str, str]] = field(init=False)
    knowledge: And = field(default_factory=lambda: And([]))
    symbols: Dict[Tuple[int, str], Symbol] = field(default_factory=dict)
    
    def __post_init__(self):
        self.combinaciones_posibles = set(self.todas_combinaciones)
        
        for pos in range(4):
            for color in COLORES:
                self.symbols[(pos, color)] = Symbol(f"{color}_{pos}")
    
    def actualizar_con_feedback(self, combinacion: Tuple[str, str, str, str], 
                              posiciones_correctas: int, 
                              colores_correctos: int) -> None:
        if posiciones_correctas + colores_correctos > 4:
            messagebox.showwarning("Advertencia", 
                              "Feedback inválido. La suma de posiciones correctas y\n"
                              "colores correctos no puede ser mayor que 4.")
            return
        
        nuevas_combinaciones = set()
        for candidato in self.combinaciones_posibles:
            if self._coincide_feedback(combinacion, candidato, posiciones_correctas, colores_correctos):
                nuevas_combinaciones.add(candidato)
        
        if not nuevas_combinaciones and self.combinaciones_posibles:
            messagebox.showwarning("Advertencia", 
                              "No hay combinaciones que coincidan con el feedback proporcionado.\n"
                              f"Feedback recibido: {posiciones_correctas} posiciones correctas, {colores_correctos} colores correctos\n"
                              "Es posible que haya un error en el feedback ingresado.")
            return
        
        self.combinaciones_posibles = nuevas_combinaciones
        
        self._agregar_restriccion_logica(combinacion, posiciones_correctas, colores_correctos)
        
    def _coincide_feedback(self, combinacion1: Tuple[str, str, str, str], 
                          combinacion2: Tuple[str, str, str, str], 
                          posiciones_correctas: int, 
                          colores_correctos: int) -> bool:
        counter1 = {color: 0 for color in COLORES}
        counter2 = {color: 0 for color in COLORES}
        
        pos_correctas = 0
        for i in range(4):
            if combinacion1[i] == combinacion2[i]:
                pos_correctas += 1
            else:
                counter1[combinacion1[i]] += 1
                counter2[combinacion2[i]] += 1
        
        colores_comunes = sum(min(counter1[color], counter2[color]) for color in COLORES)
        
        return pos_correctas == posiciones_correctas and colores_comunes == colores_correctos
    
    def _agregar_restriccion_logica(self, combinacion: Tuple[str, str, str, str], 
                                  posiciones_correctas: int, 
                                  colores_correctos: int) -> None:
        pass
        
    def siguiente_combinacion(self) -> Tuple[str, str, str, str]:
        if not self.combinaciones_posibles:
            messagebox.showwarning("Advertencia", 
                              "No hay combinaciones posibles restantes.\n"
                              "Esto puede deberse a un feedback inconsistente o a un error en el cálculo.\n"
                              "Reiniciando con una combinación aleatoria...")
            
            return tuple(random.choice(COLORES) for _ in range(4))
        
        if len(self.combinaciones_posibles) == len(self.todas_combinaciones):
            return ("azul", "azul", "rojo", "verde")
        
        if len(self.combinaciones_posibles) <= 2:
            return next(iter(self.combinaciones_posibles))
            
        if len(self.combinaciones_posibles) <= 10:
            return random.choice(list(self.combinaciones_posibles))
        
        combinaciones_a_evaluar = random.sample(
            list(self.combinaciones_posibles) if len(self.combinaciones_posibles) <= 50 
            else list(self.todas_combinaciones),
            min(20, len(self.combinaciones_posibles))
        )
        
        mejor_combinacion = None
        mejor_puntuacion = float('inf')
        
        for combinacion in combinaciones_a_evaluar:
            max_conjunto_restante = 0
            
            resultados = {}
            
            for candidato in random.sample(list(self.combinaciones_posibles), 
                                          min(50, len(self.combinaciones_posibles))):
                pos_correctas = 0
                counter1 = {color: 0 for color in COLORES}
                counter2 = {color: 0 for color in COLORES}
                
                for i in range(4):
                    if combinacion[i] == candidato[i]:
                        pos_correctas += 1
                    else:
                        counter1[combinacion[i]] += 1
                        counter2[candidato[i]] += 1
                
                colores_comunes = sum(min(counter1[color], counter2[color]) for color in COLORES)
                
                feedback = (pos_correctas, colores_comunes)
                if feedback not in resultados:
                    resultados[feedback] = 0
                resultados[feedback] += 1
                
                max_conjunto_restante = max(max_conjunto_restante, resultados[feedback])
            
            if max_conjunto_restante < mejor_puntuacion:
                mejor_puntuacion = max_conjunto_restante
                mejor_combinacion = combinacion
        
        if mejor_combinacion is None:
            return random.choice(list(self.combinaciones_posibles))
        
        return mejor_combinacion
    
    def tamano_espacio_busqueda(self) -> int:
        return len(self.combinaciones_posibles)

# Clase para el solucionador del Mastermind
@dataclass
class MastermindSolver:
    kb: MastermindKB = field(default_factory=MastermindKB)
    intentos: int = 0
    historia_espacio_busqueda: List[int] = field(default_factory=list)
    
    def evaluar_combinacion(self, combinacion: Tuple[str, str, str, str], 
                           combinacion_secreta: Tuple[str, str, str, str]) -> Tuple[int, int]:
        counter1 = {color: 0 for color in COLORES}
        counter2 = {color: 0 for color in COLORES}
        
        pos_correctas = 0
        for i in range(4):
            if combinacion[i] == combinacion_secreta[i]:
                pos_correctas += 1
            else:
                counter1[combinacion[i]] += 1
                counter2[combinacion_secreta[i]] += 1
        
        colores_comunes = sum(min(counter1[color], counter2[color]) for color in COLORES)
        
        return (pos_correctas, colores_comunes)
    
    def modo_automatico(self, combinacion_secreta: Tuple[str, str, str, str], log_callback=None) -> Tuple[int, List[int]]:
        self.kb = MastermindKB()
        self.intentos = 0
        self.historia_espacio_busqueda = [self.kb.tamano_espacio_busqueda()]
        
        while True:
            self.intentos += 1
            
            combinacion = self.kb.siguiente_combinacion()
            
            if log_callback:
                log_callback(f"Intento #{self.intentos}: {combinacion}")
            
            posiciones_correctas, colores_correctos = self.evaluar_combinacion(
                combinacion, combinacion_secreta
            )
            
            if log_callback:
                log_callback(f"Resultado: {posiciones_correctas} posiciones correctas, {colores_correctos} colores correctos")
            
            if posiciones_correctas == 4:
                if log_callback:
                    log_callback(f"¡Solución encontrada en {self.intentos} intentos!")
                return (self.intentos, self.historia_espacio_busqueda)
            
            self.kb.actualizar_con_feedback(combinacion, posiciones_correctas, colores_correctos)
            
            self.historia_espacio_busqueda.append(self.kb.tamano_espacio_busqueda())
            
            if log_callback:
                log_callback(f"Espacio de búsqueda reducido a {self.kb.tamano_espacio_busqueda()} combinaciones posibles.")
    
    def procesar_intento_tiempo_real(self, combinacion, pos_correctas, colores_correctos):
        if pos_correctas == 4:
            return True  # Solución encontrada
        
        self.kb.actualizar_con_feedback(combinacion, pos_correctas, colores_correctos)
        
        nuevo_tamano = self.kb.tamano_espacio_busqueda()
        self.historia_espacio_busqueda.append(nuevo_tamano)
        
        return False  # Continuar jugando

# Funciones auxiliares
def generar_combinacion_aleatoria() -> Tuple[str, str, str, str]:
    return tuple(random.choice(COLORES) for _ in range(4))

def convertir_entrada_a_combinacion(entrada: str) -> Optional[Tuple[str, str, str, str]]:
    if ',' in entrada:
        colores = [color.strip().lower() for color in entrada.split(',')]
    else:
        colores = [color.strip().lower() for color in entrada.split()]
    
    if len(colores) != 4:
        messagebox.showerror("Error", "¡Debes especificar exactamente 4 colores!")
        return None
    
    for color in colores:
        if color not in COLORES:
            messagebox.showerror("Error", f"Color '{color}' no válido. Los colores válidos son: {', '.join(COLORES)}")
            return None
    
    return tuple(colores)

def ejecutar_experimento_n_juegos(n_juegos, progreso_callback=None, log_callback=None):
    solver = MastermindSolver()
    
    intentos_por_juego = []
    todas_historias = []
    
    if log_callback:
        log_callback(f"Ejecutando {n_juegos} juegos automáticos...")
    
    inicio_total = time.time()
    
    for i in range(n_juegos):
        if progreso_callback:
            progreso_callback(i, n_juegos)
        
        if log_callback and i % 20 == 0:
            log_callback(f"Juego {i}/{n_juegos}")
            
        combinacion_secreta = generar_combinacion_aleatoria()
        
        intentos, historia = solver.modo_automatico(combinacion_secreta)
        
        intentos_por_juego.append(intentos)
        todas_historias.append(historia)
    
    fin_total = time.time()
    
    if log_callback:
        log_callback(f"Experimento completado en {fin_total - inicio_total:.2f} segundos")
    
    promedio_intentos = np.mean(intentos_por_juego)
    
    max_intentos = max(len(historia) for historia in todas_historias)
    
    espacio_por_intento = np.zeros((n_juegos, max_intentos))
    
    for i, historia in enumerate(todas_historias):
        for j, tamano in enumerate(historia):
            if j < max_intentos:  
                espacio_por_intento[i, j] = tamano
        
        ultimo_valor = historia[-1] if historia else 0
        for j in range(len(historia), max_intentos):
            espacio_por_intento[i, j] = ultimo_valor
    
    promedio_espacio_por_intento = np.mean(espacio_por_intento, axis=0)
    
    return {
        'promedio_intentos': promedio_intentos,
        'promedio_espacio_por_intento': promedio_espacio_por_intento,
        'intentos_por_juego': intentos_por_juego,
        'max_intentos': max_intentos,
        'tiempo_total': fin_total - inicio_total
    }

# Interfaz gráfica
class MastermindGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Solucionador de Mastermind")
        self.root.geometry("950x650")
        self.root.resizable(True, True)
        
        self.configurar_estilo()
        self.crear_widgets()
        
        self.solver = MastermindSolver()
        self.combinacion_secreta = None
        self.ultimo_intento = None
        self.modo_actual = None
        
    def configurar_estilo(self):
        self.titulo_font = font.Font(family="Helvetica", size=16, weight="bold")
        self.subtitulo_font = font.Font(family="Helvetica", size=14, weight="bold")
        self.texto_font = font.Font(family="Helvetica", size=12)
        self.codigo_font = font.Font(family="Courier", size=12)
        
        style = ttk.Style()
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TButton", font=self.texto_font, padding=5)
        style.configure("TLabel", font=self.texto_font, background="#f5f5f5")
        style.configure("Header.TLabel", font=self.subtitulo_font, background="#f5f5f5")
        style.configure("Title.TLabel", font=self.titulo_font, background="#f5f5f5")
        style.configure("TNotebook", background="#f5f5f5")
        style.configure("TNotebook.Tab", font=self.texto_font, padding=[10, 5])
        
    def crear_widgets(self):
        # Notebook principal
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestañas
        self.tab_inicio = ttk.Frame(self.notebook)
        self.tab_tiempo_real = ttk.Frame(self.notebook)
        self.tab_automatico = ttk.Frame(self.notebook)
        self.tab_experimento = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_inicio, text="Inicio")
        self.notebook.add(self.tab_tiempo_real, text="Modo Tiempo Real")
        self.notebook.add(self.tab_automatico, text="Modo Automático")
        self.notebook.add(self.tab_experimento, text="Experimento")
        
        # Configurar cada pestaña
        self.configurar_tab_inicio()
        self.configurar_tab_tiempo_real()
        self.configurar_tab_automatico()
        self.configurar_tab_experimento()
        
    def configurar_tab_inicio(self):
        frame = ttk.Frame(self.tab_inicio)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        ttk.Label(frame, text="SOLUCIONADOR DE MASTERMIND", style="Title.TLabel").pack(pady=20)
        
        # Descripción
        descripcion = (
            "Este programa implementa un solucionador inteligente para el juego Mastermind.\n\n"
            "Modos disponibles:\n"
            "• Modo en Tiempo Real: Juega contra la máquina dando retroalimentación.\n"
            "• Modo Automático: La máquina resuelve una combinación específica.\n"
            "• Experimento: Analiza el rendimiento del algoritmo en múltiples juegos.\n\n"
            "Colores disponibles: " + ", ".join(COLORES)
        )
        
        ttk.Label(frame, text=descripcion, wraplength=600, justify="center").pack(pady=20)
        
        # Frame para los botones de colores
        color_frame = ttk.Frame(frame)
        color_frame.pack(pady=20)
        
        for color in COLORES:
            boton = tk.Button(color_frame, width=3, height=1, bg=COLOR_RGB[color],
                             activebackground=COLOR_RGB[color])
            boton.pack(side=tk.LEFT, padx=5)
            
        # Botones para ir a cada modo
        botones_frame = ttk.Frame(frame)
        botones_frame.pack(pady=20)
        
        ttk.Button(botones_frame, text="Modo en Tiempo Real", 
                  command=lambda: self.notebook.select(1)).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(botones_frame, text="Modo Automático", 
                  command=lambda: self.notebook.select(2)).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(botones_frame, text="Experimento", 
                  command=lambda: self.notebook.select(3)).pack(side=tk.LEFT, padx=10)
        
    def configurar_tab_tiempo_real(self):
        # Dividir en dos columnas
        panel_izquierdo = ttk.Frame(self.tab_tiempo_real)
        panel_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        panel_derecho = ttk.Frame(self.tab_tiempo_real)
        panel_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo - Controles
        ttk.Label(panel_izquierdo, text="Modo en Tiempo Real", style="Header.TLabel").pack(pady=10)
        
        ttk.Label(panel_izquierdo, text="Piensa en una combinación secreta y dale retroalimentación\nal algoritmo para ver cómo la encuentra.",
                 wraplength=350).pack(pady=10)
        
        ttk.Button(panel_izquierdo, text="Iniciar juego", 
                  command=self.iniciar_tiempo_real).pack(pady=10)
        
        # Frame para mostrar intento actual
        self.frame_intento_actual = ttk.Frame(panel_izquierdo)
        self.frame_intento_actual.pack(pady=20, fill=tk.X)
        
        ttk.Label(self.frame_intento_actual, text="Propuesta del algoritmo:").pack()
        
        self.frame_fichas = ttk.Frame(self.frame_intento_actual)
        self.frame_fichas.pack(pady=10)
        
        self.fichas_labels = []
        for i in range(4):
            lbl = tk.Label(self.frame_fichas, width=3, height=1, bg="lightgray")
            lbl.pack(side=tk.LEFT, padx=5)
            self.fichas_labels.append(lbl)
            
        # Frame para retroalimentación
        self.frame_feedback = ttk.Frame(panel_izquierdo)
        self.frame_feedback.pack(pady=10, fill=tk.X)
        
        ttk.Label(self.frame_feedback, text="Retroalimentación:").pack()
        
        feedback_controls = ttk.Frame(self.frame_feedback)
        feedback_controls.pack(pady=10)
        
        ttk.Label(feedback_controls, text="Posiciones correctas:").grid(row=0, column=0, padx=5, pady=5)
        self.pos_correctas_var = tk.StringVar(value="0")
        ttk.Spinbox(feedback_controls, from_=0, to=4, width=5, textvariable=self.pos_correctas_var).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(feedback_controls, text="Colores correctos:").grid(row=1, column=0, padx=5, pady=5)
        self.colores_correctos_var = tk.StringVar(value="0")
        ttk.Spinbox(feedback_controls, from_=0, to=4, width=5, textvariable=self.colores_correctos_var).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(self.frame_feedback, text="Enviar retroalimentación", 
                  command=self.procesar_feedback_tiempo_real).pack(pady=10)
        
        # Info del espacio de búsqueda
        self.frame_info_tr = ttk.Frame(panel_izquierdo)
        self.frame_info_tr.pack(pady=10, fill=tk.X)
        
        ttk.Label(self.frame_info_tr, text="Información:").pack()
        
        info_grid = ttk.Frame(self.frame_info_tr)
        info_grid.pack(pady=10)
        
        ttk.Label(info_grid, text="Intento actual:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.lbl_intento_actual = ttk.Label(info_grid, text="0")
        self.lbl_intento_actual.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(info_grid, text="Combinaciones posibles:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.lbl_combinaciones_tr = ttk.Label(info_grid, text="1296")
        self.lbl_combinaciones_tr.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # Panel derecho - Historial
        ttk.Label(panel_derecho, text="Historial", style="Header.TLabel").pack(pady=10)
        
        # Frame para el historial
        historial_frame = ttk.Frame(panel_derecho)
        historial_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbar y Text widget para el historial
        scrollbar = ttk.Scrollbar(historial_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.historial_text = tk.Text(historial_frame, width=40, height=20, yscrollcommand=scrollbar.set)
        self.historial_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.historial_text.config(state=tk.DISABLED)
        
        scrollbar.config(command=self.historial_text.yview)
        
        # Ocultar inicialmente los frames de juego
        self.frame_intento_actual.pack_forget()
        self.frame_feedback.pack_forget()
        self.frame_info_tr.pack_forget()
    
    def configurar_tab_automatico(self):
        # Dividir en dos columnas
        panel_izquierdo = ttk.Frame(self.tab_automatico)
        panel_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        panel_derecho = ttk.Frame(self.tab_automatico)
        panel_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo - Controles
        ttk.Label(panel_izquierdo, text="Modo Automático", style="Header.TLabel").pack(pady=10)
        
        ttk.Label(panel_izquierdo, text="Define una combinación secreta o genera una aleatoria\npara que el algoritmo la resuelva automáticamente.",
                 wraplength=350).pack(pady=10)
        
        # Frame para la combinación secreta
        secret_frame = ttk.Frame(panel_izquierdo)
        secret_frame.pack(pady=20, fill=tk.X)
        
        ttk.Label(secret_frame, text="Combinación secreta:").pack()
        
        entrada_frame = ttk.Frame(secret_frame)
        entrada_frame.pack(pady=10)
        
        self.entrada_combinacion = ttk.Entry(entrada_frame, width=30)
        self.entrada_combinacion.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(entrada_frame, text="(ej: azul, rojo, verde, negro)").pack(side=tk.LEFT)
        
        botones_frame = ttk.Frame(secret_frame)
        botones_frame.pack(pady=10)
        
        ttk.Button(botones_frame, text="Generar aleatoria", 
                  command=self.generar_aleatoria).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(botones_frame, text="Iniciar solución", 
                  command=self.iniciar_automatico).pack(side=tk.LEFT, padx=5)
        
        # Frame para mostrar secreto
        self.frame_secreto = ttk.Frame(panel_izquierdo)
        self.frame_secreto.pack(pady=10, fill=tk.X)
        
        ttk.Label(self.frame_secreto, text="Combinación secreta:").pack()
        
        self.frame_secreto_fichas = ttk.Frame(self.frame_secreto)
        self.frame_secreto_fichas.pack(pady=10)
        
        self.secreto_labels = []
        for i in range(4):
            lbl = tk.Label(self.frame_secreto_fichas, width=3, height=1, bg="lightgray")
            lbl.pack(side=tk.LEFT, padx=5)
            self.secreto_labels.append(lbl)
        
        # Frame para información y progreso
        self.frame_info_auto = ttk.Frame(panel_izquierdo)
        self.frame_info_auto.pack(pady=10, fill=tk.X)
        
        ttk.Label(self.frame_info_auto, text="Información:").pack()
        
        info_auto_grid = ttk.Frame(self.frame_info_auto)
        info_auto_grid.pack(pady=10)
        
        ttk.Label(info_auto_grid, text="Intento actual:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.lbl_intento_auto = ttk.Label(info_auto_grid, text="0")
        self.lbl_intento_auto.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(info_auto_grid, text="Combinaciones posibles:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.lbl_combinaciones_auto = ttk.Label(info_auto_grid, text="1296")
        self.lbl_combinaciones_auto.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(info_auto_grid, text="Tiempo transcurrido:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.lbl_tiempo_auto = ttk.Label(info_auto_grid, text="0.00 seg")
        self.lbl_tiempo_auto.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Panel derecho - Historial y resultados
        ttk.Label(panel_derecho, text="Historial", style="Header.TLabel").pack(pady=10)
        
        # Frame para el historial
        historial_auto_frame = ttk.Frame(panel_derecho)
        historial_auto_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbar y Text widget para el historial
        scrollbar_auto = ttk.Scrollbar(historial_auto_frame)
        scrollbar_auto.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.historial_auto_text = tk.Text(historial_auto_frame, width=40, height=20, yscrollcommand=scrollbar_auto.set)
        self.historial_auto_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.historial_auto_text.config(state=tk.DISABLED)
        
        scrollbar_auto.config(command=self.historial_auto_text.yview)
        
        # Resultados y gráfico
        self.frame_resultados_auto = ttk.Frame(panel_derecho)
        self.frame_resultados_auto.pack(fill=tk.X, pady=10)
        
        # Botón para ver gráfico
        ttk.Button(self.frame_resultados_auto, text="Ver gráfico de espacio de búsqueda", 
                  command=self.mostrar_grafico_auto).pack(pady=10)
        
        # Ocultar inicialmente los frames de resultados
        self.frame_secreto.pack_forget()
        self.frame_info_auto.pack_forget()
        self.frame_resultados_auto.pack_forget()
    
    def configurar_tab_experimento(self):
        # Controles principales
        controles_frame = ttk.Frame(self.tab_experimento)
        controles_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(controles_frame, text="Experimento", style="Header.TLabel").pack(pady=10)
        
        ttk.Label(controles_frame, text="Ejecuta un experimento con múltiples juegos aleatorios\npara analizar el rendimiento del algoritmo.",
                 wraplength=600, justify="center").pack(pady=10)
        
        # Frame para configurar número de juegos
        config_frame = ttk.Frame(controles_frame)
        config_frame.pack(pady=20)
        
        ttk.Label(config_frame, text="Número de juegos:").grid(row=0, column=0, padx=5, pady=5)
        
        self.num_juegos_var = tk.StringVar(value="100")
        ttk.Spinbox(config_frame, from_=10, to=500, increment=10, width=5, 
                   textvariable=self.num_juegos_var).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(config_frame, text="Iniciar experimento", 
                  command=self.iniciar_experimento).grid(row=0, column=2, padx=20, pady=5)
        
        # Frame para la barra de progreso
        progreso_frame = ttk.Frame(controles_frame)
        progreso_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(progreso_frame, text="Progreso:").pack(anchor="w")
        
        self.barra_progreso = ttk.Progressbar(progreso_frame, orient="horizontal", length=600, mode="determinate")
        self.barra_progreso.pack(fill=tk.X, pady=5)
        
        self.lbl_progreso = ttk.Label(progreso_frame, text="0%")
        self.lbl_progreso.pack(anchor="e")
        
        # Frame para el log
        log_frame = ttk.Frame(self.tab_experimento)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(log_frame, text="Registro del experimento:").pack(anchor="w")
        
        # Scrollbar y Text widget para el log
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_log = ttk.Scrollbar(log_text_frame)
        scrollbar_log.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.experimento_log = tk.Text(log_text_frame, height=10, yscrollcommand=scrollbar_log.set)
        self.experimento_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.experimento_log.config(state=tk.DISABLED)
        
        scrollbar_log.config(command=self.experimento_log.yview)
        
        # Frame para resultados
        self.resultados_exp_frame = ttk.Frame(self.tab_experimento)
        self.resultados_exp_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(self.resultados_exp_frame, text="Resultados:", style="Header.TLabel").pack(anchor="w", pady=5)
        
        # Grid para métricas
        metricas_frame = ttk.Frame(self.resultados_exp_frame)
        metricas_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(metricas_frame, text="Promedio de intentos:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.lbl_prom_intentos = ttk.Label(metricas_frame, text="0.00")
        self.lbl_prom_intentos.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(metricas_frame, text="Tiempo total:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.lbl_tiempo_exp = ttk.Label(metricas_frame, text="0.00 seg")
        self.lbl_tiempo_exp.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # Botón para mostrar gráfico
        ttk.Button(self.resultados_exp_frame, text="Ver gráfico de espacio de búsqueda", 
                  command=self.mostrar_grafico_experimento).pack(pady=10)
        
        # Ocultar frame de resultados inicialmente
        self.resultados_exp_frame.pack_forget()
    
    # Funciones para el modo tiempo real
    def iniciar_tiempo_real(self):
        self.modo_actual = "tiempo_real"
        self.solver = MastermindSolver()
        
        # Mostrar los frames de juego
        self.frame_intento_actual.pack(pady=20, fill=tk.X)
        self.frame_feedback.pack(pady=10, fill=tk.X)
        self.frame_info_tr.pack(pady=10, fill=tk.X)
        
        # Limpiar historial
        self.historial_text.config(state=tk.NORMAL)
        self.historial_text.delete('1.0', tk.END)
        self.historial_text.config(state=tk.DISABLED)
        
        # Actualizar información
        self.lbl_intento_actual.config(text="1")
        self.lbl_combinaciones_tr.config(text=str(self.solver.kb.tamano_espacio_busqueda()))
        
        # Obtener primera propuesta
        combinacion = self.solver.kb.siguiente_combinacion()
        self.ultimo_intento = combinacion
        
        # Actualizar visualización de fichas
        self.actualizar_fichas(combinacion)
        
        # Añadir al historial
        self.agregar_historial(f"Intento #1:\nPropuesta: {combinacion}")
    
    def actualizar_fichas(self, combinacion):
        for i, color in enumerate(combinacion):
            self.fichas_labels[i].config(bg=COLOR_RGB[color])
    
    def agregar_historial(self, texto):
        self.historial_text.config(state=tk.NORMAL)
        self.historial_text.insert(tk.END, texto + "\n\n")
        self.historial_text.see(tk.END)
        self.historial_text.config(state=tk.DISABLED)
    
    def procesar_feedback_tiempo_real(self):
        try:
            pos_correctas = int(self.pos_correctas_var.get())
            colores_correctos = int(self.colores_correctos_var.get())
            
            if pos_correctas < 0 or pos_correctas > 4 or colores_correctos < 0 or colores_correctos > 4:
                messagebox.showerror("Error", "Los valores deben estar entre 0 y 4.")
                return
                
            if pos_correctas + colores_correctos > 4:
                messagebox.showerror("Error", "La suma de posiciones correctas y colores correctos no puede exceder 4.")
                return
                
            # Añadir al historial
            self.agregar_historial(f"Feedback: {pos_correctas} posiciones correctas, {colores_correctos} colores correctos")
            
            # Si todas las posiciones son correctas, hemos terminado
            if pos_correctas == 4:
                self.agregar_historial(f"¡Solución encontrada en {self.solver.intentos} intentos!")
                messagebox.showinfo("¡Éxito!", f"¡He encontrado tu combinación secreta en {self.solver.intentos} intentos!")
                return
            
            # Procesar el feedback
            solucion_encontrada = self.solver.procesar_intento_tiempo_real(
                self.ultimo_intento, pos_correctas, colores_correctos)
            
            if solucion_encontrada:
                return
                
            # Actualizar contador de intentos
            self.solver.intentos += 1
            self.lbl_intento_actual.config(text=str(self.solver.intentos))
            
            # Actualizar espacio de búsqueda
            self.lbl_combinaciones_tr.config(text=str(self.solver.kb.tamano_espacio_busqueda()))
            self.agregar_historial(f"Espacio de búsqueda reducido a {self.solver.kb.tamano_espacio_busqueda()} combinaciones posibles.")
            
            # Obtener siguiente propuesta
            combinacion = self.solver.kb.siguiente_combinacion()
            self.ultimo_intento = combinacion
            
            # Actualizar visualización de fichas
            self.actualizar_fichas(combinacion)
            
            # Añadir al historial
            self.agregar_historial(f"Intento #{self.solver.intentos}:\nPropuesta: {combinacion}")
            
        except ValueError:
            messagebox.showerror("Error", "Por favor, ingrese valores numéricos válidos.")
    
    # Funciones para el modo automático
    def generar_aleatoria(self):
        combinacion = generar_combinacion_aleatoria()
        self.entrada_combinacion.delete(0, tk.END)
        self.entrada_combinacion.insert(0, ", ".join(combinacion))
    
    def iniciar_automatico(self):
        # Obtener combinación secreta
        entrada = self.entrada_combinacion.get().strip()
        if entrada:
            combinacion_secreta = convertir_entrada_a_combinacion(entrada)
            if combinacion_secreta is None:
                return
        else:
            combinacion_secreta = generar_combinacion_aleatoria()
            self.entrada_combinacion.delete(0, tk.END)
            self.entrada_combinacion.insert(0, ", ".join(combinacion_secreta))
        
        self.combinacion_secreta = combinacion_secreta
        self.modo_actual = "automatico"
        
        # Mostrar frames
        self.frame_secreto.pack(pady=10, fill=tk.X)
        self.frame_info_auto.pack(pady=10, fill=tk.X)
        self.frame_resultados_auto.pack(fill=tk.X, pady=10)
        
        # Actualizar visualización de secreto
        for i, color in enumerate(combinacion_secreta):
            self.secreto_labels[i].config(bg=COLOR_RGB[color])
        
        # Limpiar historial
        self.historial_auto_text.config(state=tk.NORMAL)
        self.historial_auto_text.delete('1.0', tk.END)
        self.historial_auto_text.config(state=tk.DISABLED)
        
        # Iniciar solución en un thread
        self.resolver_automatico(combinacion_secreta)
    
    def resolver_automatico(self, combinacion_secreta):
        self.solver = MastermindSolver()
        
        # Actualizar información inicial
        self.lbl_intento_auto.config(text="0")
        self.lbl_combinaciones_auto.config(text=str(len(self.solver.kb.todas_combinaciones)))
        self.lbl_tiempo_auto.config(text="0.00 seg")
        
        # Función para actualizar el historial
        def log_callback(texto):
            self.historial_auto_text.config(state=tk.NORMAL)
            self.historial_auto_text.insert(tk.END, texto + "\n")
            self.historial_auto_text.see(tk.END)
            self.historial_auto_text.config(state=tk.DISABLED)
            
            # Actualizar contador de intentos si es posible
            if texto.startswith("Intento #"):
                intento_num = texto.split("#")[1].split(":")[0]
                self.lbl_intento_auto.config(text=intento_num)
            
            # Actualizar espacio de búsqueda si es posible
            if "Espacio de búsqueda reducido a" in texto:
                espacio = texto.split("reducido a")[1].split(" ")[1]
                self.lbl_combinaciones_auto.config(text=espacio)
            
            # Actualizar tiempo (esto es simulado, el tiempo real se ajusta después)
            self.root.update()
        
        # Iniciar tiempo
        inicio = time.time()
        
        # Resolver
        log_callback("Resolviendo combinación secreta...")
        intentos, historia = self.solver.modo_automatico(combinacion_secreta, log_callback)
        
        # Calcular tiempo
        fin = time.time()
        tiempo_total = fin - inicio
        
        # Actualizar tiempo
        self.lbl_tiempo_auto.config(text=f"{tiempo_total:.2f} seg")
        
        # Mostrar mensaje final
        messagebox.showinfo("¡Solución encontrada!", 
                          f"Se ha encontrado la solución en {intentos} intentos\nTiempo: {tiempo_total:.2f} segundos")
    
    def mostrar_grafico_auto(self):
        if self.modo_actual != "automatico" or not hasattr(self.solver, 'historia_espacio_busqueda'):
            messagebox.showinfo("Información", "Primero debe ejecutar una solución automática.")
            return
            
        # Crear una ventana para el gráfico
        ventana_grafico = tk.Toplevel(self.root)
        ventana_grafico.title("Espacio de búsqueda")
        ventana_grafico.geometry("800x600")
        
        # Crear figura y gráfico
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        
        historia = self.solver.historia_espacio_busqueda
        intentos = range(len(historia))
        
        # Crear barras
        bars = ax.bar(intentos, historia, color='#1f77b4', width=0.7)
        
        # Añadir línea de intentos
        promedio_intentos = self.solver.intentos
        ax.axvline(x=promedio_intentos-1, color='red', linestyle='-', linewidth=2)
        
        # Añadir texto explicativo
        ax.text(promedio_intentos-0.5, max(historia) * 0.8, 
                f"Intentos hasta solución: {promedio_intentos}", 
                color='red', fontsize=12, ha='left', va='center')
        
        # Añadir valores en las barras
        for i, bar in enumerate(bars):
            if historia[i] > 0:
                ax.text(i, bar.get_height() + (max(historia) * 0.01), 
                       f"{int(historia[i])}", 
                       ha='center', va='bottom', fontsize=10)
        
        # Configurar etiquetas
        ax.set_title('Espacio de búsqueda por intento', fontsize=16)
        ax.set_ylabel('Número de combinaciones posibles', fontsize=12)
        ax.set_xlabel('Número de intento', fontsize=12)
        
        ax.set_xticks(intentos)
        ax.set_xticklabels([f'{i}' for i in intentos])
        
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Crear el canvas y mostrarlo
        canvas = FigureCanvasTkAgg(fig, master=ventana_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # Funciones para el experimento
    def iniciar_experimento(self):
        try:
            num_juegos = int(self.num_juegos_var.get())
            if num_juegos < 1:
                messagebox.showerror("Error", "El número de juegos debe ser mayor que 0.")
                return
        except ValueError:
            messagebox.showerror("Error", "Por favor, ingrese un número válido.")
            return
        
        # Limpiar log
        self.experimento_log.config(state=tk.NORMAL)
        self.experimento_log.delete('1.0', tk.END)
        self.experimento_log.config(state=tk.DISABLED)
        
        # Reiniciar barra de progreso
        self.barra_progreso['value'] = 0
        self.lbl_progreso.config(text="0%")
        
        # Ocultar resultados previos
        self.resultados_exp_frame.pack_forget()
        
        # Función para actualizar el log
        def log_callback(texto):
            self.experimento_log.config(state=tk.NORMAL)
            self.experimento_log.insert(tk.END, texto + "\n")
            self.experimento_log.see(tk.END)
            self.experimento_log.config(state=tk.DISABLED)
            self.root.update()
        
        # Función para actualizar la barra de progreso
        def progreso_callback(actual, total):
            porcentaje = int((actual / total) * 100)
            self.barra_progreso['value'] = porcentaje
            self.lbl_progreso.config(text=f"{porcentaje}%")
            self.root.update()
        
        # Ejecutar experimento
        log_callback(f"Iniciando experimento con {num_juegos} juegos...")
        resultados = ejecutar_experimento_n_juegos(num_juegos, progreso_callback, log_callback)
        
        # Mostrar resultados
        self.resultados_exp_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Actualizar métricas
        self.lbl_prom_intentos.config(text=f"{resultados['promedio_intentos']:.2f}")
        self.lbl_tiempo_exp.config(text=f"{resultados['tiempo_total']:.2f} seg")
        
        # Guardar resultados para el gráfico
        self.resultados_experimento = resultados
        
        # Mostrar resumen
        log_callback("\n=== RESUMEN DEL EXPERIMENTO ===")
        log_callback(f"Número de juegos: {num_juegos}")
        log_callback(f"Promedio de intentos: {resultados['promedio_intentos']:.2f}")
        log_callback(f"Tiempo total: {resultados['tiempo_total']:.2f} segundos")
        
        # Reducción del espacio de búsqueda
        espacio_promedio = resultados['promedio_espacio_por_intento']
        if len(espacio_promedio) > 1:
            log_callback("\nReducción del espacio de búsqueda:")
            for i in range(1, min(10, len(espacio_promedio))):
                if espacio_promedio[i-1] > 0:
                    porcentaje = (1 - (espacio_promedio[i] / espacio_promedio[i-1])) * 100
                    log_callback(f"Reducción tras intento {i}: {int(espacio_promedio[i-1])} → {int(espacio_promedio[i])} ({porcentaje:.1f}%)")
    
    def mostrar_grafico_experimento(self):
        if not hasattr(self, 'resultados_experimento'):
            messagebox.showinfo("Información", "Primero debe ejecutar un experimento.")
            return
            
        # Crear una ventana para el gráfico
        ventana_grafico = tk.Toplevel(self.root)
        ventana_grafico.title("Resultados del Experimento")
        ventana_grafico.geometry("800x600")
        
        # Crear figura y gráfico
        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        
        promedio_intentos = self.resultados_experimento['promedio_intentos']
        promedio_espacio = self.resultados_experimento['promedio_espacio_por_intento']
        
        intentos = np.arange(len(promedio_espacio))
        
        # Crear barras
        bars = ax.bar(intentos, promedio_espacio, color='#1f77b4', width=0.7)
        
        # Añadir línea de intentos promedio
        promedio_redondeado = round(promedio_intentos)
        ax.axvline(x=promedio_redondeado, color='red', linestyle='-', linewidth=2)
        
        # Añadir texto explicativo
        ax.text(promedio_redondeado + 0.5, max(promedio_espacio) * 0.8, 
                f"Promedio de intentos\nhasta solución: {promedio_intentos:.2f}", 
                color='red', fontsize=12, ha='left', va='center')
        
        # Añadir valores en las barras
        for i, bar in enumerate(bars):
            if promedio_espacio[i] > 0:
                ax.text(i, bar.get_height() + (max(promedio_espacio) * 0.01), 
                       f"{int(promedio_espacio[i])}", 
                       ha='center', va='bottom', fontsize=10)
        
        # Configurar etiquetas
        ax.set_title('Espacio de búsqueda promedio por intento', fontsize=16)
        ax.set_ylabel('Espacio de búsqueda', fontsize=12)
        ax.set_xlabel('Número de intento', fontsize=12)
        
        ax.set_xticks(intentos)
        ax.set_xticklabels([f'{i}' for i in intentos])
        
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Crear el canvas y mostrarlo
        canvas = FigureCanvasTkAgg(fig, master=ventana_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def main():
    root = tk.Tk()
    app = MastermindGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
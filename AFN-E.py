import tkinter as tk
from tkinter import ttk, messagebox
import traceback
import math

# ----------------------------------------------------------------------
# Clases para el autómata (AFND-ε)
# ----------------------------------------------------------------------
class Estado:
    def __init__(self, id_, final=False, token_tipo=None):
        self.id = id_
        self.final = final
        self.token_tipo = token_tipo

class AFNDepsilon:
    def __init__(self):
        self.estados = []
        self.transiciones = {}   # (origen, simbolo) -> set(destinos)
        self.siguiente_id = 0

    def nuevo_estado(self, final=False, token_tipo=None):
        estado = Estado(self.siguiente_id, final, token_tipo)
        self.estados.append(estado)
        self.siguiente_id += 1
        return estado

    def agregar_transicion(self, origen, destino, simbolo):
        key = (origen.id, simbolo)
        if key not in self.transiciones:
            self.transiciones[key] = set()
        self.transiciones[key].add(destino)

    def clausura_epsilon(self, conjunto):
        pila = list(conjunto)
        cerrado = set(conjunto)
        while pila:
            s = pila.pop()
            key = (s.id, 'ε')
            if key in self.transiciones:
                for t in self.transiciones[key]:
                    if t not in cerrado:
                        cerrado.add(t)
                        pila.append(t)
        return cerrado

    def mover(self, conjunto, simbolo):
        resultado = set()
        for s in conjunto:
            key = (s.id, simbolo)
            if key in self.transiciones:
                resultado.update(self.transiciones[key])
        return resultado

# ----------------------------------------------------------------------
# Construcción del AFND-ε global
# ----------------------------------------------------------------------
def construir_afnd_lexer():
    afnd = AFNDepsilon()
    q_start = afnd.nuevo_estado()

    # Identificador
    id_inicio = afnd.nuevo_estado()
    id_final = afnd.nuevo_estado(final=True, token_tipo="IDENTIFICADOR")
    for ch in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_':
        afnd.agregar_transicion(id_inicio, id_final, ch)
    for ch in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_':
        afnd.agregar_transicion(id_final, id_final, ch)

    # Número
    num_q0 = afnd.nuevo_estado()
    num_q1 = afnd.nuevo_estado()
    num_q2 = afnd.nuevo_estado()
    num_final = afnd.nuevo_estado(final=True, token_tipo="NUMERO")
    for d in '0123456789':
        afnd.agregar_transicion(num_q0, num_q1, d)
        afnd.agregar_transicion(num_q1, num_q1, d)
        afnd.agregar_transicion(num_q2, num_final, d)
        afnd.agregar_transicion(num_final, num_final, d)
    afnd.agregar_transicion(num_q1, num_final, 'ε')
    afnd.agregar_transicion(num_q1, num_q2, '.')

    # Operador
    op_inicio = afnd.nuevo_estado()
    op_final = afnd.nuevo_estado(final=True, token_tipo="OPERADOR")
    for op in '+-*/^':
        afnd.agregar_transicion(op_inicio, op_final, op)

    # Paréntesis izquierdo
    paren_izq_inicio = afnd.nuevo_estado()
    paren_izq_final = afnd.nuevo_estado(final=True, token_tipo="PAREN_IZQ")
    afnd.agregar_transicion(paren_izq_inicio, paren_izq_final, '(')

    # Paréntesis derecho
    paren_der_inicio = afnd.nuevo_estado()
    paren_der_final = afnd.nuevo_estado(final=True, token_tipo="PAREN_DER")
    afnd.agregar_transicion(paren_der_inicio, paren_der_final, ')')

    # Unión mediante ε
    afnd.agregar_transicion(q_start, id_inicio, 'ε')
    afnd.agregar_transicion(q_start, num_q0, 'ε')
    afnd.agregar_transicion(q_start, op_inicio, 'ε')
    afnd.agregar_transicion(q_start, paren_izq_inicio, 'ε')
    afnd.agregar_transicion(q_start, paren_der_inicio, 'ε')

    afnd.q_start = q_start
    return afnd

# ----------------------------------------------------------------------
# Lexer basado en el AFND-ε
# ----------------------------------------------------------------------
class Token:
    def __init__(self, tipo, valor):
        self.tipo = tipo
        self.valor = valor

class Lexer:
    def __init__(self, texto):
        self.texto = texto
        self.afnd = construir_afnd_lexer()

    def analizar(self):
        tokens = []
        pos = 0
        n = len(self.texto)
        while pos < n:
            while pos < n and self.texto[pos].isspace():
                pos += 1
            if pos >= n:
                break

            current = self.afnd.clausura_epsilon({self.afnd.q_start})
            last_valid_pos = None
            last_token_tipo = None
            last_token_value = None
            start = pos

            while pos < n:
                c = self.texto[pos]
                next_set = self.afnd.mover(current, c)
                if not next_set:
                    break
                next_set = self.afnd.clausura_epsilon(next_set)
                if not next_set:
                    break
                current = next_set
                pos += 1

                for s in current:
                    if s.final:
                        last_valid_pos = pos
                        last_token_tipo = s.token_tipo
                        last_token_value = self.texto[start:pos]

            if last_valid_pos is None:
                raise Exception(f"Error Léxico: carácter no reconocido '{self.texto[start]}'")

            if last_token_tipo == "NUMERO":
                valor = float(last_token_value)
                tokens.append(Token("NUMERO", valor))
            elif last_token_tipo == "IDENTIFICADOR":
                tokens.append(Token("IDENTIFICADOR", last_token_value))
            elif last_token_tipo == "OPERADOR":
                tokens.append(Token("OPERADOR", last_token_value))
            elif last_token_tipo == "PAREN_IZQ":
                tokens.append(Token("PAREN_IZQ", last_token_value))
            elif last_token_tipo == "PAREN_DER":
                tokens.append(Token("PAREN_DER", last_token_value))
            else:
                tokens.append(Token(last_token_tipo, last_token_value))

            pos = last_valid_pos
        return tokens

# ----------------------------------------------------------------------
# Post‑procesamiento
# ----------------------------------------------------------------------
def combinar_menos_unario(tokens):
    nuevos = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if (tok.tipo == "OPERADOR" and tok.valor == '-' and
            i+1 < len(tokens) and tokens[i+1].tipo == "NUMERO"):
            if (i == 0 or tokens[i-1].tipo in ("OPERADOR", "PAREN_IZQ")):
                numero = tokens[i+1].valor
                nuevos.append(Token("NUMERO", -numero))
                i += 2
                continue
        nuevos.append(tok)
        i += 1
    return nuevos

def insertar_multiplicacion_implicita(tokens):
    nuevos = []
    for i, tok in enumerate(tokens):
        nuevos.append(tok)
        if i < len(tokens) - 1:
            actual = tok
            siguiente = tokens[i+1]
            if actual.tipo == "NUMERO" and siguiente.tipo == "PAREN_IZQ":
                nuevos.append(Token("OPERADOR", "*"))
            elif actual.tipo == "PAREN_DER" and siguiente.tipo == "NUMERO":
                nuevos.append(Token("OPERADOR", "*"))
            elif actual.tipo == "PAREN_DER" and siguiente.tipo == "PAREN_IZQ":
                nuevos.append(Token("OPERADOR", "*"))
            elif actual.tipo == "NUMERO" and siguiente.tipo == "IDENTIFICADOR":
                nuevos.append(Token("OPERADOR", "*"))
            elif actual.tipo == "IDENTIFICADOR" and siguiente.tipo == "NUMERO":
                nuevos.append(Token("OPERADOR", "*"))
            elif actual.tipo == "IDENTIFICADOR" and siguiente.tipo == "PAREN_IZQ":
                nuevos.append(Token("OPERADOR", "*"))
            elif actual.tipo == "PAREN_DER" and siguiente.tipo == "IDENTIFICADOR":
                nuevos.append(Token("OPERADOR", "*"))
            elif actual.tipo == "IDENTIFICADOR" and siguiente.tipo == "IDENTIFICADOR":
                nuevos.append(Token("OPERADOR", "*"))
    return nuevos

# ----------------------------------------------------------------------
# Parser y Evaluador
# ----------------------------------------------------------------------
class Nodo:
    def __init__(self, valor, izq=None, der=None):
        self.valor = valor
        self.izq = izq
        self.der = der

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.ops = []
        self.valores = []

    def prioridad(self, op):
        tabla = {'+':1, '-':1, '*':2, '/':2, '^':3}
        return tabla.get(op, 0)

    def reducir(self):
        if len(self.valores) < 2 or len(self.ops) < 1:
            raise Exception("Error Sintáctico: Faltan operandos u operadores")
        op = self.ops.pop()
        der = self.valores.pop()
        izq = self.valores.pop()
        self.valores.append(Nodo(op, izq, der))

    def construir(self):
        if not self.tokens:
            raise Exception("Error Sintáctico: Expresión vacía")
        for t in self.tokens:
            if t.tipo == "NUMERO":
                self.valores.append(Nodo(t.valor))
            elif t.tipo == "IDENTIFICADOR":
                self.valores.append(Nodo(t.valor))
            elif t.tipo == "OPERADOR":
                while (self.ops and self.ops[-1] != "(" and
                       self.prioridad(self.ops[-1]) >= self.prioridad(t.valor)):
                    self.reducir()
                self.ops.append(t.valor)
            elif t.tipo == "PAREN_IZQ":
                self.ops.append("(")
            elif t.tipo == "PAREN_DER":
                while self.ops and self.ops[-1] != "(":
                    self.reducir()
                if not self.ops:
                    raise Exception("Error Sintáctico: Paréntesis derecho sin abrir")
                self.ops.pop()
        while self.ops:
            if self.ops[-1] == "(":
                raise Exception("Error Sintáctico: Paréntesis izquierdo sin cerrar")
            self.reducir()
        if len(self.valores) != 1:
            raise Exception("Error Sintáctico: Expresión incompleta")
        return self.valores[0]

class Evaluador:
    def evaluar(self, nodo, variables=None):
        if variables is None:
            variables = {}
        if nodo.izq is None and nodo.der is None:
            if isinstance(nodo.valor, str):
                if nodo.valor in variables:
                    return variables[nodo.valor]
                else:
                    raise Exception(f"Error Semántico: Variable '{nodo.valor}' no definida")
            else:
                return nodo.valor
        izq = self.evaluar(nodo.izq, variables)
        der = self.evaluar(nodo.der, variables)
        if nodo.valor == '+': return izq + der
        if nodo.valor == '-': return izq - der
        if nodo.valor == '*': return izq * der
        if nodo.valor == '/':
            if der == 0:
                raise Exception("Error Semántico: División por cero")
            return izq / der
        if nodo.valor == '^': return izq ** der

# ----------------------------------------------------------------------
# GUI con visualización del AFND-ε
# ----------------------------------------------------------------------
class CompiladorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Compilador - Visualización AFND-ε Interactiva")
        self.root.geometry("1400x850")
        self.root.configure(bg="#1a1a24")
        self.afnd = None
        self.cadena_sim = ""
        self.steps = []
        self.current_step = 0
        self.posiciones_estados = {}
        self.objetos_canvas = {}
        self.estilos()
        self.layout()

    def estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1a1a24")
        style.configure("TLabelFrame", background="#1a1a24", foreground="#00ffcc", font=("Segoe UI", 11, "bold"))
        style.configure("TLabelFrame.Label", background="#1a1a24", foreground="#00ffcc")
        style.configure("TLabel", background="#1a1a24", foreground="white", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), background="#4e73df", foreground="white", padding=6)
        style.map("TButton", background=[("active", "#2e59d9")])
        style.configure("TEntry", padding=6, font=("Consolas", 12))

    def layout(self):
        # Barra superior
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=20, pady=15)
        ttk.Label(top_frame, text="Expresión:", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.entrada = ttk.Entry(top_frame, width=70)
        self.entrada.pack(side="left", padx=15)
        ttk.Button(top_frame, text="⚙ Procesar", command=self.procesar).pack(side="left")

        # Marco de tokens
        tokens_frame = ttk.LabelFrame(self.root, text=" Tokens Generados ", padding=5)
        tokens_frame.pack(fill="x", padx=20, pady=5)
        self.tokens_canvas = tk.Canvas(tokens_frame, bg="#232332", height=70, highlightthickness=0)
        scrollbar_tokens = ttk.Scrollbar(tokens_frame, orient="horizontal", command=self.tokens_canvas.xview)
        self.tokens_canvas.configure(xscrollcommand=scrollbar_tokens.set)
        scrollbar_tokens.pack(side="bottom", fill="x")
        self.tokens_canvas.pack(side="top", fill="x", expand=True)
        self.tokens_inner = tk.Frame(self.tokens_canvas, bg="#232332")
        self.tokens_canvas.create_window((0,0), window=self.tokens_inner, anchor="nw")

        # Marco del autómata
        automata_frame = ttk.LabelFrame(self.root, text=" Mapa de Autómata Finito No Determinístico con ε ", padding=5)
        automata_frame.pack(fill="both", expand=True, padx=20, pady=5)

        canvas_container = ttk.Frame(automata_frame)
        canvas_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_container, bg="#1e1e2d", highlightthickness=0)
        scroll_y = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        scroll_x = ttk.Scrollbar(canvas_container, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Barra inferior: Simulación y Resultado
        control_frame = tk.Frame(self.root, bg="#232332", bd=1, relief="ridge")
        control_frame.pack(fill="x", padx=20, pady=10)
        
        btn_frame = tk.Frame(control_frame, bg="#232332")
        btn_frame.pack(side="left", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="◀ Reiniciar", command=self.reset_simulacion).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="▶ Paso a Paso", command=self.siguiente_paso).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏵ Ejecutar Todo", command=self.ejecutar_simulacion).pack(side="left", padx=5)
        
        self.label_paso = tk.Label(btn_frame, text="Paso 0 / 0", bg="#232332", fg="#00ffcc", font=("Segoe UI", 11, "bold"))
        self.label_paso.pack(side="left", padx=20)

        # Cinta (Tape) de simulación
        self.cinta_canvas = tk.Canvas(control_frame, bg="#232332", height=50, highlightthickness=0)
        self.cinta_canvas.pack(side="left", fill="x", expand=True, padx=10)

        # Resultado final
        self.label_resultado = tk.Label(self.root, text="Resultado Final: ---", bg="#1a1a24", fg="#ffcc00", font=("Segoe UI", 16, "bold"))
        self.label_resultado.pack(pady=10)

    def mostrar_tokens(self, tokens):
        for widget in self.tokens_inner.winfo_children():
            widget.destroy()
        for tok in tokens:
            frame = tk.Frame(self.tokens_inner, bg="#232332")
            frame.pack(side="left", padx=8, pady=8)
            
            tipo_label = tk.Label(frame, text=tok.tipo, bg="#4e73df", fg="white",
                                  font=("Segoe UI", 9, "bold"), padx=6, pady=2, bd=0)
            tipo_label.pack(fill="x")
            
            valor_texto = str(tok.valor)
            if len(valor_texto) > 15: valor_texto = valor_texto[:12] + "..."
            
            valor_label = tk.Label(frame, text=valor_texto, bg="#2b2b3c", fg="white",
                                   font=("Consolas", 11), padx=6, pady=4, bd=0)
            valor_label.pack(fill="x")
        self.tokens_inner.update_idletasks()
        self.tokens_canvas.configure(scrollregion=self.tokens_canvas.bbox("all"))

    def definir_posiciones(self):
        """Distribución más balanceada y lógica del árbol de estados."""
        self.posiciones_estados = {
            0: (100, 350),   # q_start
            
            # Identificador
            1: (300, 100),  # id_inicio
            2: (550, 100),  # id_final
            
            # Número (Tiene más estados, los agrupamos bien)
            3: (300, 250),  # num_q0
            4: (450, 250),  # num_q1
            5: (600, 200),  # num_q2
            6: (750, 280),  # num_final
            
            # Operador
            7: (300, 400),  # op_inicio
            8: (550, 400),  # op_final
            
            # Paréntesis izquierdo
            9: (300, 520),  # paren_izq_inicio
            10: (550, 520), # paren_izq_final
            
            # Paréntesis derecho
            11: (300, 640), # paren_der_inicio
            12: (550, 640)  # paren_der_final
        }

    def calcular_borde(self, x1, y1, x2, y2, r):
        """Calcula el punto de intersección de la línea en el borde del círculo."""
        angulo = math.atan2(y2 - y1, x2 - x1)
        bx1 = x1 + r * math.cos(angulo)
        by1 = y1 + r * math.sin(angulo)
        bx2 = x2 - r * math.cos(angulo)
        by2 = y2 - r * math.sin(angulo)
        return bx1, by1, bx2, by2

    def abreviar_simbolos(self, simbolos):
        if 'ε' in simbolos: return 'ε'
        letras = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')
        digitos = set('0123456789')
        if simbolos.issubset(letras) and len(simbolos) > 10: return "[a-zA-Z_]"
        if simbolos.issubset(letras | digitos) and len(simbolos) > 10: return "[a-zA-Z0-9_]"
        if simbolos.issubset(digitos) and len(simbolos) > 5: return "[0-9]"
        return ",".join(sorted(list(simbolos)))

    def dibujar_automata(self):
        if not self.afnd: return
        self.canvas.delete("all")
        self.definir_posiciones()
        RADIO = 22

        # 1. Agrupar transiciones (se mantiene igual)
        transiciones_agrupadas = {}
        for (origen_id, simbolo), destinos in self.afnd.transiciones.items():
            for dest in destinos:
                clave = (origen_id, dest.id)
                if clave not in transiciones_agrupadas:
                    transiciones_agrupadas[clave] = set()
                transiciones_agrupadas[clave].add(simbolo)

        # 2. Dibujar transiciones (se mantiene igual)
        for (origen_id, destino_id), simbolos in transiciones_agrupadas.items():
            x1, y1 = self.posiciones_estados.get(origen_id, (100, 100))
            x2, y2 = self.posiciones_estados.get(destino_id, (100, 100))
            texto_simbolo = self.abreviar_simbolos(simbolos)
            
            es_epsilon = 'ε' in simbolos
            color_flecha = "#ffcc00" if es_epsilon else "#00ffcc"
            dash_pattern = (4, 4) if es_epsilon else ()

            if origen_id == destino_id:
                self.canvas.create_arc(x1-20, y1-50, x1+20, y1-15,
                                       start=0, extent=180, style=tk.ARC,
                                       outline=color_flecha, width=2, dash=dash_pattern)
                self.canvas.create_text(x1, y1-58, text=texto_simbolo, fill="white", font=("Consolas", 10, "bold"))
            else:
                bx1, by1, bx2, by2 = self.calcular_borde(x1, y1, x2, y2, RADIO)
                self.canvas.create_line(bx1, by1, bx2, by2, fill=color_flecha,
                                        arrow=tk.LAST, width=2, dash=dash_pattern)
                mx, my = (bx1+bx2)//2, (by1+by2)//2
                dy = -12 if x1 < x2 else 12
                self.canvas.create_text(mx, my+dy, text=texto_simbolo, fill="white", font=("Consolas", 10, "bold"))

        # 3. Dibujar estados (¡NUEVO DISEÑO BASADO EN EL PDF!)
        self.objetos_canvas.clear()
        for estado in self.afnd.estados:
            x, y = self.posiciones_estados.get(estado.id, (100, 100))
            color_fondo = "#2b2b3c"
            
            # Según el PDF: Finales naranjas, resto blancos
            color_borde = "#ffaa00" if estado.final else "white" 
            
            formas = [] # Guardamos todas las figuras del estado para poder colorearlas después
            
            # Flecha del Punto de Entrada (q_0)
            if estado.id == self.afnd.q_start.id:
                # Calculamos el borde superior izquierdo con trigonometría (ángulo de 135 grados)
                bx = x + RADIO * math.cos(math.radians(-135))
                by = y + RADIO * math.sin(math.radians(-135))
                # Dibujamos la flecha viniendo desde más arriba a la izquierda
                self.canvas.create_line(bx - 35, by - 35, bx, by, fill="white", arrow=tk.LAST, width=2.5)

            # Dibujo de los Círculos
            if estado.final:
                # Nodo Doble Naranja
                formas.append(self.canvas.create_oval(x-RADIO, y-RADIO, x+RADIO, y+RADIO, fill=color_fondo, outline=color_borde, width=2))
                formas.append(self.canvas.create_oval(x-(RADIO-5), y-(RADIO-5), x+(RADIO-5), y+(RADIO-5), fill=color_fondo, outline=color_borde, width=2))
            else:
                # Nodo Blanco
                formas.append(self.canvas.create_oval(x-RADIO, y-RADIO, x+RADIO, y+RADIO, fill=color_fondo, outline=color_borde, width=2))
            
            etiqueta = self.canvas.create_text(x, y, text=f"q{estado.id}", fill="white", font=("Segoe UI", 10, "bold"))
            
            # Guardamos la lista de formas en lugar de un solo círculo
            self.objetos_canvas[estado.id] = (formas, etiqueta)

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def dibujar_cinta(self, indice_activo):
        self.cinta_canvas.delete("all")
        if not self.cadena_sim: return
        x = 20
        y = 10
        ancho_celda = 35
        for i, c in enumerate(self.cadena_sim):
            color_fondo = "#4e73df" if i == indice_activo else "#2b2b3c"
            color_borde = "white" if i == indice_activo else "gray"
            self.cinta_canvas.create_rectangle(x, y, x+ancho_celda, y+35, fill=color_fondo, outline=color_borde, width=2)
            self.cinta_canvas.create_text(x + ancho_celda/2, y + 17.5, text=c, fill="white", font=("Consolas", 14, "bold"))
            x += ancho_celda + 5

    def resaltar_estados(self, conjunto_activo):
        if not self.objetos_canvas: return
        for estado in self.afnd.estados:
            if estado.id not in self.objetos_canvas: continue
            
            # Ahora desempaquetamos una lista de formas
            formas, etiqueta = self.objetos_canvas[estado.id]
            
            if estado in conjunto_activo:
                # Pintamos de azul todas las capas del estado (útil para el nodo doble)
                for f in formas:
                    self.canvas.itemconfig(f, fill="#0077b6")
                self.canvas.itemconfig(etiqueta, fill="#00ffcc")
            else:
                # Devolvemos al color de fondo normal
                for f in formas:
                    self.canvas.itemconfig(f, fill="#2b2b3c")
                self.canvas.itemconfig(etiqueta, fill="white")

    def simular_afnd(self, cadena):
        pasos = []
        pos = 0
        n = len(cadena)
        
        estados_actuales = self.afnd.clausura_epsilon({self.afnd.q_start})
        # Guardamos: (Mensaje a mostrar, estados actuales, índice en la cinta)
        pasos.append(("✨ Inicio (ε-clausura)", estados_actuales, 0))
        
        while pos < n:
            c = cadena[pos]
            siguientes = self.afnd.mover(estados_actuales, c)
            
            if not siguientes:
                # ¡Callejón sin salida! Esto significa que terminó un token.
                # Simulamos lo que hace el Lexer: reiniciar al estado inicial (q_start)
                estados_actuales = self.afnd.clausura_epsilon({self.afnd.q_start})
                pasos.append((f"🔄 Fin de token. Reiniciando para leer '{c}'...", estados_actuales, pos))
                
                # Volvemos a intentar movernos con el mismo carácter, pero desde el inicio
                siguientes = self.afnd.mover(estados_actuales, c)
                if not siguientes:
                    pasos.append((f"❌ Error: Carácter no reconocido '{c}'", set(), pos))
                    break
            
            estados_actuales = self.afnd.clausura_epsilon(siguientes)
            pasos.append((f"📥 Leyendo carácter: '{c}'", estados_actuales, pos))
            pos += 1
            
        return pasos

    def reset_simulacion(self):
        if not self.steps or not self.objetos_canvas: return
        self.current_step = 0
        self.label_paso.config(text=f"Paso 0 / {len(self.steps)-1}")
        
        accion, estados, idx_cinta = self.steps[0]
        self.resaltar_estados(estados)
        self.dibujar_cinta(-1) # Al inicio no hay nada seleccionado aún
        
        self.canvas.delete("info")
        self.canvas.create_text(100, 30, text=accion, fill="#ffcc00", font=("Segoe UI", 14, "bold"), tags="info", anchor="w")

    def siguiente_paso(self):
        if not self.steps or not self.objetos_canvas: return
        
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            accion, estados, idx_cinta = self.steps[self.current_step]
            
            self.label_paso.config(text=f"Paso {self.current_step} / {len(self.steps)-1}")
            self.resaltar_estados(estados)
            self.dibujar_cinta(idx_cinta)
            
            self.canvas.delete("info")
            # Cambiamos colores según la acción para que sea más claro visualmente
            color_texto = "#ffcc00" if "Reiniciando" in accion else ("#ff0066" if "Error" in accion else "#00ffcc")
            self.canvas.create_text(100, 30, text=accion, fill=color_texto, font=("Segoe UI", 14, "bold"), tags="info", anchor="w")
        else:
            if self.steps:
                _, estados_finales, _ = self.steps[-1]
                finales_activos = [e for e in estados_finales if e.final]
                if finales_activos:
                    messagebox.showinfo("Aceptación", "✅ Todo el análisis léxico terminó correctamente.")
                else:
                    messagebox.showerror("Error de Análisis", "❌ La cadena NO es aceptada (quedó incompleta)")

    def ejecutar_simulacion(self):
        if not self.steps or not self.objetos_canvas:
            messagebox.showinfo("Simulación", "Primero procese una expresión.")
            return
        self.reset_simulacion()
        def avanzar():
            if self.current_step < len(self.steps) - 1:
                self.siguiente_paso()
                self.root.after(800, avanzar) # 800ms por paso
        self.root.after(800, avanzar)

    def procesar(self):
        try:
            entrada_completa = self.entrada.get().strip()
            if not entrada_completa:
                raise Exception("Ingrese una expresión")
            
            self.label_resultado.config(text="Resultado Final: Evaluando...", fg="white")
            
            if ';' in entrada_completa:
                parte_vars, expr = entrada_completa.split(';', 1)
                parte_vars = parte_vars.strip()
                expr = expr.strip()
                variables = {}
                if parte_vars:
                    for asign in parte_vars.split(','):
                        if '=' not in asign: raise Exception("Formato inválido en definición de variable")
                        nombre, valor_str = asign.split('=', 1)
                        variables[nombre.strip()] = float(valor_str.strip())
            else:
                expr = entrada_completa
                variables = {}

            # Lexer y Post-procesamiento
            lexer = Lexer(expr)
            tokens_originales = lexer.analizar()
            tokens_unarios = combinar_menos_unario(tokens_originales)
            tokens_con_implicita = insertar_multiplicacion_implicita(tokens_unarios)
            self.mostrar_tokens(tokens_con_implicita)

            # Preparar Simulación AFND
            self.afnd = lexer.afnd
            self.cadena_sim = ''.join(c for c in expr if not c.isspace())
            self.steps = self.simular_afnd(self.cadena_sim)

            self.dibujar_automata()
            self.reset_simulacion()

            # Parser y Evaluación
            parser = Parser(tokens_con_implicita)
            arbol = parser.construir()
            evaluador = Evaluador()
            resultado = evaluador.evaluar(arbol, variables)
            self.label_resultado.config(text=f"Resultado Final: {resultado}", fg="#00ffcc")

        except Exception as e:
            print("=== ERROR DETECTADO ===")
            traceback.print_exc()
            self.label_resultado.config(text="Resultado Final: ERROR", fg="#ff0066")
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = CompiladorApp(root)
    root.mainloop()
import tkinter as tk
from tkinter import ttk, messagebox

class Token:
    def __init__(self, tipo, valor):
        self.tipo = tipo
        self.valor = valor

    def __repr__(self):
        return f"{self.tipo}({self.valor})"

class Lexer:
    def __init__(self, texto):
        self.texto = texto
        self.pos = 0
        self.tokens = []

    def analizar(self):
        numero = ""
        while self.pos < len(self.texto):
            c = self.texto[self.pos]
            # Identificador (letras, números, guión bajo)
            if c.isalpha() or c == '_':
                ident = ""
                while self.pos < len(self.texto) and (self.texto[self.pos].isalpha() or self.texto[self.pos].isdigit() or self.texto[self.pos] == '_'):
                    ident += self.texto[self.pos]
                    self.pos += 1
                self.tokens.append(Token("IDENTIFICADOR", ident))
                continue
            # Número (incluye punto y guión para negativos)
            elif c.isdigit() or c == '.' or (c == '-' and not numero and (not self.tokens or self.tokens[-1].tipo in ["OPERADOR", "PAREN_IZQ"])):
                numero += c
            else:
                if numero:
                    if numero == "-":
                        self.tokens.append(Token("NUMERO", -1.0))
                        self.tokens.append(Token("OPERADOR", "*"))
                    else:
                        self.tokens.append(Token("NUMERO", float(numero)))
                    numero = ""
                if c in "+-*/^":
                    self.tokens.append(Token("OPERADOR", c))
                elif c == "(":
                    self.tokens.append(Token("PAREN_IZQ", c))
                elif c == ")":
                    self.tokens.append(Token("PAREN_DER", c))
                elif c.isspace():
                    pass
                else:
                    raise Exception(f"Error Léxico: Carácter no reconocido '{c}'")
            self.pos += 1
        if numero:
            if numero == "-":
                raise Exception("Error Léxico: Expresión incompleta")
            self.tokens.append(Token("NUMERO", float(numero)))
        return self.tokens

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
            raise Exception("Error Sintáctico: Faltan operandos u operadores (Expresión mal formada)")
        op = self.ops.pop()
        der = self.valores.pop()
        izq = self.valores.pop()
        self.valores.append(Nodo(op, izq, der))

    def construir(self):
        if not self.tokens:
            raise Exception("Error Sintáctico: La expresión está vacía")
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
                raise Exception("Error Semántico: No se puede dividir por cero")
            return izq / der
        if nodo.valor == '^': return izq ** der

class CompiladorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Compilador Profesional")
        self.root.geometry("1200x700")
        self.root.configure(bg="#1e1e2f")
        self.arbol = None
        self.resultado = None
        self.estilos()
        self.layout()

    def estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e2f")
        style.configure("TLabel", background="#1e1e2f",
                        foreground="white", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TEntry", padding=6)

    def layout(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=20, pady=10)
        ttk.Label(top_frame, text="Ingrese la expresión (variables: nombre=valor separados por coma; expresión):").pack(side="left")
        self.entrada = ttk.Entry(top_frame, width=60)
        self.entrada.pack(side="left", padx=10)
        ttk.Button(top_frame, text="Procesar", command=self.procesar).pack(side="left")

        tokens_frame = ttk.LabelFrame(self.root, text="Tokens generados", padding=5)
        tokens_frame.pack(fill="x", padx=20, pady=5)
        self.tokens_canvas = tk.Canvas(tokens_frame, bg="#2b2b3c", height=80, highlightthickness=0)
        scrollbar_tokens = ttk.Scrollbar(tokens_frame, orient="horizontal", command=self.tokens_canvas.xview)
        self.tokens_canvas.configure(xscrollcommand=scrollbar_tokens.set)
        scrollbar_tokens.pack(side="bottom", fill="x")
        self.tokens_canvas.pack(side="top", fill="x", expand=True)
        self.tokens_inner = ttk.Frame(self.tokens_canvas)
        self.tokens_canvas.create_window((0,0), window=self.tokens_inner, anchor="nw")

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(canvas_frame, bg="#2b2b3c", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        scrollbar_x = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=20, pady=10)
        self.label_resultado = ttk.Label(bottom_frame, text="Resultado: ---")
        self.label_resultado.pack()

    def mostrar_tokens(self, tokens):
        for widget in self.tokens_inner.winfo_children():
            widget.destroy()
        for i, tok in enumerate(tokens):
            frame = tk.Frame(self.tokens_inner, bg="#2b2b3c", bd=1, relief="solid")
            frame.pack(side="left", padx=3, pady=3)
            tipo_label = tk.Label(frame, text=tok.tipo, bg="#4e73df", fg="white",
                                  font=("Segoe UI", 9, "bold"), padx=5, pady=2)
            tipo_label.pack(fill="x")
            valor_texto = str(tok.valor)
            if len(valor_texto) > 15:
                valor_texto = valor_texto[:12] + "..."
            valor_label = tk.Label(frame, text=valor_texto, bg="#1e1e2f", fg="white",
                                   font=("Segoe UI", 10), padx=5, pady=2)
            valor_label.pack(fill="x")
        self.tokens_inner.update_idletasks()
        self.tokens_canvas.configure(scrollregion=self.tokens_canvas.bbox("all"))

    def procesar(self):
        try:
            entrada_completa = self.entrada.get().strip()
            if not entrada_completa:
                raise Exception("Ingrese una expresión")
            # Separar variables y expresión
            if ';' in entrada_completa:
                parte_vars, expr = entrada_completa.split(';', 1)
                parte_vars = parte_vars.strip()
                expr = expr.strip()
                variables = {}
                if parte_vars:
                    for asign in parte_vars.split(','):
                        if '=' not in asign:
                            raise Exception("Formato inválido en definición de variable")
                        nombre, valor_str = asign.split('=', 1)
                        nombre = nombre.strip()
                        valor_str = valor_str.strip()
                        try:
                            variables[nombre] = float(valor_str)
                        except:
                            raise Exception(f"Valor de '{nombre}' no es numérico")
            else:
                expr = entrada_completa
                variables = {}
            # Análisis léxico y sintáctico sobre la expresión
            lexer = Lexer(expr)
            tokens_originales = lexer.analizar()
            tokens_con_implicita = insertar_multiplicacion_implicita(tokens_originales)
            self.mostrar_tokens(tokens_con_implicita)
            parser = Parser(tokens_con_implicita)
            self.arbol = parser.construir()
            evaluador = Evaluador()
            self.resultado = evaluador.evaluar(self.arbol, variables)
            self.label_resultado.config(text=f"Resultado: {self.resultado}")
            self.mostrar_arbol()
        except Exception as e:
            messagebox.showerror("Error en la Compilación", str(e))

    def mostrar_arbol(self):
        self.canvas.delete("all")
        if not self.arbol:
            return
        posiciones = {}
        self.calcular_posiciones(self.arbol, 0, 0, posiciones)
        min_x = min(x for x, y in posiciones.values())
        max_x = max(x for x, y in posiciones.values())
        max_y = max(y for x, y in posiciones.values())
        offset_x = 100 - min_x
        offset_y = 80
        for nodo, (x, y) in posiciones.items():
            posiciones[nodo] = (x + offset_x, y + offset_y)
        for nodo in posiciones:
            x, y = posiciones[nodo]
            if nodo.izq:
                x2, y2 = posiciones[nodo.izq]
                self.canvas.create_line(x, y, x2, y2, fill="white")
            if nodo.der:
                x2, y2 = posiciones[nodo.der]
                self.canvas.create_line(x, y, x2, y2, fill="white")
        for nodo in posiciones:
            x, y = posiciones[nodo]
            r = 25
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="#4e73df", outline="white")
            self.canvas.create_text(x, y, text=str(nodo.valor), fill="white", font=("Segoe UI", 11, "bold"))
        self.canvas.config(scrollregion=(0, 0, max_x - min_x + 300, max_y + 200))

    def calcular_posiciones(self, nodo, profundidad, x_actual, posiciones):
        if nodo is None:
            return 0
        espacio_h = 120
        espacio_v = 120
        ancho_izq = self.calcular_posiciones(nodo.izq, profundidad+1, x_actual, posiciones)
        if ancho_izq == 0:
            ancho_izq = 1
        ancho_der = self.calcular_posiciones(nodo.der, profundidad+1, x_actual + ancho_izq * espacio_h, posiciones)
        if ancho_der == 0:
            ancho_der = 1
        total = ancho_izq + ancho_der
        x_nodo = x_actual + (ancho_izq * espacio_h) / 2
        y_nodo = profundidad * espacio_v
        posiciones[nodo] = (x_nodo, y_nodo)
        return total

if __name__ == "__main__":
    root = tk.Tk()
    app = CompiladorApp(root)
    root.mainloop()

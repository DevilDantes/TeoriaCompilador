import streamlit as st
import re
import pandas as pd
import time


st.set_page_config(page_title="Compiladores | Dashboard", layout="wide", initial_sidebar_state="collapsed")

if 'step' not in st.session_state: st.session_state.step = 0
if 'playing' not in st.session_state: st.session_state.playing = False
if 'historial' not in st.session_state: st.session_state.historial = None
if 'instrucciones' not in st.session_state: st.session_state.instrucciones = None
if 'tokens' not in st.session_state: st.session_state.tokens = None

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Configuración general */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #fdfdfd;
    }
    
    /* Contenedores tipo Dashboard */
    .dashboard-card {
        background-color: #ffffff;
        border: 1px solid #eaedf1;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02), 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }
    
    .card-header {
        font-size: 0.95rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 16px;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 10px;
    }

    /* Editor y Consola */
    .stTextArea textarea {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 14px !important;
        background-color: #f8fafc !important;
        color: #1e293b !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        line-height: 1.5 !important;
    }
    
    .console-box {
        background-color: #0f172a;
        color: #38bdf8;
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        padding: 16px;
        border-radius: 8px;
        min-height: 120px;
        white-space: pre-wrap;
    }

    /* Pila Estilo Jenga Minimalista Avanzada */
    .jenga-stack {
        display: flex;
        flex-direction: column-reverse;
        align-items: center;
        justify-content: flex-start;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        min-height: 340px;
    }
    
    .jenga-layer {
        width: 85%;
        height: 38px;
        background: linear-gradient(135deg, #e7a977 0%, #c98a53 100%);
        border: 1px solid #a76a36;
        border-radius: 4px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 14px;
        color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        animation: pushAnim 0.2s ease-out;
    }
    
    @keyframes pushAnim {
        from { transform: scale(0.8); opacity: 0; }
        to { transform: scale(1); opacity: 1; }
    }

    /* Tokens */
    .token-pill {
        display: inline-block;
        background-color: #f1f5f9;
        color: #334155;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 6px;
        margin: 4px;
        border: 1px solid #e2e8f0;
    }
    .token-pill b {
        color: #0284c7;
    }
    
    /* Texto resaltado de instrucción actual */
    .current-instruction {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 10px 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
        color: #1d4ed8;
        font-weight: 600;
        border-radius: 0 6px 6px 0;
        margin-bottom: 16px;
    }

    /* CSS exclusivo para el historial visual de Jengas (Miniaturas) */
    .history-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        justify-content: flex-start;
        margin-top: 10px;
        padding-bottom: 10px;
    }
    .history-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px;
        width: 130px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .history-title {
        font-size: 11px;
        font-family: 'JetBrains Mono', monospace;
        color: #0f172a;
        font-weight: 600;
        margin-bottom: 10px;
        text-align: center;
        height: 32px;
        line-height: 1.2;
    }
    .history-title span {
        color: #3b82f6;
        font-size: 10px;
    }
    .jenga-stack-mini {
        display: flex;
        flex-direction: column-reverse;
        align-items: center;
        justify-content: flex-start;
        background: #f8fafc;
        border: 1px dashed #cbd5e1;
        border-radius: 4px;
        padding: 8px 4px;
        width: 100%;
        height: 140px;
        overflow-y: auto;
    }
    .jenga-layer-mini {
        width: 90%;
        height: 22px;
        min-height: 22px;
        background: linear-gradient(135deg, #e7a977 0%, #c98a53 100%);
        border: 1px solid #a76a36;
        border-radius: 3px;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 11px;
        color: #ffffff;
        box-shadow: 0 2px 3px -1px rgba(0, 0, 0, 0.1);
    }
    .empty-stack-mini {
        color: #94a3b8;
        font-size: 11px;
        margin: auto;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

class Compilador:
    def __init__(self, codigo):
        self.codigo = codigo
        self.tokens = []
        self.pos = 0
        self.instrucciones = []
        self.errores = []
        self.label_cont = 0

    def nuevo_label(self):
        self.label_cont += 1
        return f"L{self.label_cont}"

    def lexer(self):
        patrones = [
            ('IF', r'\bIF\b'),
            ('WHILE', r'\bWHILE\b'),
            ('PRINT', r'\bPRINT\b'),
            ('COMP', r'==|!=|<=|>=|<|>'),
            ('ASSIGN', r'='),
            ('ID', r'[a-zA-Z_]\w*'),
            ('NUM', r'\d+(\.\d+)?'),
            ('OP_SUMA', r'[+-]'),
            ('OP_MULT', r'[*/]'),
            ('PAREN_IZQ', r'\('),
            ('PAREN_DER', r'\)'),
            ('LLAVE_IZQ', r'\{'),
            ('LLAVE_DER', r'\}'),
            ('SALTO', r'\n+'),
            ('ESPACIO', r'[ \t]+'),
            ('ERROR', r'.')
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in patrones)
        for mo in re.finditer(tok_regex, self.codigo):
            tipo = mo.lastgroup
            valor = mo.group()
            if tipo == 'ESPACIO': continue
            elif tipo == 'ERROR': self.errores.append(f"Error Léxico: Carácter '{valor}' no permitido.")
            else: self.tokens.append((tipo, valor))

    def token_actual(self):
        if self.pos < len(self.tokens): return self.tokens[self.pos]
        return None

    def coincidir(self, tipo_esperado):
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == tipo_esperado:
            self.pos += 1
            return True
        return False

    def analizar(self):
        self.lexer()
        if self.errores: return False
        try:
            self.parse_stmts()
        except Exception as e:
            self.errores.append(str(e))
        return len(self.errores) == 0

    def parse_stmts(self):
        while self.pos < len(self.tokens):
            tok = self.token_actual()
            if not tok or tok[0] == 'LLAVE_DER': break
            if tok[0] == 'SALTO':
                self.pos += 1
                continue
            self.parse_stmt()

    def parse_stmt(self):
        tok = self.token_actual()
        if tok[0] == 'ID':
            var_name = tok[1]
            self.pos += 1
            if self.coincidir('ASSIGN'):
                self.parse_expr()
                self.instrucciones.append(f"STORE {var_name}")
            else:
                raise Exception(f"Sintaxis: Se esperaba '=' después de '{var_name}'")
        elif tok[0] == 'PRINT':
            self.pos += 1
            self.parse_expr()
            self.instrucciones.append("PRINT")
        elif tok[0] == 'IF':
            self.pos += 1
            self.parse_cond()
            if not self.coincidir('LLAVE_IZQ'): raise Exception("Sintaxis: Falta '{' tras condición del IF")
            l_end = self.nuevo_label()
            self.instrucciones.append(f"JMPF {l_end}")
            self.parse_stmts()
            if not self.coincidir('LLAVE_DER'): raise Exception("Sintaxis: Falta '}' para cerrar el bloque IF")
            self.instrucciones.append(f"LABEL {l_end}")
        elif tok[0] == 'WHILE':
            self.pos += 1
            l_start = self.nuevo_label()
            l_end = self.nuevo_label()
            self.instrucciones.append(f"LABEL {l_start}")
            self.parse_cond()
            self.instrucciones.append(f"JMPF {l_end}")
            if not self.coincidir('LLAVE_IZQ'): raise Exception("Sintaxis: Falta '{' tras condición del WHILE")
            self.parse_stmts()
            if not self.coincidir('LLAVE_DER'): raise Exception("Sintaxis: Falta '}' para cerrar el bloque WHILE")
            self.instrucciones.append(f"JMP {l_start}")
            self.instrucciones.append(f"LABEL {l_end}")
        else:
            raise Exception(f"Sintaxis: Instrucción no válida '{tok[1]}'")

    def parse_cond(self):
        self.parse_expr()
        tok = self.token_actual()
        if tok and tok[0] == 'COMP':
            op = tok[1]
            self.pos += 1
            self.parse_expr()
            
            if op == '==': self.instrucciones.append("EQ")
            elif op == '!=': self.instrucciones.append("NEQ")
            elif op == '<': self.instrucciones.append("LT")
            elif op == '>': self.instrucciones.append("GT")
            elif op == '<=': self.instrucciones.append("LE")
            elif op == '>=': self.instrucciones.append("GE")
        else:
            raise Exception("Sintaxis: Se esperaba un operador lógico (==, !=, <, >, <=, >=)")

    def parse_expr(self):
        self.parse_termino()
        while self.token_actual() and self.token_actual()[0] == 'OP_SUMA':
            op = self.token_actual()[1]
            self.pos += 1
            self.parse_termino()
            self.instrucciones.append("ADD" if op == '+' else "SUB")

    def parse_termino(self):
        self.parse_factor()
        while self.token_actual() and self.token_actual()[0] == 'OP_MULT':
            op = self.token_actual()[1]
            self.pos += 1
            self.parse_factor()
            self.instrucciones.append("MUL" if op == '*' else "DIV")

    def parse_factor(self):
        tok = self.token_actual()
        if not tok: raise Exception("Expresión incompleta")
        if tok[0] == 'NUM':
            self.instrucciones.append(f"PUSH {tok[1]}")
            self.pos += 1
        elif tok[0] == 'ID':
            self.instrucciones.append(f"LOAD {tok[1]}")
            self.pos += 1
        elif tok[0] == 'PAREN_IZQ':
            self.pos += 1
            self.parse_expr()
            if not self.coincidir('PAREN_DER'): raise Exception("Sintaxis: Falta paréntesis de cierre ')'")
        else:
            raise Exception(f"Se esperaba una variable o número, se encontró '{tok[1]}'")



class MaquinaVirtual:
    def __init__(self):
        self.pila = []
        self.memoria = {}
        self.consola = []
        self.historial = []

    def ejecutar(self, instrucciones):
        labels = {}
        codigo_limpio = []
        for instr in instrucciones:
            if instr.startswith("LABEL"):
                labels[instr.split()[1]] = len(codigo_limpio)
            else:
                codigo_limpio.append(instr)

        pc = 0
        self._guardar_estado("INICIO", pc)
        pasos = 0

        while pc < len(codigo_limpio) and pasos < 1000:
            instr = codigo_limpio[pc]
            partes = instr.split()
            cmd = partes[0]
            try:
                if cmd == "PUSH": self.pila.append(float(partes[1]))
                elif cmd == "LOAD":
                    var = partes[1]
                    if var not in self.memoria: raise Exception(f"Variable '{var}' no definida")
                    self.pila.append(self.memoria[var])
                elif cmd == "STORE": self.memoria[partes[1]] = self.pila.pop()
                elif cmd == "ADD": b, a = self.pila.pop(), self.pila.pop(); self.pila.append(a + b)
                elif cmd == "SUB": b, a = self.pila.pop(), self.pila.pop(); self.pila.append(a - b)
                elif cmd == "MUL": b, a = self.pila.pop(), self.pila.pop(); self.pila.append(a * b)
                elif cmd == "DIV":
                    b, a = self.pila.pop(), self.pila.pop()
                    if b == 0: raise Exception("División por cero")
                    self.pila.append(a / b)
                
                elif cmd == "EQ": b, a = self.pila.pop(), self.pila.pop(); self.pila.append(1.0 if a == b else 0.0)
                elif cmd == "NEQ": b, a = self.pila.pop(), self.pila.pop(); self.pila.append(1.0 if a != b else 0.0)
                elif cmd == "LT": b, a = self.pila.pop(), self.pila.pop(); self.pila.append(1.0 if a < b else 0.0)
                elif cmd == "GT": b, a = self.pila.pop(), self.pila.pop(); self.pila.append(1.0 if a > b else 0.0)
                elif cmd == "LE": b, a = self.pila.pop(), self.pila.pop(); self.pila.append(1.0 if a <= b else 0.0)
                elif cmd == "GE": b, a = self.pila.pop(), self.pila.pop(); self.pila.append(1.0 if a >= b else 0.0)
                
                elif cmd == "PRINT":
                    val = self.pila.pop()
                    self.consola.append(str(int(val) if val.is_integer() else round(val, 2)))
                elif cmd == "JMPF":
                    if self.pila.pop() == 0.0:
                        pc = labels[partes[1]]
                        self._guardar_estado(instr, pc)
                        continue
                elif cmd == "JMP":
                    pc = labels[partes[1]]
                    self._guardar_estado(instr, pc)
                    continue

                pc += 1
                self._guardar_estado(instr, pc)
                pasos += 1
            except Exception as e:
                self._guardar_estado(f"ERROR SEMÁNTICO: {str(e)}", pc)
                break

    def _guardar_estado(self, instr, pc):
        self.historial.append({
            'instruccion': instr,
            'pila': list(self.pila),
            'memoria': dict(self.memoria),
            'consola': list(self.consola)
        })


st.markdown("<h3 style='color:#1e293b; font-weight:700; margin-bottom:4px;'>IDE de Arquitectura Basada en Pila</h3>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748b; font-size:14px;'>Laboratorio Avanzado de Compiladores — Control de Flujo Dinámico</p>", unsafe_allow_html=True)

col_izq, col_der = st.columns([1.1, 1])

with col_izq:
    st.markdown("<div class='dashboard-card'><div class='card-header'>Código Fuente</div>", unsafe_allow_html=True)
    codigo_default = """limite = 3\ncontador = 1\n\nWHILE contador <= limite {\n    PRINT contador\n    contador = contador + 1\n}\n\nvalor = 10\n\nIF valor >= 10 {\n    PRINT 999\n}\n\nIF valor != 5 {\n    PRINT 888\n}"""
    codigo_usuario = st.text_area("Editor", value=codigo_default, height=220, label_visibility="collapsed")
    
    if st.button("Ensamblar y Ejecutar", type="primary", width="stretch"):
        compilador = Compilador(codigo_usuario)
        if compilador.analizar():
            vm = MaquinaVirtual()
            vm.ejecutar(compilador.instrucciones)
            
            st.session_state['tokens'] = compilador.tokens
            st.session_state['instrucciones'] = compilador.instrucciones
            st.session_state['historial'] = vm.historial
            
            st.session_state.step = 0
            st.session_state.playing = True
            st.rerun()
        else:
            st.session_state['historial'] = None
            st.error("Error de compilación detectado:")
            for error in compilador.errores:
                st.caption(f"• {error}")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state['tokens']:
        st.markdown("<div class='dashboard-card'><div class='card-header'>Tabla de Tokens Analizados</div>", unsafe_allow_html=True)
        html_tokens = ""
        for tipo, valor in st.session_state['tokens']:
            if tipo != "SALTO":
                html_tokens += f"<span class='token-pill'><b>{tipo}</b>: {valor}</span>"
        st.markdown(html_tokens, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with col_der:
    if st.session_state['historial']:
        historial = st.session_state['historial']
        total_steps = len(historial) - 1
        
        if st.session_state.step > total_steps:
            st.session_state.step = total_steps

        estado_actual = historial[st.session_state.step]

        st.markdown("<div class='dashboard-card'><div class='card-header'>Monitor del Intérprete</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='current-instruction'>Instrucción: {estado_actual['instruccion']}</div>", unsafe_allow_html=True)
        
        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)
        
        with ctrl_col1:
            if st.button("Reiniciar", width="stretch"):
                st.session_state.step = 0
                st.session_state.playing = False
                st.rerun()
                
        with ctrl_col2:
            label_play = "Pausar" if st.session_state.playing else "Reproducir"
            if st.button(label_play, width="stretch"):
                st.session_state.playing = not st.session_state.playing
                st.rerun()
                
        with ctrl_col3:
            if st.button("Paso Sig.", width="stretch"):
                st.session_state.playing = False
                if st.session_state.step < total_steps:
                    st.session_state.step += 1
                    st.rerun()
                    
        with ctrl_col4:
            if st.button("Detener", width="stretch"):
                st.session_state.playing = False
                st.session_state.step = total_steps
                st.rerun()

        st.progress((st.session_state.step) / max(total_steps, 1))
        st.caption(f"Progreso de ejecución: Paso {st.session_state.step} de {total_steps}")

        sub_col1, sub_col2 = st.columns([1, 1.1])
        
        with sub_col1:
            st.markdown("<p style='font-size:13px; font-weight:600; color:#475569; margin-bottom:8px;'>Estructura Pila (Jenga)</p>", unsafe_allow_html=True)
            pila_html = "<div class='jenga-stack'>"
            if not estado_actual['pila']:
                pila_html += "<span style='color:#94a3b8; font-size:13px; margin:auto;'>Pila Vacía</span>"
            else:
                for elemento in estado_actual['pila']:
                    formato_val = int(elemento) if elemento.is_integer() else round(elemento, 2)
                    pila_html += f"<div class='jenga-layer'>{formato_val}</div>"
            pila_html += "</div>"
            st.markdown(pila_html, unsafe_allow_html=True)
            
        with sub_col2:
            st.markdown("<p style='font-size:13px; font-weight:600; color:#475569; margin-bottom:8px;'>Memoria RAM Interna</p>", unsafe_allow_html=True)
            if not estado_actual['memoria']:
                st.markdown("<div style='color:#94a3b8; font-size:13px; padding-top:10px;'>Null (Vacía)</div>", unsafe_allow_html=True)
            else:
                df_ram = pd.DataFrame(list(estado_actual['memoria'].items()), columns=["Variable", "Valor"])
                st.dataframe(df_ram, width="stretch", hide_index=True)

        st.markdown("<p style='font-size:13px; font-weight:600; color:#475569; margin-bottom:8px; margin-top:14px;'>Consola del Sistema</p>", unsafe_allow_html=True)
        texto_consola = "\n".join(estado_actual['consola']) if estado_actual['consola'] else "Procesando flujo..."
        st.markdown(f"<div class='console-box'>{texto_consola}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Inspeccionar Código de Tres Direcciones Generado"):
            st.code("\n".join(st.session_state['instrucciones']), language="text")

        with st.expander("Ver Historial Completo de la Pila (Visualización Jenga)"):
            st.markdown("<p style='font-size:13px; color:#475569;'>Registro visual de la torre Jenga tras cada instrucción de la simulación:</p>", unsafe_allow_html=True)
            
            html_grid = "<div class='history-grid'>"
            for idx, est in enumerate(historial):
                html_grid += f"<div class='history-card'><div class='history-title'><span>Paso {idx}</span><br>{est['instruccion']}</div><div class='jenga-stack-mini'>"
                if not est['pila']:
                    html_grid += "<span class='empty-stack-mini'>Vacía</span>"
                else:
                    for elemento in est['pila']:
                        formato_val = int(elemento) if isinstance(elemento, float) and elemento.is_integer() else round(elemento, 2)
                        html_grid += f"<div class='jenga-layer-mini'>{formato_val}</div>"
                html_grid += "</div></div>"
                
            html_grid += "</div>"
            st.markdown(html_grid, unsafe_allow_html=True)

if st.session_state.playing and st.session_state.historial:
    if st.session_state.step < len(st.session_state.historial) - 1:
        time.sleep(0.4) 
        st.session_state.step += 1
        st.rerun()
    else:
        st.session_state.playing = False
        st.rerun()

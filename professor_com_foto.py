#!/usr/bin/env python3
"""
ProfessorHerePlease - Servidor com Exibição de Fotos dos Alunos
"""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import threading
import os
import base64
from datetime import datetime
import time
from collections import deque
import subprocess
import io

# Tentar importar PIL
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL não disponível. Instale: sudo apt install python3-pil python3-pil.imagetk")

class ProfessorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sim_Pois_Não - Professor com Fotos")
        self.root.geometry("750x700")
        self.root.configure(bg="#f0f0f0")
        
        self.pedidos = []
        self.running = True
        self.ip = self.get_ip()
        
        # Configurações de voz
        self.fila_voz = deque()
        self.timer_agrupamento = None
        self.TEMPO_AGRUPAMENTO = 800
        self.velocidade_voz = 150
        
        self.setup_ui()
        self.start_server()
        self.root.protocol("WM_DELETE_WINDOW", self.fechar)
        self.bind_scroll()
    
    def bind_scroll(self):
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind("<MouseWheel>", on_mousewheel)
    
    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def speak(self, texto):
        try:
            subprocess.Popen(["espeak", "-v", "pt", "-s", str(self.velocidade_voz), texto],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            print(f"[VOZ] {texto}")
    
    def agrupar_e_falar(self):
        if self.timer_agrupamento:
            self.timer_agrupamento.cancel()
        
        def falar():
            if not self.fila_voz:
                return
            
            nomes = list(dict.fromkeys(self.fila_voz))
            self.fila_voz.clear()
            
            if len(nomes) == 1:
                frase = f"Professor, o {nomes[0]} quer ajuda!"
            elif len(nomes) == 2:
                frase = f"Professor, o {nomes[0]} e o {nomes[1]} querem sua ajuda!"
            else:
                ultimo = nomes[-1]
                primeiros = nomes[:-1]
                frase = "Professor, os alunos "
                for nome in primeiros:
                    frase += f"{nome}, "
                frase += f"e o {ultimo} querem sua ajuda!"
            
            self.status.config(text=f"🔊 {frase[:60]}...", bg="#FF9800")
            self.speak(frase)
            self.root.after(3000, lambda: self.status.config(
                text=f"✅ Servidor ativo - {len(self.pedidos)} pedido(s)", bg="#4CAF50"))
        
        self.timer_agrupamento = threading.Timer(self.TEMPO_AGRUPAMENTO / 1000, falar)
        self.timer_agrupamento.start()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#2196F3", height=160)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="👨‍🏫 Sim_Pois_Não - Professor", font=("Arial", 16, "bold"),
                bg="#2196F3", fg="white").pack(pady=5)
        
        ip_frame = tk.Frame(header, bg="#2196F3")
        ip_frame.pack(pady=5)
        
        tk.Label(ip_frame, text="📡 IP:", font=("Arial", 11),
                bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        
        ip_label = tk.Label(ip_frame, text=self.ip, font=("Arial", 13, "bold"),
                           bg="#2196F3", fg="#FFD700")
        ip_label.pack(side=tk.LEFT, padx=5)
        
        tk.Label(ip_frame, text="🔌 Porta: 8080", font=("Arial", 11),
                bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=10)
        
        # Velocidade da voz
        voz_frame = tk.Frame(header, bg="#2196F3")
        voz_frame.pack(pady=5)
        
        tk.Label(voz_frame, text="Velocidade da Voz:", bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        
        self.velocidade_var = tk.IntVar(value=self.velocidade_voz)
        velocidade_scale = tk.Scale(voz_frame, from_=80, to=300, orient=tk.HORIZONTAL,
                                    variable=self.velocidade_var, length=120,
                                    bg="#2196F3", fg="white", highlightthickness=0)
        velocidade_scale.pack(side=tk.LEFT, padx=5)
        
        def atualizar_velocidade(val):
            self.velocidade_voz = int(val)
        velocidade_scale.config(command=atualizar_velocidade)
        
        tk.Label(voz_frame, text="wpm", bg="#2196F3", fg="white").pack(side=tk.LEFT)
        
        tk.Button(voz_frame, text="🔊 Testar", command=self.testar_voz,
                 bg="#FFD700", fg="#333").pack(side=tk.LEFT, padx=10)
        
        # Status
        self.status = tk.Label(self.root, text="✅ Servidor ativo - Aguardando alunos",
                              bg="#4CAF50", fg="white", font=("Arial", 10))
        self.status.pack(fill=tk.X)
        
        # Contador
        self.counter = tk.Label(self.root, text="📊 0 pedidos pendentes",
                               bg="#f0f0f0", fg="#666", font=("Arial", 9))
        self.counter.pack(pady=5)
        
        # Lista com scroll
        lista_frame = tk.Frame(self.root, bg="#f0f0f0")
        lista_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(lista_frame, bg="#f0f0f0", highlightthickness=0)
        scrollbar = tk.Scrollbar(lista_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f0f0f0")
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botões
        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(btn_frame, text="🗑️ Limpar Todos", command=self.limpar_todos,
                 bg="#FF5722", fg="white", font=("Arial", 10), padx=20).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="📋 Instruções", command=self.instrucoes,
                 bg="#2196F3", fg="white", font=("Arial", 10), padx=20).pack(side=tk.LEFT, padx=5)
        
        self.atualizar_lista()
    
    def testar_voz(self):
        self.speak("Teste de voz do Professor Here Please")
        self.status.config(text="🔊 Teste executado!", bg="#FF9800")
        self.root.after(2000, lambda: self.status.config(
            text=f"✅ Servidor ativo - {len(self.pedidos)} pedido(s)", bg="#4CAF50"))
    
    def start_server(self):
        def server_thread():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', 8080))
            print(f"✅ Servidor UDP rodando na porta 8080")
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(65536)  # Aumentar buffer para fotos
                    msg = json.loads(data.decode())
                    
                    if msg.get('type') == 'help':
                        student_name = msg.get('student', 'Aluno')
                        timestamp = msg.get('time', datetime.now().isoformat())
                        user_photo = msg.get('user_photo', None)
                        photo_source = msg.get('photo_source', 'desconhecido')
                        
                        self.root.after(0, lambda n=student_name: self.adicionar_fila_voz(n))
                        self.root.after(0, lambda: self.adicionar_pedido(
                            student_name, timestamp, addr[0], user_photo, photo_source
                        ))
                        
                except Exception as e:
                    print(f"Erro: {e}")
            sock.close()
        
        threading.Thread(target=server_thread, daemon=True).start()
    
    def adicionar_fila_voz(self, nome):
        self.fila_voz.append(nome)
        self.agrupar_e_falar()
    
    def adicionar_pedido(self, student, timestamp, ip, user_photo, photo_source):
        # Processar foto
        foto_img = None
        if user_photo and PIL_AVAILABLE:
            try:
                foto_bytes = base64.b64decode(user_photo)
                img = Image.open(io.BytesIO(foto_bytes))
                img.thumbnail((60, 60), Image.Resampling.LANCZOS)
                foto_img = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Erro ao carregar foto: {e}")
        
        self.pedidos.insert(0, {
            'student': student,
            'time': datetime.fromisoformat(timestamp),
            'ip': ip,
            'foto': foto_img,
            'foto_source': photo_source
        })
        self.atualizar_lista()
        self.mostrar_notificacao(student, photo_source)
    
    def mostrar_notificacao(self, student, photo_source):
        popup = tk.Toplevel(self.root)
        popup.title("Novo Pedido de Ajuda!")
        popup.geometry("350x180")
        popup.configure(bg="#FF9800")
        
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (350 // 2)
        y = (popup.winfo_screenheight() // 2) - (180 // 2)
        popup.geometry(f"+{x}+{y}")
        
        tk.Label(popup, text="🙋 NOVO PEDIDO!", font=("Arial", 14, "bold"),
                bg="#FF9800", fg="white").pack(pady=10)
        
        tk.Label(popup, text=f"Aluno: {student}", font=("Arial", 16, "bold"),
                bg="#FF9800", fg="white").pack(pady=5)
        
        tk.Label(popup, text=f"Foto: {photo_source}", font=("Arial", 9),
                bg="#FF9800", fg="white").pack()
        
        tk.Button(popup, text="✅ OK", command=popup.destroy,
                 bg="#4CAF50", fg="white", font=("Arial", 11), padx=30).pack(pady=10)
        
        self.root.after(5000, lambda: popup.destroy() if popup.winfo_exists() else None)
    
    def atualizar_lista(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        count = len(self.pedidos)
        self.counter.config(text=f"📊 {count} pedido(s) pendente(s)")
        
        if not self.pedidos:
            tk.Label(self.scrollable_frame, text="🎉 Nenhum pedido pendente\n\nOs alunos aparecerão aqui com suas fotos",
                    font=("Arial", 11), bg="#f0f0f0", fg="#999", justify=tk.CENTER).pack(pady=50)
            return
        
        for i, pedido in enumerate(self.pedidos):
            card = tk.Frame(self.scrollable_frame, bg="white", relief=tk.RAISED, bd=1)
            card.pack(fill=tk.X, pady=5, padx=5)
            
            # Frame da foto
            if pedido['foto']:
                foto_frame = tk.Frame(card, bg="white", padx=5, pady=5)
                foto_frame.pack(side=tk.LEFT)
                
                foto_label = tk.Label(foto_frame, image=pedido['foto'], bg="white")
                foto_label.image = pedido['foto']
                foto_label.pack()
            
            # Informações
            content = tk.Frame(card, bg="white")
            content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            name_color = "#FF6B00" if i == 0 else "#333"
            tk.Label(content, text=f"👤 {pedido['student']}",
                    font=("Arial", 13, "bold"), bg="white", fg=name_color).pack(anchor=tk.W)
            
            tk.Label(content, text=f"📸 {pedido['foto_source']}",
                    font=("Arial", 8), bg="white", fg="#666").pack(anchor=tk.W)
            
            diff = datetime.now() - pedido['time']
            if diff.seconds < 60:
                tempo_texto = "🟢 agora mesmo"
                tempo_cor = "#4CAF50"
            elif diff.seconds < 300:
                tempo_texto = f"🟡 há {diff.seconds // 60} minutos"
                tempo_cor = "#FF9800"
            else:
                tempo_texto = f"🔴 há {diff.seconds // 60} minutos"
                tempo_cor = "#F44336"
            
            tk.Label(content, text=f"⏰ {tempo_texto}",
                    font=("Arial", 10), bg="white", fg=tempo_cor).pack(anchor=tk.W)
            tk.Label(content, text=f"📍 IP: {pedido['ip']}",
                    font=("Arial", 9), bg="white", fg="#999").pack(anchor=tk.W)
            
            def atendido(idx=i):
                aluno = self.pedidos[idx]['student']
                del self.pedidos[idx]
                self.atualizar_lista()
                self.status.config(text=f"✅ {aluno} atendido(a)!", bg="#4CAF50")
                self.root.after(2000, lambda: self.status.config(
                    text=f"✅ Servidor ativo - {len(self.pedidos)} pedido(s)", bg="#4CAF50"))
            
            tk.Button(card, text="✅ Atendido", command=atendido,
                     bg="#4CAF50", fg="white", font=("Arial", 10), padx=15).pack(side=tk.RIGHT, padx=10)
    
    def limpar_todos(self):
        if messagebox.askyesno("Confirmar", "Limpar todos os pedidos?", parent=self.root):
            self.pedidos.clear()
            self.atualizar_lista()
            self.status.config(text="🗑️ Todos removidos", bg="#FF9800")
            self.root.after(2000, lambda: self.status.config(
                text="✅ Servidor ativo - 0 pedidos", bg="#4CAF50"))
    
    def instrucoes(self):
        instr_text = f"""INSTRUÇÕES

IP do Professor: {self.ip}
Porta: 8080

RECURSO DE FOTOS:
• Os alunos enviam suas fotos do sistema
• Fotos aparecem ao lado do nome
• Ajuda na identificação visual

CONFIGURAÇÕES:
• Velocidade da voz: 80-300 wpm
• Agrupamento: 800ms

COMANDOS:
• Clique em "Atendido" após ajudar
• Scroll do mouse para rolar listas"""
        
        messagebox.showinfo("Instruções", instr_text, parent=self.root)
    
    def fechar(self):
        if messagebox.askyesno("Sair", "Desligar servidor?", parent=self.root):
            self.running = False
            self.root.destroy()
    
    def run(self):
        print(f"Iniciando Servidor com Fotos")
        print(f"IP: {self.ip}:8080")
        print(f"PIL disponível: {PIL_AVAILABLE}")
        self.root.mainloop()

if __name__ == "__main__":
    app = ProfessorApp()
    app.run()

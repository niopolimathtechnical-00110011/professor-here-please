#!/usr/bin/env python3
"""
ProfessorHerePlease - App do Aluno com Foto do Usuário
Captura e envia a foto/avatar do usuário do sistema
"""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import os
import sys
import base64
from datetime import datetime
import time
import glob
import subprocess

# Tentar importar PIL
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL não disponível. Instale: sudo apt install python3-pil python3-pil.imagetk")

class AlunoApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Professor Here Please")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        # Configurar janela
        self.root.attributes('-alpha', 0.95)
        self.root.configure(bg='#f0f0f0')
        
        # Configurações
        self.student_name = os.environ.get('USER', os.environ.get('USERNAME', 'Aluno'))
        self.config_dir = os.path.expanduser("~/.professor_here")
        self.config_file = os.path.join(self.config_dir, "professor_ip.txt")
        self.image_config = os.path.join(self.config_dir, "imagem_selecionada.txt")
        self.size_config = os.path.join(self.config_dir, "tamanho_imagem.txt")
        
        # Criar diretório de configuração
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Capturar foto do usuário
        self.user_photo = self.capturar_foto_usuario()
        
        # Criar configurações padrão
        self.criar_configuracoes_padrao()
        
        # Carregar configurações
        self.teacher_ip = self.load_ip()
        self.imagem_atual = self.load_imagem_selecionada()
        self.tamanho_atual = self.load_tamanho()
        
        # Controle de clique
        self.click_start_time = None
        self.is_dragging = False
        self.DRAG_THRESHOLD = 200
        
        # Carregar imagens disponíveis
        self.imagens_disponiveis = self.carregar_imagens()
        
        # Criar janela flutuante
        self.atualizar_janela()
        
        # Eventos de mouse
        self.label.bind("<ButtonPress-1>", self.on_press)
        self.label.bind("<ButtonRelease-1>", self.on_release)
        self.label.bind("<B1-Motion>", self.on_drag)
        self.label.bind("<Button-3>", self.menu_contexto)
        
        # Variáveis para arrasto
        self.drag_x = 0
        self.drag_y = 0
        
        # Verificar IP
        if not self.teacher_ip or self.teacher_ip == "":
            self.root.after(100, self.configurar_ip)
    
    def capturar_foto_usuario(self):
        """Captura a foto/avatar do usuário do sistema"""
        foto_base64 = None
        fonte_foto = None
        
        # Método 1: Linux - Arquivo .face do usuário
        caminhos_face = [
            f"/home/{self.student_name}/.face",
            f"/home/{self.student_name}/.face.icon",
            f"/var/lib/AccountsService/icons/{self.student_name}",
            os.path.expanduser("~/.local/share/faces/icon.png"),
            os.path.expanduser("~/.face"),
            "/etc/passwd"  # fallback
        ]
        
        for caminho in caminhos_face:
            if os.path.exists(caminho) and os.path.getsize(caminho) > 100:
                try:
                    with open(caminho, 'rb') as f:
                        imagem_bytes = f.read()
                        # Verificar se é realmente uma imagem
                        if imagem_bytes.startswith(b'\x89PNG') or imagem_bytes.startswith(b'\xff\xd8'):
                            foto_base64 = base64.b64encode(imagem_bytes).decode('utf-8')
                            fonte_foto = caminho
                            break
                except:
                    pass
        
        # Método 2: Linux - accounts-daemon (GNOME/KDE)
        if not foto_base64:
            try:
                # Tentar via dbus no GNOME
                cmd = ['dbus-send', '--print-reply', '--dest=org.freedesktop.Accounts',
                       '/org/freedesktop/Accounts/User/' + str(os.getuid()),
                       'org.freedesktop.DBus.Properties.Get', 
                       'string:org.freedesktop.Accounts.User', 'string:IconFile']
                resultado = subprocess.run(cmd, capture_output=True, text=True)
                if resultado.returncode == 0:
                    # Extrair caminho do arquivo
                    import re
                    match = re.search(r'"(/[^"]+)"', resultado.stdout)
                    if match:
                        caminho_icone = match.group(1)
                        if os.path.exists(caminho_icone):
                            with open(caminho_icone, 'rb') as f:
                                imagem_bytes = f.read()
                                foto_base64 = base64.b64encode(imagem_bytes).decode('utf-8')
                                fonte_foto = caminho_icone
            except:
                pass
        
        # Método 3: Gerar avatar baseado no nome
        if not foto_base64:
            # Criar um avatar simples baseado nas iniciais
            import hashlib
            initials = ''.join([word[0].upper() for word in self.student_name.split('.')[:2]])
            if not initials:
                initials = self.student_name[0].upper()
            
            # Gerar cor baseada no nome
            hash_obj = hashlib.md5(self.student_name.encode())
            cor = hash_obj.hexdigest()[:6]
            
            # Criar imagem de avatar via PIL se disponível
            if PIL_AVAILABLE:
                try:
                    # Criar imagem 200x200 com fundo colorido
                    img = Image.new('RGBA', (200, 200), (int(cor[0:2], 16), int(cor[2:4], 16), int(cor[4:6], 16), 255))
                    from PIL import ImageDraw, ImageFont
                    draw = ImageDraw.Draw(img)
                    
                    # Desenhar círculo
                    draw.ellipse([10, 10, 190, 190], fill=(255, 255, 255, 100))
                    
                    # Desenhar iniciais
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf", 80)
                    except:
                        font = ImageFont.load_default()
                    
                    # Centralizar texto
                    bbox = draw.textbbox((0, 0), initials, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (200 - text_width) // 2
                    y = (200 - text_height) // 2
                    
                    draw.text((x, y), initials, fill=(255, 255, 255, 255), font=font)
                    
                    # Converter para bytes
                    import io
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    foto_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    fonte_foto = "avatar_gerado"
                except Exception as e:
                    print(f"Erro ao gerar avatar: {e}")
        
        # Método 4: Fallback - dados textuais
        if not foto_base64:
            foto_base64 = base64.b64encode(json.dumps({
                'type': 'text_avatar',
                'name': self.student_name,
                'initials': self.student_name[0].upper() if self.student_name else '?'
            }).encode()).decode('utf-8')
            fonte_foto = "textual"
        
        print(f"📸 Foto do usuário capturada de: {fonte_foto}")
        return {
            'base64': foto_base64,
            'fonte': fonte_foto,
            'nome': self.student_name
        }
    
    def criar_configuracoes_padrao(self):
        """Cria arquivos de configuração padrão se não existirem"""
        # Criar arquivo de imagem padrão
        if not os.path.exists(self.image_config):
            # Procurar por help-me-04-1.png
            img_dir = os.path.join(os.path.dirname(__file__), "imagens_alunos")
            imagem_padrao = None
            
            if os.path.exists(img_dir):
                arquivos = glob.glob(os.path.join(img_dir, "*.png"))
                for arquivo in sorted(arquivos):
                    if 'help-me-04-1' in arquivo:
                        imagem_padrao = arquivo
                        break
                if not imagem_padrao and arquivos:
                    imagem_padrao = arquivos[0]
            
            if not imagem_padrao:
                imagem_padrao = "emoji_homem"
            
            with open(self.image_config, 'w') as f:
                f.write(imagem_padrao)
        
        # Criar arquivo de tamanho padrão
        if not os.path.exists(self.size_config):
            with open(self.size_config, 'w') as f:
                f.write("90")
        
        # Criar arquivo de IP padrão
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as f:
                f.write("")
    
    def carregar_imagens(self):
        """Carrega todas as imagens PNG do diretório"""
        imagens = []
        
        # Adicionar opção padrão de emoji
        imagens.append({
            'arquivo': 'emoji_homem',
            'nome': '🙋‍♂️ Homem',
            'imagem': None,
            'emoji': '🙋‍♂️'
        })
        imagens.append({
            'arquivo': 'emoji_mulher',
            'nome': '🙋‍♀️ Mulher',
            'imagem': None,
            'emoji': '🙋‍♀️'
        })
        
        if not PIL_AVAILABLE:
            return imagens
        
        img_dir = os.path.join(os.path.dirname(__file__), "imagens_alunos")
        
        if os.path.exists(img_dir):
            arquivos = glob.glob(os.path.join(img_dir, "*.png"))
            for arquivo in sorted(arquivos):
                try:
                    img = Image.open(arquivo)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    imagens.append({
                        'arquivo': arquivo,
                        'nome': os.path.basename(arquivo),
                        'imagem': img
                    })
                except Exception as e:
                    print(f"Erro ao carregar {arquivo}: {e}")
        
        return imagens
    
    def load_ip(self):
        try:
            with open(self.config_file, 'r') as f:
                ip = f.read().strip()
                return ip if ip else None
        except:
            return None
    
    def save_ip(self, ip):
        with open(self.config_file, 'w') as f:
            f.write(ip)
        self.teacher_ip = ip
    
    def load_imagem_selecionada(self):
        try:
            with open(self.image_config, 'r') as f:
                imagem = f.read().strip()
                if imagem and imagem != "padrao":
                    if os.path.exists(imagem):
                        return imagem
                    for img in self.imagens_disponiveis:
                        if img['arquivo'] == imagem:
                            return imagem
                return self.imagens_disponiveis[0]['arquivo'] if self.imagens_disponiveis else 'emoji_homem'
        except:
            return self.imagens_disponiveis[0]['arquivo'] if self.imagens_disponiveis else 'emoji_homem'
    
    def save_imagem_selecionada(self, arquivo):
        with open(self.image_config, 'w') as f:
            f.write(arquivo)
        self.imagem_atual = arquivo
    
    def load_tamanho(self):
        try:
            with open(self.size_config, 'r') as f:
                tamanho = int(f.read().strip())
                return max(33, min(180, tamanho))
        except:
            return 90
    
    def save_tamanho(self, tamanho):
        with open(self.size_config, 'w') as f:
            f.write(str(tamanho))
        self.tamanho_atual = tamanho
    
    def criar_imagem_tk(self, arquivo, tamanho):
        """Cria imagem redimensionada para Tkinter"""
        for img in self.imagens_disponiveis:
            if img['arquivo'] == arquivo:
                if 'emoji' in img:
                    return img['emoji']
                if PIL_AVAILABLE and img.get('imagem'):
                    try:
                        img_copy = img['imagem'].copy()
                        img_copy.thumbnail((tamanho, tamanho), Image.Resampling.LANCZOS)
                        self.photo = ImageTk.PhotoImage(img_copy)
                        return self.photo
                    except:
                        return "🙋"
                return "🙋"
        return "🙋"
    
    def atualizar_janela(self):
        """Atualiza a janela com a imagem/emoji redimensionado"""
        if hasattr(self, 'label'):
            self.label.destroy()
        
        imagem_obj = self.criar_imagem_tk(self.imagem_atual, self.tamanho_atual)
        
        if isinstance(imagem_obj, str):
            self.label = tk.Label(self.root, text=imagem_obj, 
                                  font=("Segoe UI Emoji", self.tamanho_atual//2),
                                  bg='#f0f0f0', fg="#FFA500", cursor="hand2")
        else:
            self.label = tk.Label(self.root, image=imagem_obj, 
                                  bg='#f0f0f0', cursor="hand2", bd=0)
        
        self.label.pack(fill=tk.BOTH, expand=True)
        self.root.geometry(f"{self.tamanho_atual+20}x{self.tamanho_atual+20}+100+100")
        
        self.label.bind("<ButtonPress-1>", self.on_press)
        self.label.bind("<ButtonRelease-1>", self.on_release)
        self.label.bind("<B1-Motion>", self.on_drag)
        self.label.bind("<Button-3>", self.menu_contexto)
    
    def on_press(self, event):
        self.click_start_time = time.time() * 1000
        self.is_dragging = False
        self.drag_x = event.x
        self.drag_y = event.y
    
    def on_drag(self, event):
        if self.click_start_time:
            self.is_dragging = True
            x = self.root.winfo_x() + event.x - self.drag_x
            y = self.root.winfo_y() + event.y - self.drag_y
            self.root.geometry(f"+{x}+{y}")
    
    def on_release(self, event):
        if self.click_start_time and not self.is_dragging:
            press_duration = (time.time() * 1000) - self.click_start_time
            if press_duration < self.DRAG_THRESHOLD:
                self.pedir_ajuda()
        
        self.click_start_time = None
        self.is_dragging = False
    
    def pedir_ajuda(self):
        if not self.teacher_ip:
            self.configurar_ip()
            return
        
        try:
            self.label.config(alpha=0.5)
        except:
            pass
        self.root.update()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            
            # Enviar mensagem com a foto do usuário
            msg = json.dumps({
                "type": "help",
                "student": self.student_name,
                "time": datetime.now().isoformat(),
                "os": sys.platform,
                "timestamp": time.time(),
                "user_photo": self.user_photo['base64'],
                "photo_source": self.user_photo['fonte']
            })
            sock.sendto(msg.encode(), (self.teacher_ip, 8080))
            sock.close()
            
            self.mostrar_mensagem(f"✅ Ajuda enviada! Sua foto foi incluída.", "#4CAF50")
            
        except Exception as e:
            self.mostrar_mensagem(f"❌ Erro: {str(e)[:30]}", "#f44336")
        
        finally:
            try:
                self.label.config(alpha=1.0)
            except:
                pass
    
    def mostrar_mensagem(self, texto, cor="#333"):
        msg = tk.Toplevel(self.root)
        msg.overrideredirect(True)
        msg.configure(bg=cor)
        x = self.root.winfo_x() + 10
        y = self.root.winfo_y() - 30
        msg.geometry(f"+{x}+{y}")
        
        tk.Label(msg, text=texto, bg=cor, fg="white",
                font=("Arial", 10), padx=10, pady=5).pack()
        
        self.root.after(2000, msg.destroy)
    
    def configurar_ip(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Configurar IP do Professor")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(dialog, text="Configuração do Professor", 
                font=("Arial", 12, "bold")).pack(pady=10)
        
        tk.Label(dialog, text=f"👤 Aluno: {self.student_name}",
                font=("Arial", 10)).pack()
        
        tk.Label(dialog, text=f"📸 Foto: {self.user_photo['fonte']}",
                font=("Arial", 9), fg="#666").pack()
        
        tk.Label(dialog, text="\n📡 IP do Professor:", font=("Arial", 10)).pack()
        
        entry = tk.Entry(dialog, width=25, font=("Arial", 11))
        entry.pack(pady=5)
        entry.insert(0, "192.168.1.100")
        entry.focus()
        
        def salvar():
            ip = entry.get().strip()
            if ip:
                self.save_ip(ip)
                dialog.destroy()
                self.mostrar_mensagem(f"✅ IP configurado: {ip}", "#4CAF50")
        
        tk.Button(dialog, text="💾 Salvar", command=salvar,
                 bg="#4CAF50", fg="white", padx=30, pady=5).pack(pady=10)
        
        tk.Label(dialog, text="Dica: O IP aparece no app do professor",
                font=("Arial", 8), fg="#666").pack()
    
    def selecionar_imagem(self):
        """Janela para selecionar imagem"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Selecionar Imagem do Aluno")
        dialog.geometry("650x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (dialog.winfo_screenheight() // 2) - (550 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = tk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Info da foto do usuário
        info_frame = tk.Frame(main_frame, bg="#e3f2fd", relief=tk.GROOVE, bd=1)
        info_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(info_frame, text=f"📸 Sua foto atual: {self.user_photo['fonte']}", 
                bg="#e3f2fd", fg="#1976d2", font=("Arial", 9)).pack(pady=5)
        
        # Controles de tamanho
        controle_frame = tk.Frame(main_frame, bg="#f0f0f0", relief=tk.GROOVE, bd=1)
        controle_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(controle_frame, text="📏 Tamanho da imagem:").pack(side=tk.LEFT, padx=10, pady=5)
        
        tamanho_var = tk.IntVar(value=self.tamanho_atual)
        tamanho_scale = tk.Scale(controle_frame, from_=33, to=180, orient=tk.HORIZONTAL,
                                 variable=tamanho_var, length=200)
        tamanho_scale.pack(side=tk.LEFT, padx=10, pady=5)
        
        lbl_tamanho = tk.Label(controle_frame, text=f"{self.tamanho_atual}px", font=("Arial", 10, "bold"))
        lbl_tamanho.pack(side=tk.LEFT, padx=10)
        
        def atualizar_tamanho(*args):
            lbl_tamanho.config(text=f"{tamanho_var.get()}px")
        
        tamanho_var.trace('w', atualizar_tamanho)
        
        # Canvas com scroll
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Grid de imagens
        row = 0
        col = 0
        
        for img_info in self.imagens_disponiveis:
            if PIL_AVAILABLE and img_info.get('imagem'):
                img_thumb = img_info['imagem'].copy()
                img_thumb.thumbnail((80, 80), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_thumb)
                
                img_frame = tk.Frame(scrollable_frame, relief=tk.RAISED, bd=2)
                img_frame.grid(row=row, column=col, padx=5, pady=5)
                
                lbl = tk.Label(img_frame, image=photo, cursor="hand2")
                lbl.image = photo
                lbl.pack(padx=10, pady=5)
            else:
                emoji = img_info.get('emoji', '🙋')
                img_frame = tk.Frame(scrollable_frame, relief=tk.RAISED, bd=2)
                img_frame.grid(row=row, column=col, padx=5, pady=5)
                
                lbl = tk.Label(img_frame, text=emoji, font=("Segoe UI Emoji", 40),
                               cursor="hand2")
                lbl.pack(padx=10, pady=5)
            
            nome_texto = img_info['nome'].replace('.png', '').replace('help-me-', '')
            nome = tk.Label(img_frame, text=nome_texto[:15], font=("Arial", 8))
            nome.pack()
            
            if img_info['arquivo'] == self.imagem_atual:
                tk.Label(img_frame, text="✓ ATUAL", fg="green", font=("Arial", 8, "bold")).pack()
            
            def selecionar(arquivo=img_info['arquivo']):
                self.save_imagem_selecionada(arquivo)
                novoTamanho = tamanho_var.get()
                self.save_tamanho(novoTamanho)
                self.tamanho_atual = novoTamanho
                self.atualizar_janela()
                self.mostrar_mensagem("✅ Imagem alterada!", "#4CAF50")
                dialog.destroy()
            
            lbl.bind("<Button-1>", lambda e, s=selecionar: s())
            
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Fechar", command=dialog.destroy,
                 bg="#2196F3", fg="white", padx=30, pady=5).pack()
    
    def menu_contexto(self, event):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="⚙️ Configurar IP", command=self.configurar_ip)
        menu.add_command(label="🖼️ Trocar Imagem", command=self.selecionar_imagem)
        menu.add_separator()
        menu.add_command(label="📸 Minha Foto", command=self.mostrar_foto)
        menu.add_command(label="🎯 Funcionalidades", command=self.funcionalidades)
        menu.add_command(label="ℹ️ Sobre", command=self.sobre)
        menu.add_command(label="☕ Doações", command=self.doacoes)
        menu.add_separator()
        menu.add_command(label="🚪 Sair", command=self.sair)
        menu.post(event.x_root, event.y_root)
    
    def mostrar_foto(self):
        """Mostra a foto capturada do usuário"""
        if self.user_photo and self.user_photo['base64']:
            try:
                # Decodificar e mostrar a foto
                foto_bytes = base64.b64decode(self.user_photo['base64'])
                
                if PIL_AVAILABLE:
                    from PIL import Image
                    import io
                    
                    img = Image.open(io.BytesIO(foto_bytes))
                    img.thumbnail((300, 300))
                    
                    # Criar janela para mostrar
                    foto_window = tk.Toplevel(self.root)
                    foto_window.title("Minha Foto de Perfil")
                    foto_window.geometry("350x400")
                    foto_window.transient(self.root)
                    
                    photo_tk = ImageTk.PhotoImage(img)
                    lbl_foto = tk.Label(foto_window, image=photo_tk)
                    lbl_foto.image = photo_tk
                    lbl_foto.pack(pady=20)
                    
                    tk.Label(foto_window, text=f"Fonte: {self.user_photo['fonte']}", 
                            font=("Arial", 9), fg="#666").pack()
                    tk.Label(foto_window, text=f"Usuário: {self.student_name}", 
                            font=("Arial", 10, "bold")).pack()
                    
                    tk.Button(foto_window, text="Fechar", command=foto_window.destroy,
                             bg="#2196F3", fg="white", padx=20).pack(pady=10)
                else:
                    messagebox.showinfo("Minha Foto", 
                        f"Foto capturada de: {self.user_photo['fonte']}\n"
                        f"Usuário: {self.student_name}\n\n"
                        f"(Instale o PIL para ver a imagem: sudo apt install python3-pil python3-pil.imagetk)",
                        parent=self.root)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível mostrar a foto: {e}", parent=self.root)
    
    def funcionalidades(self):
        func_text = """🎯 FUNCIONALIDADES DO APP

📱 AÇÕES PRINCIPAIS:
• Clique na imagem = pedir ajuda
• Arraste = mover ícone pela tela
• Botão direito = menu de opções

📸 FOTO DO USUÁRIO:
• Captura automática da foto do sistema
• Envia junto com o pedido de ajuda
• Ajuda o professor a identificar o aluno

🖼️ PERSONALIZAÇÃO:
• Selecione entre várias imagens de alunos
• Ajuste o tamanho da imagem (33-180px)
• Imagem salva permanentemente

⚙️ CONFIGURAÇÕES:
• IP do professor persistente
• Nome do usuário automático
• Fundo semi-transparente

📡 COMUNICAÇÃO:
• UDP para rede local
• Notificação com voz no professor
• Agrupamento de múltiplos alunos

✨ VERSÃO: 6.0.0 - Com Foto do Usuário!"""
        
        messagebox.showinfo("Funcionalidades", func_text, parent=self.root)
    
    def sobre(self):
        about_text = """👨‍💻 DESENVOLVEDOR

Enio Alves Borges
GitHub: @niopolimathtechnical-00110011

📦 PROJETO: ProfessorHerePlease
🎯 VERSÃO: 6.0.0 (Com Foto do Usuário)
📅 DATA: Maio 2026

🌍 PLATAFORMAS:
• Linux 🐧
• Windows 🪟
• macOS 🖥️
• Android 📱

✨ RECURSOS:
• 📸 Captura foto do usuário do sistema
• 🖼️ Imagens com fundo transparente
• 📏 Redimensionamento dinâmico
• 💾 Persistência de configurações
• 📡 Comunicação UDP em rede local

🎓 EDUCACIONAL:
Desenvolvido para auxiliar em sala de aula,
permitindo alunos solicitarem ajuda
discretamente ao professor."""
        
        messagebox.showinfo("Sobre o App", about_text, parent=self.root)
    
    def doacoes(self):
        doacoes_text = """☕ APOIE O PROJETO ☕

Sua contribuição ajuda a manter o projeto vivo!

💰 MÉTODOS DE DOAÇÃO:

📱 PIX (Brasil)
Chave: soletrepix@gmail.com
Titular: Enio Alves Borges
Banco: Banco do Brasil

🪙 Criptomoedas (BTC/ETH)
Solicitar endereço por e-mail

🐠🐟 Sua contribuição, não importa o valor,
   faz diferença e incentiva novas funcionalidades!

Obrigado por apoiar software livre e educacional! 🎓"""
        
        messagebox.showinfo("Doações - Apoie o Projeto", doacoes_text, parent=self.root)
    
    def sair(self):
        if messagebox.askyesno("Sair", "Deseja sair do Professor Here Please?", parent=self.root):
            self.root.quit()
            sys.exit(0)
    
    def run(self):
        print("=" * 50)
        print("🚀 Professor Here Please v6.0 - Com Foto do Usuário")
        print("=" * 50)
        print(f"👤 Aluno: {self.student_name}")
        print(f"📸 Foto capturada de: {self.user_photo['fonte']}")
        print(f"🖼️ Imagem atual: {os.path.basename(self.imagem_atual) if self.imagem_atual else 'padrao'}")
        print(f"📏 Tamanho: {self.tamanho_atual}x{self.tamanho_atual}px")
        print(f"📡 IP do Professor: {self.teacher_ip or 'Não configurado'}")
        print("-" * 50)
        print("💡 DICAS:")
        print("   • Clique na imagem = pedir ajuda")
        print("   • Arraste = mover ícone pela tela")
        print("   • Botão direito = menu de opções")
        print("   • Menu 'Minha Foto' para ver sua foto de perfil")
        print("=" * 50)
        
        self.root.mainloop()

if __name__ == "__main__":
    app = AlunoApp()
    app.run()

"""
Professor App - Sim_Pois_Não
Recebe notificações dos alunos via UDP
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.utils import platform
from kivy.core.audio import SoundLoader
from plyer import tts
import socket
import threading
import json
from datetime import datetime
import os

# Registrar fonte emoji
LabelBase.register(name='NotoColorEmoji',
                   fn_regular='/system/fonts/NotoColorEmoji.ttf')

class HelpRequest:
    def __init__(self, student_name, ip, timestamp):
        self.student_name = student_name
        self.ip = ip
        self.timestamp = timestamp

class ProfessorApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.help_requests = []
        self.server_running = False
        self.udp_socket = None
        self.is_speaking = False
        self.speech_queue = []
        
    def build(self):
        # Layout principal
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Status bar
        self.status_layout = BoxLayout(orientation='vertical', size_hint_y=0.15)
        
        self.ip_label = Label(
            text=f"Iniciando servidor...\nIP: Carregando...",
            size_hint_y=0.5,
            color=(0.2, 0.6, 0.2, 1),
            font_size=14
        )
        self.status_layout.add_widget(self.ip_label)
        
        self.server_status = Label(
            text="🟡 Iniciando...",
            size_hint_y=0.3,
            color=(1, 1, 0, 1),
            font_size=12
        )
        self.status_layout.add_widget(self.server_status)
        
        main_layout.add_widget(self.status_layout)
        
        # Título da lista
        self.count_label = Label(
            text="📋 Pedidos pendentes: 0",
            size_hint_y=0.05,
            color=(0.2, 0.2, 0.2, 1),
            font_size=14,
            bold=True
        )
        main_layout.add_widget(self.count_label)
        
        # Lista de pedidos (scroll)
        self.scroll = ScrollView()
        self.list_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)
        main_layout.add_widget(self.scroll)
        
        # Botões de ação
        btn_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        
        clear_btn = Button(text="Limpar Todos", background_color=(0.8, 0.2, 0.2, 1))
        clear_btn.bind(on_press=self.clear_all_requests)
        
        info_btn = Button(text="Info", background_color=(0.2, 0.2, 0.8, 1))
        info_btn.bind(on_press=self.show_info)
        
        btn_layout.add_widget(clear_btn)
        btn_layout.add_widget(info_btn)
        main_layout.add_widget(btn_layout)
        
        # Iniciar servidor
        Clock.schedule_once(lambda dt: self.start_server(), 0.5)
        
        return main_layout
    
    def get_local_ip(self):
        """Obtém o IP local da máquina"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def speak_text(self, text):
        """Fala o texto usando TTS"""
        if platform == 'android':
            try:
                tts.speak(text)
            except:
                print(f"TTS: {text}")
        else:
            print(f"TTS: {text}")
    
    def speak_with_queue(self, text):
        """Adiciona texto à fila de fala"""
        self.speech_queue.append(text)
        if not self.is_speaking:
            self.process_speech_queue()
    
    def process_speech_queue(self):
        """Processa a fila de fala"""
        if self.speech_queue:
            self.is_speaking = True
            text = self.speech_queue.pop(0)
            self.speak_text(text)
            # Aguarda um pouco antes de processar o próximo
            Clock.schedule_once(lambda dt: self.process_speech_queue(), 3)
        else:
            self.is_speaking = False
    
    def start_server(self):
        """Inicia o servidor UDP"""
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.bind(('', 8080))
            self.server_running = True
            
            ip = self.get_local_ip()
            
            Clock.schedule_once(lambda dt: self.update_status(
                f"✅ Servidor Ativo\n📡 IP: {ip}:8080",
                (0, 1, 0, 1),
                "🟢 Online"
            ), 0)
            
            # Thread para receber mensagens
            def receive_messages():
                while self.server_running:
                    try:
                        data, addr = self.udp_socket.recvfrom(4096)
                        message = json.loads(data.decode())
                        
                        if message.get('type') == 'help':
                            student_name = message.get('student', 'Aluno')
                            timestamp = message.get('timestamp', datetime.now().isoformat())
                            
                            # Adicionar à lista
                            self.help_requests.insert(0, {
                                'student': student_name,
                                'time': datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else datetime.now(),
                                'ip': addr[0]
                            })
                            
                            # Atualizar UI
                            Clock.schedule_once(lambda dt: self.update_requests_list(), 0)
                            
                            # Falar o nome
                            self.speak_with_queue(f"Professor, o {student_name} está pedindo ajuda!")
                            
                            # Mostrar popup se for o primeiro
                            if len(self.help_requests) == 1:
                                Clock.schedule_once(lambda dt: self.show_notification(student_name), 0)
                            
                    except Exception as e:
                        print(f"Erro ao receber: {e}")
            
            thread = threading.Thread(target=receive_messages, daemon=True)
            thread.start()
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(
                f"❌ Erro: {str(e)[:50]}",
                (1, 0, 0, 1),
                "🔴 Erro"
            ), 0)
    
    def update_status(self, text, color, status):
        """Atualiza o status do servidor"""
        self.ip_label.text = text
        self.ip_label.color = color
        self.server_status.text = status
    
    def update_requests_list(self):
        """Atualiza a lista de pedidos"""
        self.list_layout.clear_widgets()
        
        count = len(self.help_requests)
        self.count_label.text = f"📋 Pedidos pendentes: {count}"
        
        if count == 0:
            empty_label = Label(
                text="🎉 Nenhum pedido pendente\n\nOs alunos aparecerão aqui",
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=1,
                halign='center'
            )
            self.list_layout.add_widget(empty_label)
            return
        
        for i, request in enumerate(self.help_requests[:20]):
            # Card do pedido
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=120)
            card.add_widget(Label(size_hint_y=0.05))  # Espaçador
            
            # Nome do aluno
            name_color = (1, 0.4, 0, 1) if i == 0 else (0, 0, 0, 1)
            name_layout = BoxLayout(size_hint_y=0.3)
            name_layout.add_widget(Label(
                text=f"🙋 {request['student']}",
                color=name_color,
                font_size=16,
                bold=True,
                halign='left'
            ))
            card.add_widget(name_layout)
            
            # Tempo
            diff = datetime.now() - request['time']
            if diff.seconds < 60:
                time_text = f"🟢 agora mesmo"
                time_color = (0, 1, 0, 1)
            elif diff.seconds < 300:
                time_text = f"🟡 há {diff.seconds // 60} minutos"
                time_color = (1, 1, 0, 1)
            else:
                time_text = f"🔴 há {diff.seconds // 60} minutos"
                time_color = (1, 0, 0, 1)
            
            time_layout = BoxLayout(size_hint_y=0.25)
            time_layout.add_widget(Label(
                text=time_text,
                color=time_color,
                font_size=12,
                halign='left'
            ))
            card.add_widget(time_layout)
            
            # IP
            ip_layout = BoxLayout(size_hint_y=0.25)
            ip_layout.add_widget(Label(
                text=f"📍 {request['ip']}",
                color=(0.5, 0.5, 0.5, 1),
                font_size=11,
                halign='left'
            ))
            card.add_widget(ip_layout)
            
            # Botão atender
            btn_layout = BoxLayout(size_hint_y=0.2)
            attend_btn = Button(
                text="✅ ATENDIDO",
                size_hint_x=0.5,
                background_color=(0, 0.8, 0, 1)
            )
            attend_btn.bind(on_press=lambda btn, idx=i: self.mark_as_helped(idx))
            btn_layout.add_widget(attend_btn)
            card.add_widget(btn_layout)
            
            self.list_layout.add_widget(card)
    
    def mark_as_helped(self, index):
        """Marca pedido como atendido"""
        if index < len(self.help_requests):
            student = self.help_requests[index]['student']
            del self.help_requests[index]
            self.update_requests_list()
            self.speak_with_queue(f"Aluno {student} foi atendido")
            
            # Mostrar popup
            popup = Popup(
                title="Atendido",
                content=Label(text=f"✅ {student} atendido com sucesso"),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def clear_all_requests(self, instance):
        """Limpa todos os pedidos"""
        self.help_requests.clear()
        self.update_requests_list()
        self.speak_with_queue("Todos os pedidos foram removidos")
        
        popup = Popup(
            title="Limpo",
            content=Label(text="🗑️ Todos os pedidos foram removidos"),
            size_hint=(0.6, 0.3)
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def show_notification(self, student_name):
        """Mostra popup de notificação"""
        popup = Popup(
            title="🔔 NOVO PEDIDO!",
            content=Label(
                text=f"{student_name} está pedindo ajuda!\n\nClique em ATENDIDO para responder",
                size_hint=(1, 1)
            ),
            size_hint=(0.8, 0.4)
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 5)
    
    def show_info(self, instance):
        """Mostra informações do app"""
        ip = self.get_local_ip()
        info_text = f"📡 Sim_Pois_Não - Professor\n\n"
        info_text += f"IP do Servidor: {ip}\n"
        info_text += f"Porta: 8080\n\n"
        info_text += f"📋 Status: {'Online' if self.server_running else 'Offline'}\n"
        info_text += f"📊 Pedidos: {len(self.help_requests)}\n\n"
        info_text += f"📱 Instruções:\n"
        info_text += f"1. Informe o IP acima aos alunos\n"
        info_text += f"2. Alunos configuram o IP\n"
        info_text += f"3. Receba notificações em tempo real"
        
        popup = Popup(
            title="Informações",
            content=Label(text=info_text, size_hint=(1, 1)),
            size_hint=(0.9, 0.7)
        )
        popup.open()
    
    def on_stop(self):
        """Parar o servidor ao fechar"""
        self.server_running = False
        if self.udp_socket:
            self.udp_socket.close()

if __name__ == '__main__':
    ProfessorApp().run()

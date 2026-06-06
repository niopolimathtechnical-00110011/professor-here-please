#!/bin/bash
echo "🚀 Instalador Completo - Professor Here Please"
echo "=============================================="

# Verificar se é root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️ Não execute como root. Use sudo."
    exit 1
fi

# Instalar dependências
echo "📦 Instalando dependências..."
sudo apt update
sudo apt install -y python3 python3-tk python3-pil python3-pil.imagetk

# Instalar espeak opcional
read -p "Instalar espeak para voz? (s/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    sudo apt install -y espeak
fi

# Instalar o pacote
echo "📦 Instalando Professor Here Please..."
sudo dpkg -i professor-here-please_6.0.0_all.deb
sudo apt-get install -f -y

echo ""
echo "✅ INSTALAÇÃO CONCLUÍDA!"
echo ""
echo "=============================================="
echo "📱 COMO USAR:"
echo "=============================================="
echo ""
echo "👨‍🎓 ALUNO (solicitar ajuda):"
echo "   • Execute: professor-aluno"
echo "   • Ou clique no ícone no menu 'Educação'"
echo "   • Clique na imagem para pedir ajuda"
echo "   • Botão direito para configurar IP"
echo ""
echo "👨‍🏫 PROFESSOR (receber notificações):"
echo "   • Execute: professor-professor"
echo "   • O IP do servidor aparecerá na tela"
echo "   • Passe o IP para os alunos"
echo "   • Receba notificações com fotos dos alunos"
echo ""
echo "⚙️ CONFIGURAÇÕES:"
echo "   • O app do aluno inicia automaticamente"
echo "   • Configurações salvas em: ~/.professor_here/"
echo "   • Fotos dos alunos são enviadas automaticamente"
echo ""
echo "🔧 PARA REMOVER:"
echo "   sudo dpkg --purge professor-here-please"
echo ""
echo "🐛 RELATAR PROBLEMAS:"
echo "   GitHub: @niopolimathtechnical-00110011"
echo "   Email: niopolimathtechnical@gmail.com
echo ""

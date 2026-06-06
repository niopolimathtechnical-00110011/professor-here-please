#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Iniciando Professor Here Please - Aluno"
echo "==========================================="
echo "👤 Usuário: $(whoami)"
echo "💡 Dicas:"
echo "   • Clique na imagem = pedir ajuda"
echo "   • Arraste = mover o ícone"
echo "   • Botão direito = menu de opções"
echo "==========================================="
echo ""
python3 aluno_com_foto.py

#!/bin/bash

# Etapa 1: Limpeza
echo "=== ETAPA 1: LIMPEZA ==="
rm -f professor-here-please_*.deb
rm -rf deb_package
echo "✅ Limpeza concluída"
sleep 1

# Etapa 2: Criar diretórios
echo "=== ETAPA 2: CRIANDO DIRETÓRIOS ==="
mkdir -p deb_package/DEBIAN
mkdir -p deb_package/usr/local/bin
mkdir -p deb_package/usr/local/share/professor-here
mkdir -p deb_package/usr/share/applications
mkdir -p deb_package/usr/share/icons/hicolor/128x128/apps
mkdir -p deb_package/usr/share/doc/professor-here
mkdir -p deb_package/etc/xdg/autostart
echo "✅ Diretórios criados"
sleep 1

# Etapa 3: Copiar arquivos principais
echo "=== ETAPA 3: COPIANDO ARQUIVOS ==="
cp aluno_com_foto.py deb_package/usr/local/share/professor-here/aluno.py
cp professor_com_foto.py deb_package/usr/local/share/professor-here/professor.py

if [ -d "imagens_alunos" ]; then
    cp -r imagens_alunos deb_package/usr/local/share/professor-here/
else
    mkdir -p deb_package/usr/local/share/professor-here/imagens_alunos
fi

chmod +x deb_package/usr/local/share/professor-here/aluno.py
chmod +x deb_package/usr/local/share/professor-here/professor.py
echo "✅ Arquivos copiados"
sleep 1

# Etapa 4: Criar binários
echo "=== ETAPA 4: CRIANDO BINÁRIOS ==="
printf '#!/bin/bash\ncd /usr/local/share/professor-here\npython3 aluno.py "$@"\n' > deb_package/usr/local/bin/professor-aluno
printf '#!/bin/bash\ncd /usr/local/share/professor-here\npython3 professor.py "$@"\n' > deb_package/usr/local/bin/professor-professor
chmod +x deb_package/usr/local/bin/professor-aluno
chmod +x deb_package/usr/local/bin/professor-professor
echo "✅ Binários criados"
sleep 1

# Etapa 5: Criar arquivos .desktop
echo "=== ETAPA 5: CRIANDO ARQUIVOS DESKTOP ==="
cat > deb_package/usr/share/applications/professor-aluno.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Professor Here Please - Aluno
Comment=Solicitar ajuda do professor
Exec=/usr/local/bin/professor-aluno
Icon=professor-here-aluno
Terminal=false
Categories=Education;Utility;
StartupNotify=true
X-GNOME-Autostart-enabled=true

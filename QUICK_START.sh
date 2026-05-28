#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   🚀 QUICK START - Sistema de Monitoramento Regulatório      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Detectar Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "❌ Python não encontrado! Instale Python 3.8+"
    exit 1
fi

echo "✅ Python encontrado: $($PYTHON --version)"
echo ""

# Criar venv (opcional)
read -p "Criar ambiente virtual? (s/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "📦 Criando venv..."
    $PYTHON -m venv venv
    source venv/bin/activate
    echo "✅ Venv criado e ativado"
fi

echo ""
echo "📥 Instalando dependências (pode levar 1-2 minutos)..."
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Dependências instaladas"
else
    echo "⚠️  Erro ao instalar dependências"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   ESCOLHA UMA OPÇÃO:                          ║"
echo "├────────────────────────────────────────────────────────────────┤"
echo "║  1. Executar sistema (terminal)                              ║"
echo "║  2. Abrir interface Streamlit (web)                          ║"
echo "║  3. Ver estrutura do projeto                                 ║"
echo "║  4. Executar testes                                          ║"
echo "║  5. Sair                                                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

read -p "Digite sua escolha (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🔄 Executando sistema..."
        echo ""
        $PYTHON main.py
        ;;
    2)
        echo ""
        echo "🌐 Abrindo interface Streamlit..."
        echo "   Acesse: http://localhost:8501"
        echo ""
        streamlit run app.py
        ;;
    3)
        echo ""
        echo "📁 Estrutura do projeto:"
        echo ""
        tree -L 2 -I '__pycache__|*.pyc' . || find . -type f -name "*.py" | head -20
        ;;
    4)
        echo ""
        echo "🧪 Executando testes..."
        $PYTHON -m pytest tests/ -v
        ;;
    5)
        echo "Até logo! 👋"
        exit 0
        ;;
    *)
        echo "❌ Opção inválida!"
        exit 1
        ;;
esac

echo ""
echo "✅ Concluído!"

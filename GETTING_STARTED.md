# 🚀 Próximos Passos - Guia Prático

## 1️⃣ Instalação de Dependências

```bash
# Navegar para o diretório
cd /home/rotsen/Área\ de\ Trabalho/1_Semestre_Doutorado/Agentes\ De\ IA/TP

# Criar ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

## 2️⃣ Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas credenciais
nano .env  # ou seu editor preferido
```

**Campos importantes a preencher:**
- `LLM_API_KEY`: Sua chave da API (OpenAI, Anthropic, etc)
- `LLM_MODEL`: Modelo a usar (gpt-4, claude-3, etc)
- `EMBEDDING_MODEL`: Modelo de embeddings (já tem default)

## 3️⃣ Primeira Execução

### Opção A: Via linha de comando (teste rápido)
```bash
python3 main.py
```

Isso executará um ciclo completo com dados de teste e exibirá os alertas gerados.

### Opção B: Via Streamlit (interface visual)
```bash
streamlit run app.py
```

Abrirá uma interface web em `http://localhost:8501`

## 4️⃣ Prioridades de Implementação

### FASE 1 - Coleta de Dados (🔥 Critical)
1. **Implementar `_fetch_bcb_documents()`** 
   - Arquivo: `src/agents/monitor_agent.py`
   - Tarefas:
     - Parser de RSS do BCB
     - Normalizar tipos de documentos
     - Trata de exceções

2. **Implementar `_fetch_cvm_documents()`**
   - Similar ao BCB mas para CVM
   - Portal CVM é mais complexo (pode precisar de scraping)

### FASE 2 - Análise e Extração (🔥 Critical)
1. **Implementar `_extract_dates()`** em `src/agents/analysis_agent.py`
   - Regex para formatos brasileiros
   - Processar prazos relativos ("30 dias após publicação")

2. **Implementar `_extract_obligations()`**
   - NER ou busca de palavras-chave
   - Estruturar como lista

3. **Integrar com LLM para sumarização**
   - Criar `src/utils/llm_integration.py`
   - Usar prompts em português

### FASE 3 - Persistência (📋 Important)
1. **Criar schema de banco de dados** (`database/schema.sql`)
2. **Implementar `DocumentRepository`** em `src/utils/data_collection.py`
3. **Salvar histórico processado**

### FASE 4 - Teste e Avaliação (📊 Important)
1. **Criar corpus anotado** em `data/test_corpus.json`
   - ~30-50 documentos reais
   - Anotados com verdade-ouro

2. **Calcular métricas**
   - Precisão/Recall/F1 para classificação
   - Acurácia para campos extraídos

## 5️⃣ Exemplo: Implementar coleta BCB

**Arquivo:** `src/agents/monitor_agent.py`

**Função a completar:**
```python
def _fetch_bcb_documents(self, url: str) -> List[RegulatoryDocument]:
    """Coleta documentos do BCB via RSS"""
    try:
        # 1. Parse RSS
        feed = feedparser.parse("https://www.bcb.gov.br/htms/novidades/ult_noticias.xml")
        
        documents = []
        for entry in feed.entries:
            # 2. Filtar apenas atos normativos (palavras-chave: "Circular", "Resolução", etc)
            if not any(word in entry.title for word in ["Circular", "Resolução", "Ofício"]):
                continue
            
            # 3. Criar RegulatoryDocument
            doc = RegulatoryDocument(
                id=entry.get('id', entry.link),
                title=entry.title,
                source="BCB",
                document_type=self._detect_document_type(entry.title),
                published_date=datetime.fromisoformat(entry.published),
                url=entry.link,
                content=entry.summary
            )
            documents.append(doc)
        
        return documents
        
    except Exception as e:
        logger.error(f"Erro ao coletar BCB: {e}")
        return []
```

## 6️⃣ Estrutura de Commits Recomendada

```bash
# Commit 1: Setup inicial (já feito)
git add .
git commit -m "Initial project structure with 3 agents"

# Commit 2: Implementar coleta
git commit -m "Implement BCB and CVM document collection"

# Commit 3: Implementar extração
git commit -m "Implement information extraction (dates, obligations)"

# Commit 4: Integrar LLM
git commit -m "Add LLM integration for advanced analysis"

# Commit 5: Banco de dados
git commit -m "Add database persistence layer"

# Commit 6: Testes e avaliação
git commit -m "Add evaluation metrics and test corpus"
```

## 7️⃣ Debugging e Teste Local

### Ver logs detalhados
```bash
# Editar main.py, adicionar ao topo:
import logging
logging.basicConfig(level=logging.DEBUG)

python3 main.py
```

### Testar componentes isoladamente
```python
# Em um script Python (test.py)
from src.agents.monitor_agent import MonitorAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.alert_agent import AlertAgent

# Testar Monitor Agent
monitor = MonitorAgent()
print("Monitor status:", monitor.get_status())

# Testar Analysis Agent
analysis = AnalysisAgent()
result = analysis.analyze_document("Texto de teste...", {"id": "1", "source": "BCB"})
print("Analysis:", result)

# Testar Alert Agent
alert_agent = AlertAgent()
alert = alert_agent.generate_alert({"title": "Test", "source_url": "..."})
print(alert_agent.format_for_display(alert))
```

## 8️⃣ Testes Automatizados (Opcional)

```bash
# Criar arquivo tests/test_agents.py
# Adicionar testes unitários

# Executar
python3 -m pytest tests/ -v
```

## 9️⃣ Deploy da Interface

```bash
# Streamlit cloud deployment (gratuito)
# 1. Push para GitHub
# 2. Ir em https://share.streamlit.io
# 3. Conectar repositório

# Ou em servidor privado:
streamlit run app.py --server.port 80 --server.headless true
```

## 🔟 Recursos Úteis

- 📖 [LangChain Docs](https://python.langchain.com/)
- 📖 [Streamlit Docs](https://docs.streamlit.io/)
- 📄 [BCB RSS Feed](https://www.bcb.gov.br/htms/novidades/ult_noticias.xml)
- 🎯 [Proposta Original](file:///home/rotsen/Downloads/proposta_projeto_risco_regulatorio_prosa.pdf)

---

## ⚠️ Checklist de Implementação

- [ ] Coleta BCB implementada
- [ ] Coleta CVM implementada
- [ ] Extração de datas funcionando
- [ ] Extração de obrigações funcionando
- [ ] LLM integrado para análise
- [ ] Banco de dados criado e funcionando
- [ ] Corpus de teste anotado (~30-50 docs)
- [ ] Métricas calculadas
- [ ] Interface Streamlit funcional
- [ ] Documentação atualizada
- [ ] Testes passando
- [ ] Pronto para apresentação

---

**Você está pronto para começar! 🚀**

Próximo passo recomendado: Implemente `_fetch_bcb_documents()` para começar a coletar documentos reais.

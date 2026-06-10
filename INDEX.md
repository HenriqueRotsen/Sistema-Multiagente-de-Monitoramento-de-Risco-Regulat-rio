# Índice do Projeto

## Documentação

| Arquivo | Quando ler |
|---------|------------|
| [README.md](README.md) | Visão geral do projeto e status atual |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Configuração, execução e testes |
| [TODO.md](TODO.md) | Pendências e próximos passos |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Resumo técnico do que foi implementado |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitetura detalhada original |
| [PROJECT_STATUS.txt](PROJECT_STATUS.txt) | Status visual resumido |

## Código Principal

| Arquivo | Status | Descrição |
|---------|--------|-----------|
| [main.py](main.py) | Funcional | Orquestra coleta, análise e alertas |
| [app.py](app.py) | Parcial | Interface Streamlit básica |
| [src/agents/monitor_agent.py](src/agents/monitor_agent.py) | Funcional para BCB | Coleta BCB, deduplica e faz triagem |
| [src/agents/analysis_agent.py](src/agents/analysis_agent.py) | Funcional | Usa LLM ou fallback heurístico |
| [src/agents/alert_agent.py](src/agents/alert_agent.py) | Funcional | Gera alertas com resumo, impacto e recomendações |
| [src/utils/llm_integration.py](src/utils/llm_integration.py) | Funcional | Cliente Ollama/OpenAI-compatible |
| [src/utils/data_collection.py](src/utils/data_collection.py) | Parcial | Utilitários e repositório ainda em esqueleto |

## Testes

| Arquivo | Cobre |
|---------|-------|
| [tests/test_monitor_agent.py](tests/test_monitor_agent.py) | Coleta BCB, RSS mockado, deduplicação e triagem |
| [tests/test_analysis_agent.py](tests/test_analysis_agent.py) | Análise com mock de LLM e fallback |
| [tests/test_llm_integration.py](tests/test_llm_integration.py) | Cliente Ollama e parsing JSON |
| [tests/test_alert_agent.py](tests/test_alert_agent.py) | Resumo, impacto, recomendações e prioridade |

Comando:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v
```

## Configuração

| Arquivo | Uso |
|---------|-----|
| [.env.example](.env.example) | Template de variáveis de ambiente |
| [.gitignore](.gitignore) | Garante que `.env` e caches não sejam versionados |
| [requirements.txt](requirements.txt) | Dependências Python |
| [QUICK_START.sh](QUICK_START.sh) | Script legado de início rápido |

## Fluxo Atual

```text
main.py
├── MonitorAgent
│   └── coleta BCB via API pública atual
├── AnalysisAgent
│   ├── RegulatoryLLM se .env estiver configurado
│   └── fallback heurístico se LLM falhar
└── AlertAgent
    └── alerta com resumo, impacto, obrigações e recomendações
```

## Comandos Mais Usados

Instalar:

```bash
pip install -r requirements.txt
```

Testar:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v
```

Rodar pipeline real:

```bash
python3 main.py
```

Rodar interface:

```bash
streamlit run app.py
```

Smoke test com LLM:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c "from main import RegulatoryMonitoringSystem; system=RegulatoryMonitoringSystem(); system.run_monitoring_cycle(manual_documents=[{'id':'teste','title':'Circular de Teste','source':'BCB','document_type':'Circular','url':'https://example.com','content':'O Banco Central determina que as instituições de pagamento deverão atualizar controles antifraude até 30/06/2026.'}])"
```

## Tarefas por Prioridade

### Alta

1. Criar persistência SQLite.
2. Persistir documentos, extrações e alertas.
3. Conectar Streamlit aos dados persistidos.

### Média

1. Implementar coleta CVM.
2. Adicionar retry/backoff e cache de análises.
3. Criar export CSV.

### Pesquisa/Avaliação

1. Criar corpus anotado.
2. Medir precisão, recall, F1 e acurácia de campos.
3. Comparar modelos LLM.

## Status Resumido

| Área | Status |
|------|--------|
| Coleta BCB | Implementada |
| Coleta CVM | Pendente |
| LLM Ollama | Implementado |
| OpenAI-compatible | Implementado |
| Fallback sem LLM | Implementado |
| Alertas estruturados | Implementado |
| Banco de dados | Pendente |
| Corpus anotado | Pendente |
| Métricas | Pendente |

---

**Versão:** 0.2.0  
**Atualizado em:** 10 de junho de 2026

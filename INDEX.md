# Índice do Projeto

## Documentação

| Arquivo | Quando ler |
|---------|------------|
| [README.md](README.md) | Visão geral do projeto e status atual |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Configuração, execução e testes |
| [TODO.md](TODO.md) | Pendências e próximos passos |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Resumo técnico do que foi implementado |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitetura técnica atualizada do sistema |
| [EVALUATION_METHODOLOGY.md](EVALUATION_METHODOLOGY.md) | Corpus, métricas e protocolo de avaliação |
| [PROJECT_STATUS.txt](PROJECT_STATUS.txt) | Status visual resumido |

## Código Principal

| Arquivo | Status | Descrição |
|---------|--------|-----------|
| [main.py](main.py) | Funcional | Orquestra coleta, análise e alertas |
| [app.py](app.py) | Funcional | Interface com filtros, histórico e exportações |
| [src/agents/monitor_agent.py](src/agents/monitor_agent.py) | Funcional | Coleta BCB/CVM, deduplica e faz triagem |
| [src/agents/analysis_agent.py](src/agents/analysis_agent.py) | Funcional | Usa LLM ou fallback heurístico |
| [src/agents/alert_agent.py](src/agents/alert_agent.py) | Funcional | Gera alertas e exporta JSON/CSV/HTML/PDF |
| [src/utils/llm_integration.py](src/utils/llm_integration.py) | Funcional | Cliente Ollama/OpenAI-compatible |
| [src/utils/data_collection.py](src/utils/data_collection.py) | Funcional | Repositório SQLite e histórico de ciclos |

## Testes

| Arquivo | Cobre |
|---------|-------|
| [tests/test_monitor_agent.py](tests/test_monitor_agent.py) | Coleta BCB, RSS mockado, deduplicação e triagem |
| [tests/test_analysis_agent.py](tests/test_analysis_agent.py) | Análise com mock de LLM e fallback |
| [tests/test_llm_integration.py](tests/test_llm_integration.py) | Cliente Ollama e parsing JSON |
| [tests/test_alert_agent.py](tests/test_alert_agent.py) | Resumo, impacto, recomendações e prioridade |
| [tests/test_document_repository.py](tests/test_document_repository.py) | Persistência e histórico de ciclos |
| [tests/test_evaluation.py](tests/test_evaluation.py) | Métricas de avaliação |

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
│   └── coleta BCB/CVM + deduplicação persistida
├── AnalysisAgent
│   ├── RegulatoryLLM se .env estiver configurado
│   └── fallback heurístico + cache por hash
└── AlertAgent
    └── alerta + exportações + relatório por ciclo
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

## Focos Recomendados

1. Revisão manual do corpus anotado seed para gold set.
2. Reexecução da comparação de modelos em janela de estabilidade do endpoint.
3. Consolidação do relatório técnico final para entrega.

## Status Resumido

| Área | Status |
|------|--------|
| Coleta BCB | Implementada |
| Coleta CVM | Implementada |
| LLM Ollama | Implementado |
| OpenAI-compatible | Implementado |
| Fallback sem LLM | Implementado |
| Alertas estruturados | Implementado |
| Banco de dados | Implementado |
| Corpus anotado (seed) | Implementado |
| Métricas | Implementadas |

---

**Versão:** 0.8.0  
**Atualizado em:** 26 de junho de 2026

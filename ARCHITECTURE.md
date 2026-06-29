# Arquitetura do Sistema Multiagente

Este documento descreve a arquitetura implementada no projeto após integração de coleta BCB/CVM, persistência SQLite, avaliação de qualidade, robustez operacional e interface Streamlit com histórico e exportação.

## Visão Geral Atual

```text
Fontes Regulatórias
  - BCB API pública (notícias regulatórias)
  - RSS/XML legado opcional (BCB)
  - CVM (legislação com paginação)
        |
        v
Monitor Agent
  - coleta por fonte
  - normaliza em RegulatoryDocument
  - filtra tipos regulatórios
  - aplica deduplicação em memória + banco
  - retry/backoff + timeout por fonte
        |
        v
Analysis Agent
  - usa LLM (Ollama/OpenAI-compatible) se disponível
  - fallback heurístico em erro/ausência
  - extrai resumo, datas, obrigações, atividades, impacto
  - cache de análise por hash de conteúdo
        |
        v
Alert Agent
  - cria StructuredAlert
  - prioriza por prazo/impacto
  - exporta JSON/CSV/HTML/PDF
  - gera relatório consolidado por ciclo (JSON/HTML/PDF)
        |
        v
Persistência (SQLite)
  - documents
  - extractions
  - alerts
  - monitoring_cycles
        |
        v
Interface Streamlit / Console / Revisão Humana
  - dashboard com métricas e histórico de ciclos
  - filtros por prioridade, regulador, atividade e revisão
  - marcação de revisão persistida
  - downloads de alertas e relatório de ciclo
```

## Componentes

### 1. Monitor Agent

Arquivo: `src/agents/monitor_agent.py`

Responsabilidades:

- Coleta BCB por API pública atual.
- Suporte opcional a RSS/XML legado.
- Coleta CVM por listagem oficial de legislação com paginação.
- Normalização para `RegulatoryDocument`.
- Filtro de conteúdo regulatório e deduplicação.
- Retry/backoff e timeout configurável por fonte.

Configurações relevantes:

- `BCB_NEWS_API_URL`
- `BCB_HISTORY_LIMIT` (padrão: `200`)
- `CVM_LEGISLATION_URL`
- `CVM_MAX_PAGES` (padrão: `20`)
- `BCB_TIMEOUT_SECONDS`
- `CVM_TIMEOUT_SECONDS`
- `SOURCE_RETRY_ATTEMPTS`
- `SOURCE_RETRY_BACKOFF_SECONDS`

### 2. Analysis Agent

Arquivo: `src/agents/analysis_agent.py`

Responsabilidades:

- Recebe texto + metadados de documento.
- Realiza extração estruturada em dois modos:
  - `llm`: via `RegulatoryLLM`;
  - `regex`: fallback heurístico local.
- Extrai:
  - resumo;
  - datas de vigência/prazo;
  - obrigações;
  - atividades e entidades afetadas;
  - impacto e recomendações.

### 3. LLM Integration

Arquivo: `src/utils/llm_integration.py`

Responsabilidades:

- Cliente para provedores:
  - `ollama` (`/api/chat`, `X-API-Key`);
  - `openai` (`/chat/completions`).
- Retry/backoff em chamadas HTTP.
- Rate limiting local por requisição.
- Normalização de saída JSON para schema estável.

Configurações relevantes:

- `LLM_PROVIDER`
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_API_KEY_HEADER`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `LLM_MAX_TOKENS`
- `LLM_TEMPERATURE`
- `LLM_MAX_RETRIES`
- `LLM_RETRY_BACKOFF_SECONDS`
- `LLM_RATE_LIMIT_PER_MINUTE`

### 4. Alert Agent

Arquivo: `src/agents/alert_agent.py`

Responsabilidades:

- Construção de `StructuredAlert` por documento analisado.
- Priorização (`CRÍTICO`, `ALTO`, `MÉDIO`, `BAIXO`).
- Formatação para triagem humana.
- Exportação:
  - alertas: `json`, `csv`, `html`, `pdf`;
  - ciclo consolidado: `json`, `html`, `pdf`.

### 5. Repositório e Persistência

Arquivo: `src/utils/data_collection.py` (`DocumentRepository`)

Banco SQLite:

- `documents`: documentos coletados e status.
- `extractions`: extrações estruturadas por documento.
- `alerts`: alertas e revisão humana.
- `monitoring_cycles`: histórico resumido de execução.

Capacidades:

- deduplicação persistida;
- cache por hash de conteúdo;
- estatísticas operacionais;
- recuperação de histórico para interface.

### 6. Orquestrador

Arquivo: `main.py`

Pipeline por ciclo:

1. coleta e persistência de documentos;
2. análise (com cache por hash);
3. geração e persistência de alertas;
4. persistência de resumo do ciclo em `monitoring_cycles`.

Extras:

- suporte a `--limit N` para ciclos menores;
- worker contínuo com `--watch` e intervalo configurável por CLI ou
  `MONITOR_INTERVAL_SECONDS`;
- logging em console e opcional em arquivo (`LOG_FILE`).

### 7. Interface Streamlit

Arquivo: `app.py`

Funcionalidades:

- Dashboard com métricas de alertas e histórico de ciclos.
- Filtros funcionais de alertas:
  - regulador;
  - prioridade;
  - atividade afetada;
  - status de revisão;
  - confiança mínima.
- Marcação de revisão persistida.
- Download de alertas e relatório de ciclo em múltiplos formatos.
- Atualização periódica do dashboard e dos alertas via fragmentos Streamlit.

### 8. Execução em containers

- Uma imagem multi-stage e não-root é compartilhada pelos serviços `worker` e `web`.
- O Compose mantém os processos isolados e compartilha apenas o volume SQLite.
- O worker executa `main.py --watch`; a interface expõe a porta `8501` e possui healthcheck.

## Modelo de Dados (Resumo)

### RegulatoryDocument

- id, título, fonte, tipo documental, data, URL, conteúdo, metadados.

### ExtractedInfo

- resumo, datas, obrigações, atividades afetadas, impacto, recomendações, confiança, método de extração.

### StructuredAlert

- identificador, metadados do documento, prioridade, resumo/impacto, obrigações, prazo, confiança, revisão humana.

## Fluxo de Avaliação de Qualidade

Arquivos:

- `scripts/build_annotated_corpus.py`
- `scripts/evaluate_analysis_quality.py`
- `src/utils/evaluation.py`

Etapas:

1. gerar corpus anotado inicial (seed);
2. executar baseline heurístico;
3. comparar modelos LLM configurados;
4. registrar relatório em `reports/quality/`.

## Governança

- O sistema não substitui análise jurídica.
- Todo alerta exige validação humana.
- Confiança é sinal auxiliar e não decisão automática.
- Rastreabilidade da fonte é preservada.

---

**Versão documentada:** 0.8.0  
**Atualizado em:** 2026-06-26  
**Status:** Pipeline funcional com coleta BCB/CVM, persistência, interface avançada e avaliação inicial de qualidade.

# TODO - Sistema de Monitoramento de Risco Regulatório

Este checklist reflete o estado atual do projeto após a coleta real do BCB e a integração com LLM via proxy Ollama da disciplina.

## Concluído

### 1. Monitor Agent - BCB
- [x] Implementar `_fetch_bcb_documents()`
  - [x] Coleta pela API pública atual do BCB: `/api/servico/sitebcb/noticias`
  - [x] Suporte opcional a RSS/XML legado quando configurado manualmente
  - [x] Normalização para `RegulatoryDocument`
  - [x] Extração de título, data, URL, conteúdo e metadados
  - [x] Detecção heurística de tipo documental: Resolução, Circular, Comunicado, Consulta Pública etc.
- [x] Deduplicação por título, fonte e data
- [x] Triagem inicial de documentos regulatórios

### 2. Analysis Agent
- [x] Integrar `AnalysisAgent` ao pipeline real em `main.py`
- [x] Criar cliente LLM em `src/utils/llm_integration.py`
- [x] Suportar proxy Ollama da disciplina:
  - [x] `POST /api/chat`
  - [x] header `X-API-Key`
  - [x] modelos configuráveis via `.env`
- [x] Suportar servidores OpenAI-compatible:
  - [x] `POST /chat/completions`
  - [x] bearer token opcional
- [x] Prompt estruturado para JSON com:
  - [x] resumo
  - [x] datas
  - [x] atividades afetadas
  - [x] entidades afetadas
  - [x] obrigações
  - [x] recomendações
  - [x] impacto
  - [x] confiança
- [x] Fallback heurístico sem LLM:
  - [x] resumo simples
  - [x] datas contextuais
  - [x] obrigações por verbos modais
  - [x] keywords setoriais
  - [x] impacto básico
  - [x] recomendações básicas

### 3. Alert Agent
- [x] Usar resumo produzido pelo LLM/fallback
- [x] Exibir avaliação de impacto
- [x] Exibir recomendações
- [x] Preservar texto longo em obrigações/recomendações com quebra de linha
- [x] Corrigir IDs repetidos de alertas
- [x] Evitar prioridade crítica automática para prazos vencidos
- [x] Export JSON

### 4. Configuração e Segurança
- [x] Atualizar `.env.example` para Ollama/proxy da disciplina
- [x] Adicionar `.gitignore`
- [x] Ignorar `.env` para proteger a chave da API

### 5. Testes
- [x] Testes do `MonitorAgent`
- [x] Testes do `AnalysisAgent`
- [x] Testes do cliente LLM
- [x] Testes do `AlertAgent`
- [x] Descoberta padrão com `unittest discover`

## Pendências Estratégicas

### 1. Coleta CVM
- [x] Implementar `_fetch_cvm_documents()`
  - [x] Escolher fonte oficial estável da CVM
  - [x] Coletar resoluções, deliberações, instruções, ofícios e comunicados
  - [x] Normalizar metadados para `RegulatoryDocument`
  - [x] Tratar paginação
  - [x] Criar testes com mocks

### 2. Persistência
- [x] Criar `database/schema.sql`
- [x] Implementar `DocumentRepository`
  - [x] `add_document()`
  - [x] `check_duplicate()`
  - [x] `get_processed_documents()`
  - [x] `update_processing_status()`
  - [x] `get_statistics()`
- [x] Salvar documentos coletados
- [x] Salvar extrações do LLM/fallback
- [x] Salvar alertas e status de revisão humana

### 3. Interface Streamlit
- [x] Conectar dashboard a dados persistidos
- [x] Exibir resumo, impacto e recomendações do LLM nos cards de alerta
- [x] Implementar filtros funcionais por:
  - [x] regulador
  - [x] prioridade
  - [x] atividade afetada
  - [x] status de revisão
- [x] Persistir marcação de alerta revisado
- [x] Mostrar histórico de ciclos
- [x] Exportar CSV além de JSON

### 4. Qualidade da Análise
- [x] Criar corpus anotado com 30-50 documentos reais
- [x] Anotar campos de referência (seed inicial para revisão humana):
  - [x] relevância
  - [x] datas de vigência
  - [x] prazos
  - [x] obrigações
  - [x] atividades afetadas
  - [x] impacto
- [x] Calcular métricas:
  - [x] precisão, recall e F1 para relevância
  - [x] acurácia de datas
  - [x] acurácia de obrigações
  - [x] erro médio de prazo em dias
- [x] Comparar modelos:
  - [x] `llama3.2:3b`
  - [x] `deepseek-r1:8b`
  - [x] outro modelo disponível, se útil

### 5. Robustez Operacional
- [x] Retry com backoff para BCB, CVM e LLM
- [x] Timeout configurável por fonte
- [x] Rate limiting para chamadas LLM
- [x] Cache de análises por hash de conteúdo
- [x] Logging em arquivo via `LOG_FILE`
- [x] Modo `--limit N` para testar poucos documentos reais

### 6. Exportação e Relatórios
- [x] JSON
- [x] CSV
- [x] HTML
- [x] PDF
- [x] Relatório consolidado por ciclo

### 7. Documentação
- [x] README alinhado ao estado atual
- [x] Guia de início atualizado
- [x] TODO atualizado
- [x] Status/índice atualizados
- [x] Atualizar diagramas detalhados em `ARCHITECTURE.md`
- [x] Documentar corpus e metodologia de avaliação quando existirem

## Próximo Passo Recomendado

**Consolidar a qualidade da avaliação com revisão humana do corpus seed.**

Motivo: o pipeline técnico está funcional, mas a validação acadêmica final depende de um gold set anotado manualmente para reduzir viés de autoanotação.

Ordem sugerida:

1. Revisar manualmente `data/corpus/annotated_corpus.jsonl`.
2. Congelar uma versão de corpus para benchmark.
3. Reexecutar comparação de modelos em janela estável do endpoint LLM.
4. Consolidar relatório final de resultados.

## Comandos Úteis

Rodar testes:

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

Teste rápido com documento manual e LLM:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c "from main import RegulatoryMonitoringSystem; system=RegulatoryMonitoringSystem(); system.run_monitoring_cycle(manual_documents=[{'id':'teste','title':'Circular de Teste','source':'BCB','document_type':'Circular','url':'https://example.com','content':'O Banco Central determina que as instituições de pagamento deverão atualizar controles antifraude até 30/06/2026.'}])"
```

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

## Pendente

### 1. Coleta CVM
- [ ] Implementar `_fetch_cvm_documents()`
  - [ ] Escolher fonte oficial estável da CVM
  - [ ] Coletar resoluções, deliberações, instruções, ofícios e comunicados
  - [ ] Normalizar metadados para `RegulatoryDocument`
  - [ ] Tratar paginação
  - [ ] Criar testes com mocks

### 2. Persistência
- [ ] Criar `database/schema.sql`
- [ ] Implementar `DocumentRepository`
  - [ ] `add_document()`
  - [ ] `check_duplicate()`
  - [ ] `get_processed_documents()`
  - [ ] `update_processing_status()`
  - [ ] `get_statistics()`
- [ ] Salvar documentos coletados
- [ ] Salvar extrações do LLM/fallback
- [ ] Salvar alertas e status de revisão humana

### 3. Interface Streamlit
- [ ] Conectar dashboard a dados persistidos
- [ ] Exibir resumo, impacto e recomendações do LLM nos cards de alerta
- [ ] Implementar filtros funcionais por:
  - [ ] regulador
  - [ ] prioridade
  - [ ] atividade afetada
  - [ ] status de revisão
- [ ] Persistir marcação de alerta revisado
- [ ] Mostrar histórico de ciclos
- [ ] Exportar CSV além de JSON

### 4. Qualidade da Análise
- [ ] Criar corpus anotado com 30-50 documentos reais
- [ ] Anotar manualmente:
  - [ ] relevância
  - [ ] datas de vigência
  - [ ] prazos
  - [ ] obrigações
  - [ ] atividades afetadas
  - [ ] impacto
- [ ] Calcular métricas:
  - [ ] precisão, recall e F1 para relevância
  - [ ] acurácia de datas
  - [ ] acurácia de obrigações
  - [ ] erro médio de prazo em dias
- [ ] Comparar modelos:
  - [ ] `llama3.2:3b`
  - [ ] `deepseek-r1:8b`
  - [ ] outro modelo disponível, se útil

### 5. Robustez Operacional
- [ ] Retry com backoff para BCB, CVM e LLM
- [ ] Timeout configurável por fonte
- [ ] Rate limiting para chamadas LLM
- [ ] Cache de análises por hash de conteúdo
- [ ] Logging em arquivo via `LOG_FILE`
- [ ] Modo `--limit N` para testar poucos documentos reais

### 6. Exportação e Relatórios
- [x] JSON
- [ ] CSV
- [ ] HTML
- [ ] PDF
- [ ] Relatório consolidado por ciclo

### 7. Documentação
- [x] README alinhado ao estado atual
- [x] Guia de início atualizado
- [x] TODO atualizado
- [x] Status/índice atualizados
- [ ] Atualizar diagramas detalhados em `ARCHITECTURE.md`
- [ ] Documentar corpus e metodologia de avaliação quando existirem

## Próximo Passo Recomendado

**Implementar persistência mínima em SQLite antes de expandir para CVM.**

Motivo: sem histórico persistido, o sistema reprocessa os mesmos documentos a cada execução e a interface não consegue mostrar revisão, histórico ou métricas de uso de forma confiável.

Ordem sugerida:

1. Criar `database/schema.sql`.
2. Implementar `DocumentRepository` em `src/utils/data_collection.py`.
3. Fazer `MonitorAgent` consultar duplicatas no repositório.
4. Salvar alertas gerados.
5. Atualizar Streamlit para ler alertas persistidos.

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

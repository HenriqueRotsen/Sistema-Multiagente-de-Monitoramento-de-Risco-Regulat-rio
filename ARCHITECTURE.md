# Arquitetura do Sistema Multiagente

Este documento descreve o estado atual do sistema. O prototipo ja executa um ciclo completo para publicacoes do Banco Central do Brasil, com analise por LLM quando configurado e fallback heuristico quando o LLM nao estiver disponivel.

## Visao Geral

```text
Fontes regulatorias
  - BCB API publica atual
  - RSS/XML legado opcional
  - CVM pendente
        |
        v
Monitor Agent
  - coleta publicacoes
  - normaliza metadados
  - filtra itens regulatorios
  - remove duplicatas em memoria
        |
        v
Analysis Agent
  - chama LLM configurado
  - aplica fallback heuristico em caso de falha
  - extrai resumo, datas, entidades, obrigacoes, impacto e recomendacoes
        |
        v
Alert Agent
  - calcula prioridade
  - consolida resumo e impacto
  - formata alerta para triagem humana
  - exporta JSON
        |
        v
Console / Streamlit / Validacao humana
```

## Componentes

### Monitor Agent

Arquivo: `src/agents/monitor_agent.py`

Responsabilidades atuais:

- Coletar publicacoes do BCB pela API `https://www.bcb.gov.br/api/servico/sitebcb/noticias`.
- Aceitar RSS/XML legado quando `BCB_RSS_URL` ou uma URL `.xml` for configurada.
- Limpar HTML e normalizar campos para `RegulatoryDocument`.
- Detectar atos normativos por titulo e resumo.
- Deduplicar documentos por titulo, fonte e data.

Pendencias:

- Persistir documentos processados em banco para evitar reprocessamento entre execucoes.
- Implementar coleta real da CVM.
- Baixar e processar documentos anexos quando a publicacao apontar para PDF ou pagina normativa detalhada.

### Analysis Agent

Arquivo: `src/agents/analysis_agent.py`

Responsabilidades atuais:

- Receber texto e metadados do documento.
- Usar `RegulatoryLLM` quando configurado.
- Solicitar JSON estruturado ao LLM com resumo, datas, atividades afetadas, entidades, obrigacoes, recomendacoes, palavras-chave, impacto e confiancas.
- Aplicar fallback heuristico local para resumo, datas contextuais, obrigacoes, entidades, palavras-chave, impacto e recomendacoes.

Modos de extracao:

- `llm`: resposta estruturada vinda do modelo.
- `regex`: fallback local baseado em regras simples.

Pendencias:

- Melhorar validacao do JSON retornado pelo LLM.
- Criar corpus anotado para medir qualidade das extracoes.
- Adicionar recuperacao semantica/embeddings se o projeto crescer para documentos longos.

### Alert Agent

Arquivo: `src/agents/alert_agent.py`

Responsabilidades atuais:

- Gerar `StructuredAlert` a partir de `ExtractedInfo`.
- Definir prioridade por prazo e impacto.
- Usar resumo, impacto e recomendacoes produzidos pela analise.
- Formatar alerta legivel no console.
- Exportar alertas em JSON.

Pendencias:

- Exportar CSV, HTML e PDF.
- Persistir revisao humana.
- Criar canal de notificacao, como email, somente depois de existir revisao e historico.

### LLM Integration

Arquivo: `src/utils/llm_integration.py`

Responsabilidades atuais:

- Ler configuracao por variaveis de ambiente.
- Suportar provider `ollama` via `/api/chat`.
- Suportar provider `openai` via `/chat/completions`.
- Enviar `X-API-Key` para o proxy Ollama da disciplina quando configurado.
- Retornar JSON validado minimamente para o `AnalysisAgent`.

Variaveis principais:

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=https://ollama.futurelab.dcc.ufmg.br
LLM_API_KEY=sua_chave
LLM_API_KEY_HEADER=X-API-Key
LLM_MODEL=llama3.2:3b
LLM_TIMEOUT_SECONDS=60
LLM_MAX_TOKENS=1200
LLM_TEMPERATURE=0.1
```

### Interface Streamlit

Arquivo: `app.py`

Responsabilidades atuais:

- Mostrar dashboard basico.
- Executar ciclo de monitoramento.
- Exibir alertas.
- Exportar JSON.

Pendencias:

- Conectar filtros a dados persistidos.
- Exibir historico real.
- Registrar revisao humana.

## Estruturas De Dados

### RegulatoryDocument

```python
{
    "id": "bcb-...",
    "title": "Resolucao BCB ...",
    "source": "BCB",
    "document_type": "Resolucao",
    "published_date": datetime(...),
    "url": "https://www.bcb.gov.br/detalhenoticia/...",
    "content": "Texto limpo da publicacao",
    "metadata": {
        "feed_url": "...",
        "raw_id": "...",
        "collected_at": "...",
        "published_raw": "..."
    },
    "processed": False,
    "relevance_score": 0.0
}
```

### ExtractedInfo

```python
{
    "document_id": "bcb-...",
    "regulatory_body": "BCB",
    "document_type": "Resolucao",
    "title": "...",
    "summary": "...",
    "effective_date": datetime(...),
    "implementation_deadline": datetime(...),
    "affected_activities": ["Pix", "Autenticacao e seguranca"],
    "affected_entities": ["instituicoes de pagamento"],
    "obligations": ["..."],
    "keywords": ["pix", "seguranca"],
    "recommendations": ["..."],
    "impact_score": 0.75,
    "impact_description": "...",
    "impact_areas": ["Compliance", "Tecnologia"],
    "confidence_scores": {
        "summary": 0.8,
        "dates": 0.7,
        "obligations": 0.7,
        "impact": 0.7
    },
    "extraction_method": "llm"
}
```

### StructuredAlert

```python
{
    "alert_id": "ALR-20260610120000123456",
    "created_at": "2026-06-10T12:00:00",
    "regulatory_body": "BCB",
    "document_title": "...",
    "document_type": "Resolucao",
    "source_url": "https://...",
    "summary": "...",
    "priority": "ALTO",
    "affected_activities": ["..."],
    "obligations": ["..."],
    "effective_date": "2026-01-01T00:00:00",
    "implementation_deadline": "2026-06-30T00:00:00",
    "days_until_deadline": 20,
    "confidence_level": "MEDIA",
    "impact_assessment": "...",
    "recommendations": ["..."],
    "human_reviewed": false
}
```

## Fluxo De Execucao

1. `main.py` carrega `.env`, se `python-dotenv` estiver instalado.
2. `RegulatoryLLM.from_env()` tenta montar o cliente de LLM.
3. `MonitorAgent.monitor_sources()` coleta publicacoes reais do BCB.
4. `MonitorAgent.initial_screening()` mantem itens com sinais regulatorios.
5. `AnalysisAgent.analyze_document()` chama o LLM ou usa fallback.
6. `AlertAgent.batch_generate_alerts()` cria e prioriza alertas.
7. Os alertas sao exibidos no console e podem ser exportados em JSON.

## Proximo Passo Tecnico

A proxima melhoria recomendada e implementar persistencia SQLite:

```text
database/schema.sql
src/utils/data_collection.py ou novo repository.py

tables:
  documents
  analyses
  alerts
  reviews
```

Isso resolve tres lacunas importantes:

- evita reprocessamento dos mesmos documentos;
- permite historico na interface;
- abre caminho para revisao humana persistente e metricas.

## Governanca

- O sistema nao substitui analise juridica.
- Todo alerta deve passar por revisao humana.
- O LLM pode errar ou inferir campos ausentes.
- A URL da fonte e preservada para rastreabilidade.
- A pontuacao de confianca e apenas um sinal auxiliar.

---

**Versao documentada:** 0.2.0  
**Atualizado em:** 2026-06-10  
**Status:** Prototipo funcional com BCB + LLM + fallback heuristico.

# 🏗️ Arquitetura do Sistema Multiagente

## Visão Geral

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SOURCES (REGULATÓRIAS)                           │
│        ┌──────────────────┐           ┌──────────────────┐         │
│        │   Banco Central  │           │       CVM        │         │
│        │    RSS + Web     │           │    Web Portal    │         │
│        └─────────┬────────┘           └────────┬─────────┘         │
└────────────────────┼──────────────────────────────────┼─────────────┘
                     │                                   │
                     └───────────────────┬───────────────┘
                                         │
                    ┌────────────────────▼─────────────────┐
                    │  📥 MONITOR AGENT                    │
                    │  • Coleta documentos                 │
                    │  • Elimina duplicatas                │
                    │  • Triagem inicial                   │
                    └────────────────────┬─────────────────┘
                                         │
                    ┌────────────────────▼─────────────────┐
                    │  📊 ANALYSIS AGENT                   │
                    │  • Extrai informações                │
                    │  • Estima impacto                    │
                    │  • Identifica obrigações             │
                    └────────────────────┬─────────────────┘
                                         │
                    ┌────────────────────▼─────────────────┐
                    │  🔔 ALERT AGENT                      │
                    │  • Prioriza alertas                  │
                    │  • Estrutura saída                   │
                    │  • Formata para triagem              │
                    └────────────────────┬─────────────────┘
                                         │
                    ┌────────────────────▼─────────────────┐
                    │  ✋ VALIDAÇÃO HUMANA                 │
                    │  • Revisão especialista              │
                    │  • Sem automação crítica             │
                    └────────────────────┬─────────────────┘
                                         │
                    ┌────────────────────▼─────────────────┐
                    │  📈 OUTPUTS                          │
                    │  • Interface Streamlit               │
                    │  • JSON/CSV/PDF                      │
                    │  • Email alerts (TODO)               │
                    └────────────────────────────────────────┘
```

## Componentes Detalhados

### 1. Monitor Agent 🔍
**Responsabilidade:** Coleta e triagem inicial

```
┌─────────────────────────────────────────┐
│      MONITOR AGENT                      │
├─────────────────────────────────────────┤
│                                         │
│  monitor_sources()                      │
│    ├─ fetch_from_source("BCB")         │
│    │   ├─ Parsear RSS                  │
│    │   ├─ Normalizar tipos             │
│    │   └─ Extrair metadata             │
│    │                                    │
│    └─ fetch_from_source("CVM")         │
│        ├─ Web scraping                 │
│        ├─ Normalizar tipos             │
│        └─ Extrair metadata             │
│                                         │
│  eliminate_duplicates()                 │
│    └─ Hash-based dedup                 │
│                                         │
│  initial_screening()                    │
│    ├─ Filtrar por tipo                 │
│    ├─ Validar estrutura                │
│    └─ Validar keywords                 │
│                                         │
└─────────────────────────────────────────┘
         ↓ RegulatoryDocument[]
```

**Entrada:** URLs de fontes
**Saída:** Lista de RegulatoryDocument

### 2. Analysis Agent 📊
**Responsabilidade:** Extração de informações estruturadas

```
┌─────────────────────────────────────────┐
│      ANALYSIS AGENT                     │
├─────────────────────────────────────────┤
│                                         │
│  analyze_document(text, metadata)       │
│    ├─ _extract_summary()                │
│    │   └─ [LLM] Sumarização             │
│    │                                    │
│    ├─ _extract_dates()                  │
│    │   └─ [Regex + NLP] Datas           │
│    │                                    │
│    ├─ _extract_obligations()            │
│    │   └─ [NER] Obrigações              │
│    │                                    │
│    ├─ _extract_entities()               │
│    │   └─ [NER] Entidades afetadas      │
│    │                                    │
│    ├─ _extract_keywords()               │
│    │   └─ [TF-IDF/BERTopic] Keywords   │
│    │                                    │
│    └─ _estimate_impact()                │
│        └─ [Rules + ML] Impact score     │
│                                         │
│  batch_analyze(documents)               │
│    └─ Processa múltiplos em paralelo   │
│                                         │
│  filter_by_relevance(threshold)         │
│    └─ Filtra por score de impacto      │
│                                         │
└─────────────────────────────────────────┘
         ↓ ExtractedInfo[]
```

**Entrada:** RegulatoryDocument[]
**Saída:** ExtractedInfo[] (informações estruturadas)

### 3. Alert Agent 🔔
**Responsabilidade:** Geração e priorização de alertas

```
┌─────────────────────────────────────────┐
│      ALERT AGENT                        │
├─────────────────────────────────────────┤
│                                         │
│  generate_alert(extracted_info)         │
│    ├─ _determine_priority()             │
│    │   └─ CRÍTICO/ALTO/MÉDIO/BAIXO     │
│    │                                    │
│    ├─ _generate_summary()               │
│    │   └─ Template-based formatting     │
│    │                                    │
│    ├─ _assess_confidence()              │
│    │   └─ ALTA/MÉDIA/BAIXA             │
│    │                                    │
│    ├─ _generate_recommendations()       │
│    │   └─ Ações iniciais                │
│    │                                    │
│    └─ Retorna StructuredAlert           │
│                                         │
│  prioritize_alerts(alerts)              │
│    └─ Ordena por urgência               │
│                                         │
│  format_for_display(alert)              │
│    ├─ Formatação visual                │
│    ├─ Markdown/ASCII                    │
│    └─ Para terminal/web                │
│                                         │
│  export_alerts(format)                  │
│    ├─ JSON                              │
│    ├─ CSV                               │
│    ├─ PDF (TODO)                        │
│    └─ HTML (TODO)                       │
│                                         │
└─────────────────────────────────────────┘
         ↓ StructuredAlert[]
```

**Entrada:** ExtractedInfo[]
**Saída:** StructuredAlert[] (estruturados e priorizados)

## Fluxo de Dados

```
┌───────────────┐
│  Fonte: BCB   │
│  Fonte: CVM   │
└───────┬───────┘
        │
        ▼ RawDocument
┌──────────────────┐
│  Monitor Agent   │─── Coleta
│  (monitor_agent) │───✓ Remove duplicatas
│                  │───✓ Triagem inicial
└───────┬──────────┘
        │
        ▼ RegulatoryDocument
┌──────────────────┐
│ Analysis Agent   │─── Extrai
│ (analysis_agent) │───✓ Datas
│                  │───✓ Obrigações
│                  │───✓ Impacto
└────────┬─────────┘
         │
         ▼ ExtractedInfo
┌──────────────────┐
│  Alert Agent     │─── Prioriza
│  (alert_agent)   │───✓ Formata
│                  │───✓ Estrutura
└────────┬─────────┘
         │
         ▼ StructuredAlert
┌──────────────────────────┐
│  Validação Humana        │ ◄─── REQUER REVISÃO
│  (sem automação)         │
└────────┬─────────────────┘
         │
         ▼ ValidatedAlert
┌──────────────────────────┐
│  Outputs                 │
│ • Streamlit Dashboard    │
│ • JSON Export            │
│ • Email (TODO)           │
│ • Banco de Dados         │
└──────────────────────────┘
```

## Estruturas de Dados

### RegulatoryDocument
```python
{
    "id": "doc_001",
    "title": "Circular 3.961 - Autenticação de Usuários",
    "source": "BCB",
    "document_type": "Circular",
    "published_date": "2024-05-28T00:00:00",
    "url": "https://...",
    "content": "...",
    "metadata": {...},
    "processed": false,
    "relevance_score": 0.0
}
```

### ExtractedInfo
```python
{
    "document_id": "doc_001",
    "regulatory_body": "BCB",
    "document_type": "Circular",
    "title": "...",
    "summary": "Resumo aqui",
    
    "effective_date": "2024-06-28",
    "implementation_deadline": "2024-12-28",
    "affected_activities": ["Processamento de pagamentos"],
    "affected_entities": ["Fintechs"],
    "obligations": ["Implementar MFA"],
    "keywords": ["autenticação", "segurança"],
    
    "impact_score": 0.75,
    "impact_description": "Alto impacto",
    "impact_areas": ["Compliance", "Segurança"],
    
    "confidence_scores": {
        "summary": 0.85,
        "dates": 0.60,
        "obligations": 0.80,
        "impact": 0.75
    }
}
```

### StructuredAlert
```python
{
    "alert_id": "ALR-20260528091014",
    "created_at": "2024-05-28T09:10:14",
    
    "regulatory_body": "BCB",
    "document_title": "Circular 3.961",
    "document_type": "Circular",
    "source_url": "https://...",
    
    "summary": "O BCB requer implementação de MFA",
    "priority": "ALTO",
    "affected_activities": ["Processamento de pagamentos"],
    "obligations": ["Implementar MFA até 31/12/2024"],
    
    "effective_date": "2024-06-28",
    "implementation_deadline": "2024-12-28",
    "days_until_deadline": 214,
    
    "confidence_level": "MÉDIA",
    "impact_assessment": "Alto impacto para fintechs",
    "recommendations": ["Revisar com especialista"],
    
    "human_reviewed": false,
    "reviewer_notes": ""
}
```

## Integrações Externas

### 1. LLM (quando disponível)
```
┌─────────────────┐
│   LLM Cloud     │
│ (OpenAI, etc)   │
└────────┬────────┘
         │ HTTP
    ┌────▼─────────────────────┐
    │  LLM Integration Layer    │
    │  (src/utils/llm_*)        │
    ├──────────────────────────┤
    │ Prompts:                 │
    │ • Sumarização            │
    │ • Extração               │
    │ • Estimativa de impacto  │
    └────┬─────────────────────┘
         │ Results
    ┌────▼──────────────────┐
    │  Analysis Agent        │
    │  Usa respostas do LLM  │
    └───────────────────────┘
```

### 2. Banco de Dados (TODO)
```
┌──────────────────────┐
│   SQLite Database    │
│  regulatory_monitor  │
├──────────────────────┤
│ Tables:              │
│ • documents          │
│ • extractions        │
│ • alerts             │
│ • processing_status  │
└──────────────────────┘
```

### 3. Vector Database (para embeddings)
```
┌──────────────────────┐
│  ChromaDB            │
│  (ou similar)        │
├──────────────────────┤
│ Armazena:            │
│ • Document vectors   │
│ • Semantic search    │
│ • Similarity         │
└──────────────────────┘
```

## Fluxo de Implantação

```
Fase 1: Coleta (THIS WEEK)
├─ [ ] _fetch_bcb_documents()
├─ [ ] _fetch_cvm_documents()
└─ [ ] eliminate_duplicates()

Fase 2: Análise (NEXT WEEK)
├─ [ ] _extract_dates()
├─ [ ] _extract_obligations()
├─ [ ] _estimate_impact()
└─ [ ] LLM integration

Fase 3: Persistência (FOLLOWING WEEK)
├─ [ ] Database schema
├─ [ ] DocumentRepository
└─ [ ] Historical tracking

Fase 4: Teste & Avaliação
├─ [ ] Test corpus (~50 docs)
├─ [ ] Metrics calculation
├─ [ ] Error analysis
└─ [ ] Documentation
```

## Considerações de Performance

- **Coleta:** Paralelizar requests (ThreadPoolExecutor)
- **Análise:** Batch processing, cache de embeddings
- **Alertas:** Priorização por score (eficiente)
- **Escalabilidade:** Adicionar queue (Celery) conforme necessário

## Segurança & Governance

```
┌─────────────────────────────────────────┐
│  Security Layers                        │
├─────────────────────────────────────────┤
│                                         │
│  ✓ Validação Humana Obrigatória        │
│    └─ Nenhum alerta é acionável sem    │
│       revisão especializada             │
│                                         │
│  ✓ Rastreabilidade Total               │
│    └─ Link original preservado          │
│    └─ Confiança em cada inferência      │
│                                         │
│  ✓ Análise de Confiança                │
│    └─ Indicar ALTA/MÉDIA/BAIXA         │
│    └─ Estimar precisão de campos       │
│                                         │
│  ✓ Logs de Auditoria                   │
│    └─ Quem revisou quê                 │
│    └─ Quando e por quê                 │
│                                         │
└─────────────────────────────────────────┘
```

---

**Diagrama criado:** 2024-05-28
**Versão:** 0.1.0
**Status:** Estrutura base implementada ✓

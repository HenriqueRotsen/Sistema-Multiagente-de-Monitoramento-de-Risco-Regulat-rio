# Metodologia de Avaliação da Qualidade

Este documento descreve como o projeto avalia a qualidade da extração regulatória em termos de relevância, datas, obrigações e prazo.

## Objetivo

Medir o desempenho do pipeline de análise para priorizar melhorias de extração e comparar modelos LLM sob o mesmo conjunto de documentos.

## Corpus Anotado

Arquivo padrão:

- `data/corpus/annotated_corpus.jsonl`

Tamanho recomendado:

- 30 a 50 documentos reais.

Origem:

- coleta real BCB/CVM via `MonitorAgent`.

Estrutura por entrada:

- metadados do documento (`id`, `title`, `source`, `document_type`, `url`, `published_date`);
- conteúdo textual (`content`);
- bloco `gold` com campos de referência:
  - `relevance`;
  - `effective_date`;
  - `implementation_deadline`;
  - `obligations`;
  - `affected_activities`;
  - `impact_score`.

Status de anotação:

- `seeded_auto_needs_human_review` indica anotação inicial automática, que deve ser revisada manualmente para avaliação acadêmica final.

## Geração do Corpus

Comando:

```bash
CVM_MAX_PAGES=4 PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_annotated_corpus.py --size 30 --output data/corpus/annotated_corpus.jsonl
```

## Métricas

Implementação:

- `src/utils/evaluation.py`

Métricas calculadas:

- **Relevância**: precisão, recall, F1.
- **Datas**:
  - acurácia de `effective_date`;
  - acurácia de `implementation_deadline`;
  - média (`overall`).
- **Obrigações**:
  - precisão, recall, F1 por similaridade textual.
- **Prazo**:
  - erro médio absoluto em dias (`deadline_error_days_mean`).

## Execução da Avaliação

### Baseline heurístico

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/evaluate_analysis_quality.py --corpus data/corpus/annotated_corpus.jsonl --heuristic-only
```

### Comparação entre modelos

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/evaluate_analysis_quality.py --corpus data/corpus/annotated_corpus.jsonl --models llama3.2:3b,deepseek-r1:8b --comparison-samples 8 --llm-timeout 45 --llm-max-tokens 300 --llm-retries 1
```

## Saída dos Relatórios

Diretório:

- `reports/quality/`

Formato:

- `quality_report_YYYYMMDD_HHMMSS.json`

Campos principais:

- `generated_at`
- `corpus_path`
- `sample_size`
- `results` por baseline/modelo
- `telemetry` para modelos LLM (`llm_success_count`, `fallback_count`, warnings de health)

## Limitações Atuais

- Anotação inicial é seed automática; a avaliação final depende de revisão humana.
- Instabilidade do endpoint LLM pode induzir fallback heurístico e enviesar comparação.
- Métrica de obrigações usa similaridade textual simples e pode ser refinada.

## Boas Práticas Recomendadas

- Congelar uma versão do corpus para comparação justa entre modelos.
- Rodar avaliação em janelas curtas (`--comparison-samples`) quando o endpoint estiver instável.
- Registrar no relatório quando houve fallback por indisponibilidade de LLM.
- Repetir execuções em dias diferentes para reduzir viés de infraestrutura.

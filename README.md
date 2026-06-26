# Sistema Multiagente de Monitoramento de Risco Regulatório

Sistema de IA para monitoramento automatizado de mudanças regulatórias no setor financeiro brasileiro, com foco inicial em publicações do Banco Central do Brasil (BCB) relevantes para fintechs e instituições de pagamento.

## Status Atual

- [x] Arquitetura multiagente com 3 agentes
- [x] Coleta real de publicações do BCB via API pública atual
- [x] Triagem inicial e deduplicação de documentos
- [x] Integração com LLM via proxy Ollama da disciplina (`/api/chat`, header `X-API-Key`)
- [x] Suporte alternativo a servidores OpenAI-compatible (`/chat/completions`)
- [x] Fallback heurístico sem LLM para resumo, datas, obrigações, impacto e recomendações
- [x] Alertas estruturados com resumo, impacto, obrigações, recomendações e rastreabilidade
- [x] Interface Streamlit básica
- [x] Testes unitários para coleta, análise, LLM e alertas
- [x] Coleta CVM real
- [x] Banco de dados persistente (SQLite mínimo)
- [ ] Corpus anotado e métricas de avaliação

## Estrutura do Projeto

```text
.
├── main.py                         # Orquestra o ciclo completo
├── app.py                          # Interface Streamlit
├── src/
│   ├── agents/
│   │   ├── monitor_agent.py        # Coleta BCB, deduplicação e triagem
│   │   ├── analysis_agent.py       # Análise via LLM ou fallback heurístico
│   │   └── alert_agent.py          # Geração e priorização de alertas
│   └── utils/
│       ├── llm_integration.py      # Cliente Ollama/OpenAI-compatible
│       └── data_collection.py      # Utilitários e repositório em esqueleto
├── tests/
│   ├── test_monitor_agent.py
│   ├── test_analysis_agent.py
│   ├── test_llm_integration.py
│   └── test_alert_agent.py
├── requirements.txt
├── .env.example
└── TODO.md
```

## Arquitetura

```text
Fontes regulatórias
        |
        v
Monitor Agent
  - Coleta BCB via API pública
  - Filtra itens regulatórios
  - Remove duplicatas
        |
        v
Analysis Agent
  - Usa LLM se configurado
  - Usa fallback heurístico se necessário
  - Extrai resumo, datas, obrigações, impacto e recomendações
        |
        v
Alert Agent
  - Define prioridade
  - Formata alerta para triagem humana
  - Exporta JSON
        |
        v
Interface / Console / Validação humana
```

## Configuração

Crie o `.env` a partir do exemplo:

```bash
cp .env.example .env
```

Configuração recomendada para o proxy Ollama da disciplina:

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=https://ollama.futurelab.dcc.ufmg.br
LLM_API_KEY=sua_chave_aqui
LLM_API_KEY_HEADER=X-API-Key
LLM_MODEL=llama3.2:3b
LLM_TIMEOUT_SECONDS=60
LLM_MAX_TOKENS=1200
LLM_TEMPERATURE=0.1

BCB_NEWS_API_URL=https://www.bcb.gov.br/api/servico/sitebcb/noticias?quantidade=20
```

Modelos úteis disponíveis no servidor da disciplina incluem `llama3.2:3b` para testes rápidos e `deepseek-r1:8b` para análises mais fortes.

## Como Rodar

Instale dependências:

```bash
pip install -r requirements.txt
```

Rode o pipeline completo:

```bash
python3 main.py
```

Rode a interface:

```bash
streamlit run app.py
```

Rode os testes:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v
```

## Avaliação de Qualidade da Análise

Gerar corpus anotado inicial (30 documentos reais):

```bash
CVM_MAX_PAGES=4 PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_annotated_corpus.py --size 30 --output data/corpus/annotated_corpus.jsonl
```

Rodar baseline heurístico:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/evaluate_analysis_quality.py --corpus data/corpus/annotated_corpus.jsonl --heuristic-only
```

Comparar modelos (quando LLM estiver configurado no `.env`):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/evaluate_analysis_quality.py --corpus data/corpus/annotated_corpus.jsonl --models llama3.2:3b,deepseek-r1:8b
```

Relatórios são salvos em `reports/quality/`.

## Teste Rápido do LLM

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c "from main import RegulatoryMonitoringSystem; system=RegulatoryMonitoringSystem(); system.run_monitoring_cycle(manual_documents=[{'id':'teste','title':'Circular de Teste - Instituições de Pagamento','source':'BCB','document_type':'Circular','url':'https://example.com/teste','content':'O Banco Central determina que as instituições de pagamento deverão atualizar seus controles de prevenção a fraudes e autenticação de usuários até 30/06/2026. A norma entra em vigor em 01/01/2026. As instituições deverão manter registros das transações e comunicar incidentes relevantes ao regulador.'}])"
```

Resultado esperado: alerta com seções de resumo, impacto, atividades afetadas, obrigações, recomendações, prazo, confiança e fonte.

## Perfil Setorial Monitorado

**Foco inicial:** fintechs e instituições de pagamento.

Temas monitorados:
- pagamentos
- Pix
- Open Banking/Open Finance
- prevenção a fraudes
- segurança/autenticação
- compliance
- PLD/FT
- regulação prudencial

## Limitações e Governança

- Não substitui consultoria jurídica.
- Não toma decisões autônomas.
- Todos os alertas exigem revisão humana.
- O LLM pode errar, omitir ou inferir incorretamente.
- A rastreabilidade até a fonte é preservada no alerta.
- A confiança é estimada e deve ser usada como sinal auxiliar, não como verdade.

## Próximos Passos

1. Implementar coleta real da CVM.
2. Evoluir persistência em banco de dados (consultas, migrações e escala).
3. Criar corpus anotado com 30-50 documentos.
4. Calcular precisão, recall, F1 e acurácia de campos extraídos.
5. Melhorar filtros e histórico na interface Streamlit.

---

**Disciplina:** Projeto de Agentes de IA  
**Professor:** Antônio Alfredo Ferreira Loureiro  
**Alunos:** Gabriel Castelo Branco Rocha Alencar Pinto, Henrique Rotsen Santos Ferreira

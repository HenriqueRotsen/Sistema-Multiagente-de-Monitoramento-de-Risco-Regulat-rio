# Guia Prático de Início

Este guia descreve como instalar, configurar e testar o estado atual do sistema.

## 1. Instalação

```bash
cd /home/rotsen/Área\ de\ Trabalho/1_Semestre_Doutorado/Agentes\ De\ IA/TP

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

## 2. Configuração do `.env`

```bash
cp .env.example .env
```

Edite `.env` com a chave da API da disciplina:

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

Para análises mais fortes, teste:

```env
LLM_MODEL=deepseek-r1:8b
```

O arquivo `.env` está ignorado no git para proteger a chave.

## 3. Teste Rápido do LLM

Rode um ciclo com documento manual pequeno:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c "from main import RegulatoryMonitoringSystem; system=RegulatoryMonitoringSystem(); system.run_monitoring_cycle(manual_documents=[{'id':'teste','title':'Circular de Teste - Instituições de Pagamento','source':'BCB','document_type':'Circular','url':'https://example.com/teste','content':'O Banco Central determina que as instituições de pagamento deverão atualizar seus controles de prevenção a fraudes e autenticação de usuários até 30/06/2026. A norma entra em vigor em 01/01/2026. As instituições deverão manter registros das transações e comunicar incidentes relevantes ao regulador.'}])"
```

Resultado esperado:

- log `LLM configurado: provider=ollama model=...`
- alerta com `RESUMO`, `IMPACTO`, `OBRIGAÇÕES` e `RECOMENDAÇÕES`
- prioridade baseada em prazo e impacto

## 4. Executar Pipeline Real

```bash
python3 main.py
```

O sistema irá:

1. Coletar publicações reais do BCB.
2. Filtrar itens regulatórios.
3. Analisar cada documento com LLM, se configurado.
4. Usar fallback heurístico se o LLM falhar.
5. Gerar alertas estruturados no console.

Observação: o ciclo real pode chamar o LLM várias vezes. Para testes rápidos, prefira o comando manual da seção anterior.

## 5. Interface Streamlit

```bash
streamlit run app.py
```

Abra o endereço indicado pelo Streamlit e clique em **Executar Ciclo de Monitoramento**.

Status atual da interface:

- dashboard básico
- execução do ciclo
- visualização de alertas
- export JSON
- filtros visuais ainda parcialmente conectados
- revisão humana ainda não persistida

## 6. Testes Automatizados

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -v
```

Resultado esperado:

```text
Ran 13 tests
OK
```

Os testes cobrem:

- coleta BCB via API atual e RSS mockado
- análise com mock de LLM
- fallback heurístico
- cliente Ollama com `X-API-Key`
- alertas com resumo, impacto e recomendações
- prioridade com prazo vencido

## 7. Configurações de LLM Suportadas

### Proxy Ollama da disciplina

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=https://ollama.futurelab.dcc.ufmg.br
LLM_API_KEY=sua_chave
LLM_API_KEY_HEADER=X-API-Key
LLM_MODEL=llama3.2:3b
```

### Servidor OpenAI-compatible

```env
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sua_chave
LLM_MODEL=gpt-4o-mini
```

## 8. Arquivos Mais Importantes

| Arquivo | Função |
|--------|--------|
| `main.py` | Orquestra coleta, análise e alertas |
| `src/agents/monitor_agent.py` | Coleta BCB e triagem |
| `src/agents/analysis_agent.py` | Análise com LLM/fallback |
| `src/agents/alert_agent.py` | Priorização e formatação dos alertas |
| `src/utils/llm_integration.py` | Cliente Ollama/OpenAI-compatible |
| `app.py` | Interface Streamlit |
| `TODO.md` | Próximas tarefas |

## 9. Próximo Desenvolvimento Recomendado

Implementar persistência SQLite:

1. Criar `database/schema.sql`.
2. Implementar `DocumentRepository`.
3. Evitar reprocessamento dos mesmos documentos.
4. Persistir alertas e revisão humana.
5. Alimentar a interface Streamlit com histórico real.

Depois disso, implementar a coleta CVM fica mais útil, porque o sistema já terá histórico e controle de duplicatas persistente.

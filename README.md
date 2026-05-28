# Sistema Multiagente de Monitoramento de Risco Regulatório

Sistema de IA para monitoramento automatizado de mudanças regulatórias no setor financeiro brasileiro, focando em publicações do Banco Central do Brasil (BCB) e Comissão de Valores Mobiliários (CVM).

## 📋 Estrutura do Projeto

```
.
├── src/
│   ├── agents/           # Agentes principais do sistema
│   │   ├── monitor_agent.py       # Monitora fontes regulatórias
│   │   ├── analysis_agent.py      # Analisa impacto regulatório
│   │   └── alert_agent.py         # Gera alertas estruturados
│   ├── utils/            # Funções utilitárias
│   │   ├── data_collection.py     # Coleta de documentos
│   │   ├── extraction.py          # Extração de informações
│   │   ├── embeddings.py          # Processamento de embeddings
│   │   └── validators.py          # Validações
│   └── data/             # Dados e modelos
│       ├── profiles.yaml  # Perfis setoriais
│       └── keywords.json  # Palavras-chave por domínio
├── database/
│   └── schema.sql        # Schema do banco de dados
├── notebooks/            # Análise exploratória
├── tests/                # Testes unitários
├── app.py                # Interface Streamlit
└── main.py               # Orquestração principal

```

## 🎯 Objetivos

- [x] Arquitetura de 3 agentes multiagente
- [ ] Coleta automática de documentos do BCB e CVM
- [ ] Classificação de relevância por setor (fintechs/pagamentos)
- [ ] Extração estruturada de informações (datas, prazos, impacto)
- [ ] Geração de alertas estruturados
- [ ] Interface para visualização e triagem humana
- [ ] Base de dados com histórico processado
- [ ] Avaliação com métricas (Precisão, Recall, F1)

## 🔧 Arquitetura do Sistema Multiagente

### 1. **Monitor Agent** (Coletor)
- Observa fontes: RSS BCB, portal CVM, APIs públicas
- Detecta novos documentos
- Elimina duplicatas
- Encaminha para análise inicial

### 2. **Analysis Agent** (Analisador de Impacto)
- Análise profunda do conteúdo
- Extrai: obrigações, atividades afetadas, datas, prazos
- Estima impacto potencial
- Identifica entidades impactadas

### 3. **Alert Agent** (Gerador de Alertas)
- Consolida dados extraídos
- Prioriza por urgência
- Gera alertas estruturados
- Formata para triagem humana

## 📊 Fluxo de Processamento

```
Fontes Regulatórias
        ↓
   [Monitor Agent]
   (triagem inicial)
        ↓
  [Analysis Agent]
  (extração de info)
        ↓
   [Alert Agent]
   (formatação)
        ↓
 [Validação Humana]
        ↓
   Interface/Output
```

## 🚀 Como Começar

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas chaves de API

# Executar agente
python main.py

# Iniciar interface Streamlit
streamlit run app.py
```

## 📝 Configuração

Criar arquivo `.env`:
```env
# LLM
LLM_API_KEY=your_api_key_here
LLM_MODEL=your_model_name

# Banco de Dados
DB_URL=sqlite:///regulatory_monitor.db

# Fontes
BCB_RSS_URL=https://www.bcb.gov.br/...
CVM_RSS_URL=https://www.cvm.gov.br/...

# Embeddings
EMBEDDING_MODEL=sentence-transformers/...
CHROMA_DB_PATH=./chroma_db
```

## 🔍 Perfil Setorial Monitorado

**Foco Inicial**: Fintechs e Instituições de Pagamento
- Tópicos: Pagamentos, PLD/FT, Segurança, Compliance, Open Banking
- Reguladores: BCB, CVM
- Idioma: Português (BR)

## 📊 Métricas de Avaliação

- **Classificação**: Precisão, Recall, F1-score
- **Extração**: Acurácia em campos críticos (data, prazo, regulador)
- **Qualitativa**: Clareza, rastreabilidade, utilidade dos alertas

## ⚠️ Limitações & Governance

- ❌ NÃO substitui consultoria jurídica
- ❌ NÃO toma decisões autônomas
- ✅ REQUER validação humana de todos os alertas
- ✅ PRESERVA rastreabilidade até fonte original
- ✅ INDICA confiança/natureza estimativa de inferências

## 🧪 Status de Implementação

- [ ] Monitor Agent funcional
- [ ] Analysis Agent funcional
- [ ] Alert Agent funcional
- [ ] Integração com BCB/CVM
- [ ] Database schema
- [ ] Interface Streamlit
- [ ] Testes unitários
- [ ] Avaliação com corpus anotado

---
**Disciplina**: Projeto de Agentes de IA
**Professor**: Antônio Alfredo Ferreira Loureiro
**Alunos**: Gabriel Castelo Branco Rocha Alencar Pinto, Henrique Rotsen Santos Ferreira

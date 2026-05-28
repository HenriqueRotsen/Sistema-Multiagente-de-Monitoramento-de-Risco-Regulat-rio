# TODO - Sistema de Monitoramento de Risco Regulatório

## 🎯 Implementação Principal

### 1. Monitor Agent - Coleta de Dados
- [ ] Implementar `_fetch_bcb_documents()` 
  - [ ] Parser de RSS do BCB
  - [ ] Normalização de tipos (Circular, Resolução, Ofício)
  - [ ] Extração de metadados

- [ ] Implementar `_fetch_cvm_documents()`
  - [ ] Scraping ou API de portal CVM
  - [ ] Normalização de tipos (Instrução, Resolução, Deliberação)
  - [ ] Tratamento de paginação

- [ ] Tratamento de erros e retry logic
- [ ] Cache de documentos já processados

### 2. Analysis Agent - Extração de Informações
- [ ] Implementar `_extract_summary()` com LLM
  - [ ] Integração com modelo de linguagem
  - [ ] Sumarização abstractiva (150-200 palavras)

- [ ] Implementar `_extract_dates()`
  - [ ] Regex para datas brasileiras (DD/MM/YYYY)
  - [ ] Processamento de "X dias após publicação"
  - [ ] Identificação de "vigência imediata"

- [ ] Implementar `_extract_obligations()`
  - [ ] NER para verbos modais
  - [ ] Estruturação de obrigações
  - [ ] Associação com prazos

- [ ] Implementar `_estimate_impact()`
  - [ ] Scoring baseado em relevância setorial
  - [ ] Identificação de áreas impactadas
  - [ ] Cálculo de urgência por prazo

### 3. Alert Agent - Geração de Alertas
- [ ] Implementar `_generate_summary()` com templates customizados
- [ ] Implementar `_generate_recommendations()` por tipo de obrigação
- [ ] Implementar `export_alerts()` com múltiplos formatos
  - [ ] JSON (para sistemas)
  - [ ] PDF (para relatórios)
  - [ ] CSV (para planilhas)
  - [ ] HTML (para portal)

### 4. Data Collection Utils
- [ ] Implementar `fetch_bcb_rss()` completo
- [ ] Implementar `fetch_cvm_documents()` completo
- [ ] Implementar `normalize_date()` com múltiplos formatos
- [ ] Implementar `extract_sections()` de documentos legais
- [ ] Implementar `extract_dates()` com regex robustos
- [ ] Implementar `extract_obligations()` com NER
- [ ] Implementar `extract_entities()` para instituições

### 5. Banco de Dados
- [ ] Criar schema SQL (schema.sql)
- [ ] Implementar `DocumentRepository.add_document()`
- [ ] Implementar `DocumentRepository.check_duplicate()`
- [ ] Implementar `DocumentRepository.get_processed_documents()`
- [ ] Implementar `DocumentRepository.update_processing_status()`

### 6. Integração LLM
- [ ] Setup de conexão com API potente (GPT-4, Claude, etc)
- [ ] Implementar prompts para:
  - [ ] Sumarização
  - [ ] Extração de obrigações
  - [ ] Estimativa de impacto
  - [ ] Geração de recomendações
- [ ] Tratamento de rate limits
- [ ] Fallback para métodos mais simples em caso de falha

### 7. Interface Streamlit
- [ ] Implementar dashboard dinâmico com dados reais
- [ ] Implementar sistema de filtros funcional
- [ ] Implementar export de alertas
- [ ] Implementar marcação de alertas como revisados
- [ ] Implementar histórico de processamento

### 8. Testes
- [ ] Testes unitários para cada agente
- [ ] Testes de integração do fluxo completo
- [ ] Testes de coleta (mock de dados)
- [ ] Testes de análise (corpus de teste)
- [ ] Testes de performance

### 9. Avaliação
- [ ] Montar corpus anotado de teste (~30-50 documentos)
- [ ] Anotar: relevância, datas, prazos, tipos, impacto
- [ ] Calcular métricas:
  - [ ] Precisão/Recall/F1 para classificação
  - [ ] Acurácia para extração de campos
  - [ ] Taxa de erro de prazos
- [ ] Análise de erros e limitações

### 10. Documentação
- [ ] Documentar arquitetura com diagramas
- [ ] Docstrings completas em cada função
- [ ] Guia de configuração
- [ ] Exemplos de uso
- [ ] Tratamento de erros comuns

---

## 🔌 Integração com LLM (Próximos Passos)

Quando tiver acesso à máquina potente via API key:

```python
# Em src/utils/llm_integration.py (CRIAR)
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class RegulatoryLLM:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.llm = OpenAI(api_key=api_key, model=model)
    
    def summarize_regulation(self, text: str) -> str:
        """Sumariza documento regulatório"""
        ...
    
    def extract_obligations(self, text: str) -> List[str]:
        """Extrai obrigações estruturadas"""
        ...
    
    def estimate_impact(self, text: str, sector_profile: dict) -> float:
        """Estima impacto para setor"""
        ...
```

Adicionar em requirements.txt quando pronto:
```
openai>=0.27.0
langchain>=0.0.200
tiktoken>=0.4.0
```

---

## 📊 Corpus de Teste

Criar arquivo `data/test_corpus.json` com ~10 documentos de teste:
- 5 documentos BCB (Circulares, Resoluções)
- 5 documentos CVM (Instruções, Deliberações)
- Anotados com: relevância, datas, prazos, impacto

---

## 🎓 Métricas de Avaliação (Proposta)

### Classificação de Relevância
- Precisão: Documentos classificados como relevantes que realmente o são
- Recall: Proporção de documentos relevantes detectados
- F1-score: Média harmônica

### Extração de Informações
- Acurácia campo "data de vigência"
- Acurácia campo "prazo de implementação"
- Acurácia campo "regulador"
- Taxa de erro em prazos (dias)

### Qualidade de Alertas
- Clareza: Compreensibilidade por especialista
- Rastreabilidade: Correspondência com fonte
- Utilidade: Qualidade para tomada de decisão

---

## ⚠️ Limitações Conhecidas (Documentar)

1. Documentos regulatórios com estrutura não-padrão
2. Exceções e condicionantes complexas
3. Mudanças em formatos de publicação das fontes
4. Linguagem ambígua ou com termos mal definidos
5. Alucinação potencial de LLMs

---

## ✅ Checklist de Entrega Final

- [ ] Código funcional e testado
- [ ] Corpus anotado criado
- [ ] Métricas de avaliação calculadas
- [ ] Documentação completa
- [ ] Análise de resultados e limitações
- [ ] README atualizado
- [ ] Repositório limpo

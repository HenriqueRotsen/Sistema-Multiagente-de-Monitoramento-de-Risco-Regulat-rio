"""
Template para Integração com LLM Externo
Quando você tiver acesso à máquina potente via API key

PRÓXIMOS PASSOS:
1. Adicionar chaves em .env
2. Instalar langchain: pip install langchain openai  (ou similar)
3. Descomentar e preencher o arquivo abaixo
4. Integrar com Analysis Agent
"""

# ============================================================================
# EXEMPLO 1: Integração com OpenAI (GPT-4)
# ============================================================================

# Descomente quando tiver API key:

"""
import os
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

class RegulatoryLLM:
    def __init__(self, api_key: str = None, model: str = "gpt-4"):
        api_key = api_key or os.getenv("LLM_API_KEY")
        self.llm = OpenAI(
            api_key=api_key,
            model_name=model,
            temperature=0.3,
            max_tokens=1000
        )

    def summarize_regulation(self, text: str) -> str:
        '''Sumariza documento regulatório em português'''
        prompt_template = PromptTemplate(
            input_variables=['text'],
            template='''Você é um especialista em regulação financeira brasileira.
            Resuma o seguinte documento regulatório em 3-4 sentenças claras:
            
            {text}
            
            Resumo:'''
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        return chain.run(text=text[:3000])  # Limitar tamanho
    
    def extract_obligations(self, text: str) -> list:
        '''Extrai obrigações principais do documento'''
        prompt_template = PromptTemplate(
            input_variables=['text'],
            template='''Extraia as 5 obrigações principais deste documento regulatório.
            Retorne como lista numerada, cada obrigação em uma linha.
            
            {text}
            
            Obrigações:'''
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        response = chain.run(text=text[:3000])
        
        # Parse response into list
        obligations = [
            line.strip() 
            for line in response.split('\\n')
            if line.strip() and not line.startswith('Obrigações')
        ]
        return obligations[:5]
    
    def estimate_impact(self, text: str, sector: str = "fintechs") -> dict:
        '''Estima impacto para setor específico'''
        prompt_template = PromptTemplate(
            input_variables=['text', 'sector'],
            template='''Analise o impacto desta regulação para {sector}.
            
            Retorne em formato JSON:
            {{
                "impact_score": <0.0-1.0>,
                "affected_areas": [lista de áreas impactadas],
                "urgency": "CRÍTICA|ALTA|MÉDIA|BAIXA",
                "key_risks": [lista de riscos principais],
                "recommendations": [lista de ações recomendadas]
            }}
            
            Documento:
            {text}
            
            JSON:'''
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        response = chain.run(text=text[:3000], sector=sector)
        
        import json
        try:
            return json.loads(response)
        except:
            # Fallback
            return {
                "impact_score": 0.5,
                "affected_areas": ["Compliance"],
                "urgency": "MÉDIA",
                "key_risks": [],
                "recommendations": []
            }
    
    def generate_recommendations(self, obligations: list) -> list:
        '''Gera recomendações iniciais baseado em obrigações'''
        prompt_template = PromptTemplate(
            input_variables=['obligations'],
            template='''Para cada uma das seguintes obrigações regulatórias,
            sugira 1-2 ações iniciais que uma fintech deve tomar:
            
            Obrigações:
            {obligations}
            
            Recomendações (formato: - AÇÃO | prazo):'''
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        response = chain.run(obligations='\\n'.join(obligations))
        
        return [
            line.strip()
            for line in response.split('\\n')
            if line.strip().startswith('-')
        ]
"""

# ============================================================================
# EXEMPLO 2: Integração com Claude (Anthropic)
# ============================================================================

"""
from langchain.chat_models import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage

class RegulatoryLLMClaude:
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("LLM_API_KEY")
        self.llm = ChatAnthropic(
            anthropic_api_key=api_key,
            model="claude-3-sonnet-20240229"
        )
    
    def summarize_regulation(self, text: str) -> str:
        messages = [
            SystemMessage(content="Você é especialista em regulação financeira brasileira."),
            HumanMessage(content=f"Resuma este documento em 3-4 sentenças:\\n\\n{text[:3000]}")
        ]
        return self.llm(messages).content
"""

# ============================================================================
# EXEMPLO 3: Integração com Cohere
# ============================================================================

"""
from langchain.llms import Cohere

class RegulatoryLLMCohere:
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("LLM_API_KEY")
        self.llm = Cohere(
            cohere_api_key=api_key,
            model="command"
        )
"""

# ============================================================================
# COMO USAR NO ANALYSIS AGENT
# ============================================================================

"""
# Em src/agents/analysis_agent.py, modificar:

def _extract_summary(self, text: str, info: ExtractedInfo):
    '''Agora com LLM!'''
    if self.llm_model:
        try:
            info.summary = self.llm_model.summarize_regulation(text)
            info.confidence_scores['summary'] = 0.85
        except Exception as e:
            logger.error(f"Erro ao chamar LLM: {e}")
            info.summary = "Erro na sumarização"
    else:
        info.summary = text[:200] + "..."

def _extract_obligations(self, text: str, info: ExtractedInfo):
    '''Agora com LLM!'''
    if self.llm_model:
        try:
            info.obligations = self.llm_model.extract_obligations(text)
            info.confidence_scores['obligations'] = 0.80
        except Exception as e:
            logger.error(f"Erro ao extrair obrigações: {e}")
            info.obligations = []
    else:
        info.obligations = []

def _estimate_impact(self, text: str, info: ExtractedInfo):
    '''Agora com LLM!'''
    if self.llm_model:
        try:
            result = self.llm_model.estimate_impact(text, self.sector_profile['name'])
            info.impact_score = result.get('impact_score', 0.5)
            info.impact_areas = result.get('affected_areas', [])
            info.confidence_scores['impact'] = 0.80
        except Exception as e:
            logger.error(f"Erro ao estimar impacto: {e}")
    else:
        # Fallback para heurística
        ...
"""

# ============================================================================
# SETUP NO main.py
# ============================================================================

"""
# Em main.py, modificar:

from src.utils.llm_integration import RegulatoryLLM  # Quando implementar
import os

class RegulatoryMonitoringSystem:
    def __init__(self):
        # ... código existente ...
        
        # Integrar LLM se API key disponível
        llm_api_key = os.getenv("LLM_API_KEY")
        if llm_api_key:
            self.llm = RegulatoryLLM(api_key=llm_api_key)
            self.analysis_agent.llm_model = self.llm
            logger.info("✓ LLM integrado com sucesso")
        else:
            logger.warning("⚠ LLM não configurado (deixando em modo placeholder)")
"""

# ============================================================================
# REQUIREMENTS.TXT (Adicionar quando tiver API key)
# ============================================================================

"""
# Descomente para integração com LLM específico:

# Para OpenAI/GPT-4:
# openai>=0.27.0
# langchain>=0.0.200
# tiktoken>=0.4.0

# Para Anthropic/Claude:
# anthropic>=0.7.0

# Para Cohere:
# cohere>=4.0.0

# Para suporte a múltiplos (recomendado):
langchain-openai>=0.1.0
langchain-anthropic>=0.1.0
"""

# ============================================================================
# VARIÁVEIS DE AMBIENTE (.env)
# ============================================================================

"""
# OpenAI
OPENAI_API_KEY=sk-...

# Ou Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Ou Cohere
COHERE_API_KEY=...

# Ou seu endpoint customizado
LLM_API_KEY=...
LLM_API_BASE=https://...
LLM_MODEL=seu-modelo
"""

# ============================================================================
# TESTANDO LOCALMENTE COM API MOCK (sem custos)
# ============================================================================

"""
# Para desenvolvimento, use modelos locais com Ollama:
# https://ollama.ai

# 1. Instale Ollama
# 2. Execute: ollama pull llama2-uncensored
# 3. Adicione em .env: LLM_BASE_URL=http://localhost:11434

from langchain.llms import Ollama

class RegulatoryLLMLocal:
    def __init__(self, model: str = "llama2"):
        self.llm = Ollama(
            model=model,
            base_url="http://localhost:11434"
        )
    
    # Mesmos métodos acima, mas usando modelo local
"""

# ============================================================================
# MONITORAMENTO DE CUSTOS
# ============================================================================

"""
Adicione tracking de custos se usar API paga:

class CostTracker:
    def __init__(self):
        self.total_tokens = 0
        self.total_cost = 0.0
    
    def log_usage(self, model: str, tokens_used: int):
        # Preços (exemplo para GPT-4)
        prices = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
        }
        
        self.total_tokens += tokens_used
        # Calcule custo conforme sua tarificação
"""

print("""
╔════════════════════════════════════════════════════════════════════╗
║  🚀 INTEGRAÇÃO COM LLM - PRÓXIMOS PASSOS                          ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  1. Obtenha API key de seu provedor (OpenAI, Anthropic, etc)     ║
║                                                                    ║
║  2. Adicione em .env:                                             ║
║     LLM_API_KEY=sua_chave_aqui                                   ║
║     LLM_MODEL=modelo_desejado                                    ║
║                                                                    ║
║  3. Instale dependências:                                         ║
║     pip install langchain openai  (ou seu provedor)              ║
║                                                                    ║
║  4. Crie src/utils/llm_integration.py com exemplos acima         ║
║                                                                    ║
║  5. Modifique analysis_agent.py para usar self.llm_model        ║
║                                                                    ║
║  6. Teste com: python3 main.py                                   ║
║                                                                    ║
║  ⚠️  AVISO: APIs pagas podem ter custos significativos!          ║
║     Use estimativas de tokens antes de deploy em produção       ║
║                                                                    ║
║  💡 DICA: Comece com GPT-3.5-turbo (mais barato) para testar     ║
║           Migre para GPT-4 quando quiser melhor qualidade       ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
""")

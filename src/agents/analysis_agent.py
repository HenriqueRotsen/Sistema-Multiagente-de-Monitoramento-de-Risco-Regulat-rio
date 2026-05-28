"""
Analysis Agent - Analisa impacto regulatório e extrai informações estruturadas
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractedInfo:
    """Informações extraídas de um documento regulatório"""
    document_id: str
    regulatory_body: str  # BCB, CVM
    document_type: str
    title: str
    summary: str
    
    # Informações estruturadas extraídas
    effective_date: Optional[datetime] = None
    implementation_deadline: Optional[datetime] = None
    affected_activities: List[str] = field(default_factory=list)
    affected_entities: List[str] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # Estimativa de impacto
    impact_score: float = 0.0  # 0.0 (baixo) a 1.0 (alto)
    impact_description: str = ""
    impact_areas: List[str] = field(default_factory=list)  # Compliance, Tecnologia, Operacional, etc
    
    # Confiança das extrações
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    extraction_method: str = "placeholder"  # "regex", "nlp", "llm", "hybrid"


class AnalysisAgent:
    """
    Agente responsável por:
    1. Análise profunda de conteúdo regulatório
    2. Extração de informações estruturadas
    3. Estimativa de impacto
    4. Identificação de entidades afetadas
    """

    def __init__(self, llm_model=None, embedding_model=None):
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.sector_profile = {
            "name": "Fintechs e Instituições de Pagamento",
            "keywords": self._get_sector_keywords(),
            "activities": self._get_affected_activities(),
            "risk_areas": ["Compliance", "Segurança", "PLD/FT", "Open Banking", "Autenticação"]
        }

    def analyze_document(self, document_text: str, metadata: Dict[str, Any]) -> ExtractedInfo:
        """
        Analisa um documento completo e extrai informações estruturadas
        """
        logger.info(f"Analisando documento: {metadata.get('title', 'sem título')}")
        
        info = ExtractedInfo(
            document_id=metadata.get('id', ''),
            regulatory_body=metadata.get('source', ''),
            document_type=metadata.get('document_type', ''),
            title=metadata.get('title', '')
        )
        
        # Executa pipeline de extração
        self._extract_summary(document_text, info)
        self._extract_dates(document_text, info)
        self._extract_obligations(document_text, info)
        self._extract_affected_entities(document_text, info)
        self._extract_keywords(document_text, info)
        self._estimate_impact(document_text, info)
        
        return info

    def _extract_summary(self, text: str, info: ExtractedInfo):
        """
        TODO: Implementar sumarização
        - Usar modelo de sumarização abstractiva
        - Limitar a ~150-200 palavras
        - Manter informações críticas
        """
        info.summary = "Sumarização a ser implementada com LLM"
        info.confidence_scores['summary'] = 0.0

    def _extract_dates(self, text: str, info: ExtractedInfo):
        """
        TODO: Implementar extração de datas
        - Data de vigência
        - Prazo de implementação
        - Usar regex + NER para datas
        - Lidar com formatos variados (DD/MM/YYYY, etc)
        - Extrair "X dias após publicação"
        """
        info.confidence_scores['dates'] = 0.0

    def _extract_obligations(self, text: str, info: ExtractedInfo):
        """
        TODO: Implementar extração de obrigações
        - Identificar verbos modais (deve, deverá, é obrigado a)
        - Estruturar obrigações como lista
        - Associar com prazos quando possível
        - Exemplo: ["Implementar autenticação MFA até 30/06/2024", ...]
        """
        info.obligations = [
            "Placeholder: obrigações a extrair",
        ]
        info.confidence_scores['obligations'] = 0.0

    def _extract_affected_entities(self, text: str, info: ExtractedInfo):
        """
        TODO: Implementar extração de entidades afetadas
        - NER para identificar instituições
        - Validar contra base de instituições financeiras
        - Identificar setores afetados
        - Exemplo: ["Fintechs", "Instituições de pagamento", ...]
        """
        info.affected_activities = self._match_sector_keywords(text)
        info.confidence_scores['entities'] = 0.0

    def _extract_keywords(self, text: str, info: ExtractedInfo):
        """
        TODO: Implementar extração de keywords
        - TF-IDF ou BERTopic
        - Filtrar palavras relevantes para o domínio
        - Top-5 keywords por importância
        """
        info.keywords = ["Placeholder", "keywords"]
        info.confidence_scores['keywords'] = 0.0

    def _estimate_impact(self, text: str, info: ExtractedInfo):
        """
        TODO: Implementar estimativa de impacto
        - Score 0.0-1.0 baseado em:
          * Relevância para setor (fintechs/pagamentos)
          * Urgência (prazo curto = alto impacto)
          * Amplitude (quantas entidades afetadas)
          * Tipo de mudança (obrigação vs recomendação)
        - Identificar áreas de impacto (Compliance, Tech, Ops)
        """
        # Heurística simples: keyword matching
        sector_match = any(kw in text.lower() for kw in self.sector_profile['keywords'])
        info.impact_score = 0.6 if sector_match else 0.3
        info.impact_areas = ["Compliance"]
        info.impact_description = "Impacto estimado a ser refinado com LLM"
        info.confidence_scores['impact'] = 0.0

    def _match_sector_keywords(self, text: str) -> List[str]:
        """Identifica atividades afetadas baseado em keywords"""
        matched = []
        text_lower = text.lower()
        
        for activity in self.sector_profile['activities']:
            if activity.lower() in text_lower:
                matched.append(activity)
        
        return matched

    def _get_sector_keywords(self) -> List[str]:
        """Keywords relevantes para fintechs e pagamentos"""
        return [
            "pagamento", "fintech", "cartão", "transferência", "instituição de pagamento",
            "gateway", "wallet", "criptomoeda", "open banking", "pix", "autenticação",
            "segurança", "pld", "fraude", "compliance", "capital", "prudencial"
        ]

    def _get_affected_activities(self) -> List[str]:
        """Atividades que podem ser afetadas"""
        return [
            "Processamento de pagamentos",
            "Transferências interbancárias",
            "Carteiras digitais",
            "Custódia de criptoativos",
            "Crédito ao consumidor",
            "Open Banking",
            "Autenticação e segurança",
            "Conformidade com regulações",
            "Relatórios regulatórios"
        ]

    def batch_analyze(self, documents: List[Dict[str, Any]]) -> List[ExtractedInfo]:
        """Analisa lote de documentos"""
        results = []
        
        for doc in documents:
            try:
                info = self.analyze_document(
                    doc.get('content', ''),
                    doc.get('metadata', {})
                )
                results.append(info)
            except Exception as e:
                logger.error(f"Erro ao analisar documento {doc.get('id')}: {str(e)}")
        
        return results

    def filter_by_relevance(self, analyses: List[ExtractedInfo], threshold: float = 0.5) -> List[ExtractedInfo]:
        """Filtra análises por score de impacto"""
        return [a for a in analyses if a.impact_score >= threshold]

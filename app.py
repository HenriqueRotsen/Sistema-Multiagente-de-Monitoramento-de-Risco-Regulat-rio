"""
Interface Streamlit para visualização e triagem de alertas regulatórios
"""
import streamlit as st
from datetime import datetime
from typing import List
import json

from src.agents.alert_agent import AlertPriority
from main import RegulatoryMonitoringSystem


st.set_page_config(
    page_title="Monitor de Risco Regulatório",
    page_icon="🏛️",
    layout="wide"
)


def init_session_state():
    """Inicializa estado da sessão"""
    if 'system' not in st.session_state:
        st.session_state.system = RegulatoryMonitoringSystem()
    if 'alerts' not in st.session_state:
        st.session_state.alerts = []
    if 'reviewed_alerts' not in st.session_state:
        st.session_state.reviewed_alerts = {}


def render_header():
    """Renderiza cabeçalho da aplicação"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🏛️ Monitor de Risco Regulatório")
        st.markdown("*Sistema de Monitoramento Automatizado de Alterações Regulatórias Brasileiras*")
    
    with col2:
        st.markdown(f"**Status:** 🟢 Online")
        st.markdown(f"**Última atualização:** {datetime.now().strftime('%H:%M:%S')}")


def render_dashboard():
    """Renderiza dashboard principal"""
    st.header("📊 Dashboard")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Alertas Críticos",
            value=0,
            delta="+1 novo"
        )
    
    with col2:
        st.metric(
            label="Alertas Altos",
            value=0,
            delta="Sem mudanças"
        )
    
    with col3:
        st.metric(
            label="Pendentes de Revisão",
            value=len(st.session_state.alerts),
            delta=f"+{len(st.session_state.alerts)}"
        )
    
    with col4:
        st.metric(
            label="Taxa de Processamento",
            value="95%",
            delta="+2%"
        )


def render_alerts_section():
    """Renderiza seção de alertas"""
    st.header("🔔 Alertas Regulatórios")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        priority_filter = st.multiselect(
            "Filtrar por Prioridade",
            ["CRÍTICO", "ALTO", "MÉDIO", "BAIXO"],
            default=["CRÍTICO", "ALTO"]
        )
    
    with col2:
        regulator_filter = st.multiselect(
            "Filtrar por Regulador",
            ["BCB", "CVM"],
            default=["BCB", "CVM"]
        )
    
    with col3:
        status_filter = st.selectbox(
            "Status de Revisão",
            ["Todos", "Pendentes", "Revisados"]
        )
    
    st.divider()
    
    # Lista de alertas
    if st.session_state.alerts:
        for i, alert in enumerate(st.session_state.alerts):
            with st.expander(
                f"🔔 {alert['priority']} | {alert['document_title'][:60]}... | "
                f"{alert['regulatory_body']} | {alert['created_at'][:10]}",
                expanded=(i == 0)
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Regulador:** {alert['regulatory_body']}")
                    st.markdown(f"**Tipo:** {alert['document_type']}")
                    st.markdown(f"**Resumo:** {alert['summary']}")
                    
                    if alert['affected_activities']:
                        st.markdown("**Atividades Afetadas:**")
                        for activity in alert['affected_activities']:
                            st.markdown(f"  • {activity}")
                    
                    if alert['obligations']:
                        st.markdown("**Obrigações:**")
                        for obligation in alert['obligations'][:3]:
                            st.markdown(f"  • {obligation}")
                    
                    if alert['implementation_deadline']:
                        days = alert['days_until_deadline'] or 0
                        st.markdown(f"**Prazo:** {alert['implementation_deadline'][:10]} ({days} dias)")
                    
                    st.markdown(f"**Confiança:** {alert['confidence_level']}")
                    st.markdown(f"**[Fonte]({alert['source_url']}) {{target=_blank}}")
                
                with col2:
                    if st.button(f"✅ Revisar", key=f"review_{i}"):
                        st.session_state.reviewed_alerts[alert['alert_id']] = True
                        st.success("Alerta marcado como revisado!")
                    
                    if st.button(f"📌 Arquivar", key=f"archive_{i}"):
                        st.info("Alerta arquivado")
    else:
        st.info("Nenhum alerta gerado no ciclo atual")


def render_execution_panel():
    """Renderiza painel de execução"""
    st.header("⚙️ Controle de Execução")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Executar Ciclo de Monitoramento", key="run_cycle"):
            with st.spinner("Executando monitoramento..."):
                result = st.session_state.system.run_monitoring_cycle()
                st.session_state.alerts = result.get('alerts', [])
                
                st.success(f"✓ Ciclo concluído!")
                st.json({
                    "documentos_coletados": result['documents_collected'],
                    "documentos_analisados": result['documents_analyzed'],
                    "alertas_gerados": result['alerts_generated']
                })
    
    with col2:
        if st.button("📊 Exportar Alertas (JSON)"):
            if st.session_state.alerts:
                json_str = json.dumps(st.session_state.alerts, ensure_ascii=False, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"alertas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.warning("Nenhum alerta para exportar")


def render_documentation():
    """Renderiza seção de documentação"""
    st.header("📚 Documentação")
    
    with st.expander("ℹ️ Sobre o Sistema"):
        st.markdown("""
        ### Sistema Multiagente de Monitoramento de Risco Regulatório
        
        Automatiza o monitoramento de mudanças regulatórias no setor financeiro brasileiro,
        integrando publicações do **Banco Central** e **CVM**.
        
        **Componentes:**
        - 🔍 Monitor Agent: Coleta documentos regulatórios
        - 📊 Analysis Agent: Extrai informações e estima impacto
        - 🔔 Alert Agent: Gera alertas estruturados para triagem humana
        """)
    
    with st.expander("⚠️ Aviso Legal"):
        st.warning("""
        **IMPORTANTE:**
        - ⚠️ Este sistema **NÃO substitui consultoria jurídica**
        - ⚠️ **REQUER validação humana** de todos os alertas antes de ação
        - ✅ Mantém rastreabilidade completa até a fonte original
        - ✅ Indicar nível de confiança em todas as inferências
        """)
    
    with st.expander("📋 Prioridades de Alerta"):
        st.markdown("""
        | Nível | Critério | Ação |
        |-------|----------|------|
        | 🔴 **CRÍTICO** | Prazo < 7 dias | Revisar imediatamente |
        | 🟠 **ALTO** | Prazo 7-30 dias | Revisar hoje |
        | 🟡 **MÉDIO** | Prazo 30-90 dias | Revisar esta semana |
        | 🟢 **BAIXO** | Prazo > 90 dias | Acompanhar |
        """)


def render_sidebar():
    """Renderiza sidebar"""
    with st.sidebar:
        st.title("🔧 Configurações")
        
        st.subheader("Fontes")
        bcb_enabled = st.checkbox("BCB", value=True)
        cvm_enabled = st.checkbox("CVM", value=True)
        
        st.subheader("Filtros de Relevância")
        sector = st.selectbox(
            "Setor Monitorado",
            ["Fintechs", "Instituições de Pagamento", "Todas"]
        )
        
        min_confidence = st.slider(
            "Confiança Mínima",
            0.0, 1.0, 0.6, 0.1
        )
        
        st.divider()
        
        st.subheader("Sobre")
        st.markdown("""
        **Disciplina:** Projeto de Agentes de IA
        
        **Professor:** Antônio Alfredo Ferreira Loureiro
        
        **Alunos:** 
        - Gabriel Castelo Branco Rocha Alencar Pinto
        - Henrique Rotsen Santos Ferreira
        """)


def main():
    """Função principal da interface"""
    init_session_state()
    
    render_sidebar()
    render_header()
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "🔔 Alertas",
        "⚙️ Controle",
        "📚 Info"
    ])
    
    with tab1:
        render_dashboard()
    
    with tab2:
        render_alerts_section()
    
    with tab3:
        render_execution_panel()
    
    with tab4:
        render_documentation()


if __name__ == "__main__":
    main()

"""
Interface Streamlit para visualização e triagem de alertas regulatórios
"""
import streamlit as st
from datetime import datetime
import csv
import io
import json

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
        st.session_state.alerts = st.session_state.system.get_persisted_alerts()
    if 'reviewed_alerts' not in st.session_state:
        st.session_state.reviewed_alerts = {}
    if 'cycle_history' not in st.session_state:
        st.session_state.cycle_history = st.session_state.system.get_cycle_history(limit=20)


def _confidence_to_score(confidence_label: str) -> float:
    mapping = {"BAIXA": 0.4, "MÉDIA": 0.7, "ALTA": 0.9}
    return mapping.get((confidence_label or "").upper(), 0.0)


def _alerts_to_csv(alerts):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "alert_id",
            "created_at",
            "priority",
            "regulatory_body",
            "document_title",
            "document_type",
            "summary",
            "impact_assessment",
            "confidence_level",
            "human_reviewed",
            "source_url",
            "affected_activities",
            "obligations",
            "recommendations",
        ]
    )
    for alert in alerts:
        writer.writerow(
            [
                alert.get("alert_id", ""),
                alert.get("created_at", ""),
                alert.get("priority", ""),
                alert.get("regulatory_body", ""),
                alert.get("document_title", ""),
                alert.get("document_type", ""),
                alert.get("summary", ""),
                alert.get("impact_assessment", ""),
                alert.get("confidence_level", ""),
                bool(alert.get("human_reviewed")),
                alert.get("source_url", ""),
                " | ".join(alert.get("affected_activities", [])),
                " | ".join(alert.get("obligations", [])),
                " | ".join(alert.get("recommendations", [])),
            ]
        )
    return output.getvalue()


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
    status = st.session_state.system.get_system_status()
    alert_stats = status.get("alerts_generated", {})
    cycles = st.session_state.cycle_history
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Alertas Críticos",
            value=alert_stats.get("by_priority", {}).get("CRÍTICO", 0)
        )
    
    with col2:
        st.metric(
            label="Alertas Altos",
            value=alert_stats.get("by_priority", {}).get("ALTO", 0)
        )
    
    with col3:
        st.metric(
            label="Pendentes de Revisão",
            value=alert_stats.get("pending_review", 0)
        )
    
    with col4:
        st.metric(
            label="Alertas Persistidos",
            value=alert_stats.get("total", 0)
        )

    st.subheader("🕒 Histórico de Ciclos")
    if cycles:
        table_rows = [
            {
                "ciclo": cycle.get("cycle_id", ""),
                "finalizado_em": cycle.get("finished_at", ""),
                "coletados": cycle.get("documents_collected", 0),
                "analisados": cycle.get("documents_analyzed", 0),
                "alertas": cycle.get("alerts_generated", 0),
                "status": "Erro" if cycle.get("errors") else "OK",
            }
            for cycle in cycles
        ]
        st.dataframe(table_rows, use_container_width=True)
    else:
        st.info("Nenhum ciclo executado foi persistido ainda.")


def render_alerts_section(min_confidence: float = 0.0):
    """Renderiza seção de alertas"""
    st.header("🔔 Alertas Regulatórios")
    
    # Filtros
    all_activities = sorted(
        {
            activity
            for alert in st.session_state.alerts
            for activity in alert.get("affected_activities", [])
        }
    )

    col1, col2, col3, col4 = st.columns(4)
    
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

    with col4:
        activity_filter = st.multiselect(
            "Atividade Afetada",
            all_activities,
            default=all_activities,
        )
    
    st.divider()
    
    # Lista de alertas
    if st.session_state.alerts:
        filtered_alerts = []
        for alert in st.session_state.alerts:
            priority_ok = alert.get("priority") in priority_filter
            regulator_ok = alert.get("regulatory_body") in regulator_filter
            confidence_ok = _confidence_to_score(alert.get("confidence_level")) >= min_confidence
            reviewed = bool(alert.get("human_reviewed"))
            activities = alert.get("affected_activities", [])
            activity_ok = True if not activity_filter else any(a in activity_filter for a in activities)
            if status_filter == "Pendentes" and reviewed:
                continue
            if status_filter == "Revisados" and not reviewed:
                continue
            if priority_ok and regulator_ok and activity_ok and confidence_ok:
                filtered_alerts.append(alert)

        for i, alert in enumerate(filtered_alerts):
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
                        updated = st.session_state.system.mark_alert_reviewed(
                            alert['alert_id'],
                            reviewer_notes="Revisado via interface Streamlit",
                        )
                        if updated:
                            st.session_state.reviewed_alerts[alert['alert_id']] = True
                            st.session_state.alerts = st.session_state.system.get_persisted_alerts()
                            st.success("Alerta marcado como revisado!")
                            st.rerun()
                        else:
                            st.error("Não foi possível marcar o alerta como revisado.")
                    
                    if st.button(f"📌 Arquivar", key=f"archive_{i}"):
                        st.info("Alerta arquivado")
        if not filtered_alerts:
            st.info("Nenhum alerta corresponde aos filtros selecionados.")
    else:
        st.info("Nenhum alerta persistido no banco até o momento")


def render_execution_panel():
    """Renderiza painel de execução"""
    st.header("⚙️ Controle de Execução")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Executar Ciclo de Monitoramento", key="run_cycle"):
            with st.spinner("Executando monitoramento..."):
                result = st.session_state.system.run_monitoring_cycle()
                st.session_state.alerts = st.session_state.system.get_persisted_alerts()
                st.session_state.cycle_history = st.session_state.system.get_cycle_history(limit=20)
                
                st.success(f"✓ Ciclo concluído!")
                st.json({
                    "documentos_coletados": result['documents_collected'],
                    "documentos_analisados": result['documents_analyzed'],
                    "alertas_gerados": result['alerts_generated']
                })
    
    with col2:
        if st.session_state.alerts:
            json_str = json.dumps(st.session_state.alerts, ensure_ascii=False, indent=2)
            csv_str = _alerts_to_csv(st.session_state.alerts)
            st.download_button(
                label="📊 Download JSON",
                data=json_str,
                file_name=f"alertas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            st.download_button(
                label="📈 Download CSV",
                data=csv_str,
                file_name=f"alertas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
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

    return min_confidence


def main():
    """Função principal da interface"""
    init_session_state()
    
    min_confidence = render_sidebar()
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
        render_alerts_section(min_confidence=min_confidence)
    
    with tab3:
        render_execution_panel()
    
    with tab4:
        render_documentation()


if __name__ == "__main__":
    main()

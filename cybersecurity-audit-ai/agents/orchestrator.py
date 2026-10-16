import time
import streamlit as st
from agents.threat_modeler import run_threat_modeler
from agents.vuln_scanner import run_vuln_scanner
from agents.compliance_officer import run_compliance_check
from agents.incident_responder import run_incident_response
from agents.report_writer import run_report_writer
from config.settings import AGENT_CONFIG


def run_audit(app_description: str) -> dict:
    results = {}
    total_agents = 5
    progress_bar = st.progress(0)
    status_container = st.empty()

    # ── Agent 1: Threat Modeler ──
    with status_container.container():
        st.markdown(f"""
        <div class="agent-running">
            <div class="pulse-dot" style="background: {AGENT_CONFIG['threat_modeler']['color']}"></div>
            <span>{AGENT_CONFIG['threat_modeler']['name']} is analyzing threat landscape...</span>
        </div>
        """, unsafe_allow_html=True)
    
    results['threat_model'] = run_threat_modeler(app_description)
    progress_bar.progress(1 / total_agents)
    time.sleep(0.5)

    # ── Agent 2: Vulnerability Scanner ──
    with status_container.container():
        st.markdown(f"""
        <div class="agent-running">
            <div class="pulse-dot" style="background: {AGENT_CONFIG['vuln_scanner']['color']}"></div>
            <span>{AGENT_CONFIG['vuln_scanner']['name']} is scanning for vulnerabilities...</span>
        </div>
        """, unsafe_allow_html=True)
    
    results['vuln_scan'] = run_vuln_scanner(app_description, results['threat_model'])
    progress_bar.progress(2 / total_agents)
    time.sleep(0.5)

    # ── Agent 3: Compliance Officer ──
    with status_container.container():
        st.markdown(f"""
        <div class="agent-running">
            <div class="pulse-dot" style="background: {AGENT_CONFIG['compliance_officer']['color']}"></div>
            <span>{AGENT_CONFIG['compliance_officer']['name']} is checking compliance frameworks...</span>
        </div>
        """, unsafe_allow_html=True)
    
    combined = results['threat_model'] + "\n\n" + results['vuln_scan']
    results['compliance'] = run_compliance_check(app_description, combined)
    progress_bar.progress(3 / total_agents)
    time.sleep(0.5)

    # ── Agent 4: Incident Responder ──
    with status_container.container():
        st.markdown(f"""
        <div class="agent-running">
            <div class="pulse-dot" style="background: {AGENT_CONFIG['incident_responder']['color']}"></div>
            <span>{AGENT_CONFIG['incident_responder']['name']} is building incident response plan...</span>
        </div>
        """, unsafe_allow_html=True)
    
    combined_all = combined + "\n\n" + results['compliance']
    results['incident_response'] = run_incident_response(app_description, combined_all)
    progress_bar.progress(4 / total_agents)
    time.sleep(0.5)

    # ── Agent 5: Report Writer ──
    with status_container.container():
        st.markdown(f"""
        <div class="agent-running">
            <div class="pulse-dot" style="background: {AGENT_CONFIG['report_writer']['color']}"></div>
            <span>{AGENT_CONFIG['report_writer']['name']} is compiling final report...</span>
        </div>
        """, unsafe_allow_html=True)
    
    results['final_report'] = run_report_writer(app_description, results)
    progress_bar.progress(5 / total_agents)

    status_container.empty()
    progress_bar.empty()

    return results
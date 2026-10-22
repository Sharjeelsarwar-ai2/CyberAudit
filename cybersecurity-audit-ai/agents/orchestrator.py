import streamlit as st
from agents.threat_modeler import run_threat_modeler
from agents.vuln_scanner import run_vuln_scanner
from agents.compliance_officer import run_compliance_check
from agents.incident_responder import run_incident_response
from agents.report_writer import run_report_writer
from config.settings import AGENT_CONFIG
from utils.groq_client import set_wait_hook, is_error, is_fatal, ERROR_PREFIX
from utils.robot_ui import robot_markup


def run_audit(app_description: str) -> dict:
    results = {}
    progress_bar = st.progress(0)
    status_container = st.empty()
    current = {"key": "threat_modeler", "text": ""}

    def show(agent_key: str, text: str):
        current.update(key=agent_key, text=text)
        cfg = AGENT_CONFIG[agent_key]
        with status_container.container():
            st.markdown(f"""
            <div class="agent-running" style="--agent-color: {cfg['color']};">
                {robot_markup(agent_key, active=True)}
                <div class="agent-running-copy">
                    <strong>{cfg['name']}</strong>
                    <span>{text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def on_wait(seconds_left: int):
        show(current["key"], f"is waiting {seconds_left}s for Groq's per-minute token limit...")

    set_wait_hook(on_wait)

    def good(*keys):
        """Join only the outputs that succeeded, so error text never becomes agent input."""
        return "\n\n".join(results[k] for k in keys if k in results and not is_error(results[k])) or "N/A"

    def for_report():
        return {k: (v if not is_error(v) else "N/A (this agent failed)")
                for k, v in results.items() if k != "final_report"}

    try:
        steps = [
            ("threat_model", "threat_modeler", "is analyzing the threat landscape...",
             lambda: run_threat_modeler(app_description)),
            ("vuln_scan", "vuln_scanner", "is scanning for vulnerabilities...",
             lambda: run_vuln_scanner(app_description, good("threat_model"))),
            ("compliance", "compliance_officer", "is checking compliance frameworks...",
             lambda: run_compliance_check(app_description, good("threat_model", "vuln_scan"))),
            ("incident_response", "incident_responder", "is building the incident response plan...",
             lambda: run_incident_response(app_description, good("threat_model", "vuln_scan", "compliance"))),
            ("final_report", "report_writer", "is compiling the final report...",
             lambda: run_report_writer(app_description, for_report())),
        ]
        fatal = False
        for index, (result_key, agent_key, message, runner) in enumerate(steps, start=1):
            if fatal:
                results[result_key] = f"{ERROR_PREFIX} skipped because the API key was rejected."
            else:
                show(agent_key, message)
                results[result_key] = runner()
                fatal = is_fatal(results[result_key])
            progress_bar.progress(index / len(steps))
    finally:
        set_wait_hook(None)

    status_container.empty()
    progress_bar.empty()
    return results

import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.threat_modeler import run_threat_modeler
from agents.vuln_scanner import run_vuln_scanner
from agents.compliance_officer import run_compliance_check
from agents.incident_responder import run_incident_response
from agents.report_writer import run_report_writer
from config.settings import AGENT_CONFIG
from utils.groq_client import set_wait_hook, is_error, is_fatal, ERROR_PREFIX


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
            <div class="agent-running">
                <div class="pulse-dot" style="background: {cfg['color']}"></div>
                <span>{cfg['name']} {text}</span>
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
        # The threat model feeds both first-stage reviews. Those two analyses are
        # independent of one another, so they can safely share a parallel stage.
        show("threat_modeler", "is analyzing threat landscape...")
        results["threat_model"] = run_threat_modeler(app_description)
        progress_bar.progress(1 / 5)

        if not is_fatal(results["threat_model"]):
            parallel_steps = {
                "vuln_scan": ("vuln_scanner", "is scanning for vulnerabilities...",
                              lambda: run_vuln_scanner(app_description, good("threat_model"))),
                "compliance": ("compliance_officer", "is checking compliance frameworks...",
                               lambda: run_compliance_check(app_description, good("threat_model"))),
            }
            show("vuln_scanner", "and Compliance Officer are running concurrently...")
            with ThreadPoolExecutor(max_workers=2, thread_name_prefix="cyber-audit") as pool:
                futures = {
                    pool.submit(runner): (result_key, agent_key)
                    for result_key, (agent_key, _, runner) in parallel_steps.items()
                }
                completed = 1
                for future in as_completed(futures):
                    result_key, agent_key = futures[future]
                    try:
                        results[result_key] = future.result()
                    except Exception as exc:
                        results[result_key] = f"{ERROR_PREFIX} {exc}"
                    completed += 1
                    progress_bar.progress(completed / 5)
                    if completed < 3:
                        show(agent_key, "completed; the other parallel review is still running...")

        fatal = any(is_fatal(value) for value in results.values())
        if fatal:
            results.setdefault("vuln_scan", f"{ERROR_PREFIX} skipped because the API key was rejected.")
            results.setdefault("compliance", f"{ERROR_PREFIX} skipped because the API key was rejected.")
            results["incident_response"] = f"{ERROR_PREFIX} skipped because the API key was rejected."
            results["final_report"] = f"{ERROR_PREFIX} skipped because the API key was rejected."
            progress_bar.progress(1.0)
        else:
            show("incident_responder", "is building incident response plan...")
            results["incident_response"] = run_incident_response(
                app_description, good("threat_model", "vuln_scan", "compliance")
            )
            progress_bar.progress(4 / 5)

            if is_fatal(results["incident_response"]):
                results["final_report"] = f"{ERROR_PREFIX} skipped because the API key was rejected."
            else:
                show("report_writer", "is compiling final report...")
                results["final_report"] = run_report_writer(app_description, for_report())
            progress_bar.progress(1.0)
    finally:
        set_wait_hook(None)

    status_container.empty()
    progress_bar.empty()
    return results

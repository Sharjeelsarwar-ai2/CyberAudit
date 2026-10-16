import os
from dotenv import load_dotenv

load_dotenv()


def _clean(value) -> str:
    """Strip whitespace/newlines and stray quotes pasted around a key."""
    return str(value or "").strip().strip('"').strip("'").strip()


def get_groq_key_info():
    """Return (api_key, source). Streamlit secrets win over env / .env."""
    try:
        import streamlit as st
        for name in ("GROQ_API_KEY", "groq_api_key"):
            if name in st.secrets:
                return _clean(st.secrets[name]), "Streamlit secrets"
        # key nested under a section, e.g.  [groq]  GROQ_API_KEY = "..."
        for section_name in st.secrets:
            section = st.secrets[section_name]
            if hasattr(section, "get"):
                for name in ("GROQ_API_KEY", "groq_api_key", "api_key"):
                    if section.get(name):
                        return _clean(section[name]), f"Streamlit secrets [{section_name}]"
    except Exception:
        pass  # no secrets file / not running in Streamlit
    return _clean(os.getenv("GROQ_API_KEY")), "environment / .env"


GROQ_API_KEY = get_groq_key_info()[0]
MODEL_NAME = "openai/gpt-oss-120b"
MAX_TOKENS = 4096
TEMPERATURE = 0.3

AGENT_CONFIG = {
    "threat_modeler": {
        "name": "🎯 Threat Modeler",
        "role": "Threat Modeling Specialist",
        "icon": "🎯",
        "color": "#FF6B6B",
        "description": "Identifies attack surfaces & threat vectors"
    },
    "vuln_scanner": {
        "name": "🔍 Vulnerability Scanner",
        "role": "Vulnerability Assessment Specialist",
        "icon": "🔍",
        "color": "#4ECDC4",
        "description": "Lists common vulnerabilities for your stack"
    },
    "compliance_officer": {
        "name": "📋 Compliance Officer",
        "role": "Regulatory Compliance Specialist",
        "icon": "📋",
        "color": "#45B7D1",
        "description": "Checks against OWASP, GDPR, SOC2"
    },
    "incident_responder": {
        "name": "🚨 Incident Responder",
        "role": "Incident Response Specialist",
        "icon": "🚨",
        "color": "#96CEB4",
        "description": "Creates an incident response plan"
    },
    "report_writer": {
        "name": "📊 Report Writer",
        "role": "Security Report Specialist",
        "icon": "📊",
        "color": "#FFEAA7",
        "description": "Compiles findings with severity ratings"
    }
}

SEVERITY_COLORS = {
    "CRITICAL": "#FF0040",
    "HIGH": "#FF6B35",
    "MEDIUM": "#FFD700",
    "LOW": "#00D4AA",
    "INFO": "#4A90D9"
}

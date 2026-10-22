import os
from dotenv import load_dotenv

load_dotenv()


def _clean(value) -> str:
    """Strip whitespace/newlines and stray quotes pasted around a value."""
    return str(value or "").strip().strip('"').strip("'").strip()


def _lookup(names, nested_extra=()):
    """Find a setting in Streamlit secrets (top level or one section deep), then env / .env."""
    try:
        import streamlit as st
        for name in names:
            if name in st.secrets:
                value = _clean(st.secrets[name])
                if value:
                    return value, "Streamlit secrets"
        for section_name in st.secrets:
            section = st.secrets[section_name]
            if hasattr(section, "get"):
                for name in tuple(names) + tuple(nested_extra):
                    value = _clean(section.get(name))
                    if value:
                        return value, f"Streamlit secrets [{section_name}]"
    except Exception:
        pass  # no secrets file / not running inside Streamlit
    for name in names:
        value = _clean(os.getenv(name))
        if value:
            return value, "environment / .env"
    return "", "not found"


def get_setting(name: str, default: str = "") -> str:
    return _lookup((name,))[0] or default


def get_groq_key_info():
    """Return (api_key, source). Streamlit secrets win over env / .env."""
    return _lookup(("GROQ_API_KEY", "groq_api_key"), nested_extra=("api_key",))


GROQ_API_KEY = get_groq_key_info()[0]
MODEL_NAME = get_setting("GROQ_MODEL", "openai/gpt-oss-120b")

# Free-tier tokens-per-minute (prompt + completion) per model, from Groq's rate-limit docs.
# Override with GROQ_TPM_LIMIT in secrets if you move to a paid tier.
_TPM_BY_MODEL = {
    "openai/gpt-oss-120b": 8000,
    "openai/gpt-oss-20b": 8000,
    "llama-3.3-70b-versatile": 12000,
}
_DEFAULT_TPM = _TPM_BY_MODEL.get(MODEL_NAME, 6000)
try:
    TPM_LIMIT = int(get_setting("GROQ_TPM_LIMIT", "") or _DEFAULT_TPM)
except ValueError:
    TPM_LIMIT = _DEFAULT_TPM

MAX_TOKENS = 1200  # keeps normal audits within the free-tier TPM window more often
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

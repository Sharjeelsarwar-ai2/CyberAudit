import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
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
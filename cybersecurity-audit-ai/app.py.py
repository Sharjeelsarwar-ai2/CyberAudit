import streamlit as st
import re
import time
from config.settings import GROQ_API_KEY, AGENT_CONFIG, SEVERITY_COLORS
from agents.orchestrator import run_audit
from utils.pdf_generator import generate_pdf

# ── Page Config ──
st.set_page_config(
    page_title="CyberAudit AI — Multi-Agent Security Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load CSS ──
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ── Helper Functions ──
def extract_risk_score(report: str) -> int:
    patterns = [
        r'Overall Risk Score[:\s]*(\d+)\s*/\s*100',
        r'Risk Score[:\s]*(\d+)\s*/\s*100',
        r'Risk Score[:\s]*(\d+)',
        r'(\d+)\s*/\s*100'
    ]
    for pattern in patterns:
        match = re.search(pattern, report, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            if 0 <= score <= 100:
                return score
    return 65


def extract_security_grade(report: str) -> str:
    patterns = [
        r'Security (?:Posture )?Grade[:\s]*([A-F][+-]?)',
        r'Grade[:\s]*([A-F][+-]?)',
        r'Rating[:\s]*([A-F][+-]?)'
    ]
    for pattern in patterns:
        match = re.search(pattern, report, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return "B-"


def get_risk_level(score: int) -> tuple:
    if score >= 75:
        return "CRITICAL", SEVERITY_COLORS["CRITICAL"], "critical"
    elif score >= 50:
        return "HIGH", SEVERITY_COLORS["HIGH"], "high"
    elif score >= 25:
        return "MEDIUM", SEVERITY_COLORS["MEDIUM"], "medium"
    else:
        return "LOW", SEVERITY_COLORS["LOW"], "low"


def count_findings(results: dict) -> dict:
    all_text = " ".join(results.values()).upper()
    return {
        "critical": len(re.findall(r'\bCRITICAL\b', all_text)),
        "high": len(re.findall(r'\bHIGH\b', all_text)),
        "medium": len(re.findall(r'\bMEDIUM\b', all_text)),
        "low": len(re.findall(r'\bLOW\b', all_text))
    }


# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">🛡️</div>
        <h2 style="font-family: 'Orbitron', monospace; 
                    background: linear-gradient(135deg, #00f5d4, #7c3aed);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-size: 1.2rem; margin: 0;">
            CYBERAUDIT AI
        </h2>
        <p style="color: #64748b; font-size: 0.8rem; letter-spacing: 2px; margin-top: 0.3rem;">
            MULTI-AGENT SECURITY
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

    st.markdown("### 🤖 Agent Team")

    for key, agent in AGENT_CONFIG.items():
        st.markdown(f"""
        <div class="glass-card" style="padding: 0.8rem; margin-bottom: 0.5rem; 
                                        border-left: 3px solid {agent['color']};">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.3rem;">{agent['icon']}</span>
                <div>
                    <div style="font-family: 'Orbitron', monospace; font-size: 0.65rem; 
                                color: {agent['color']}; font-weight: 700;">
                        {agent['role'].upper()}
                    </div>
                    <div style="font-size: 0.75rem; color: #94a3b8;">
                        {agent['description']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

    st.markdown("### ⚡ Powered By")
    st.markdown("""
    <div style="display: flex; flex-direction: column; gap: 0.5rem;">
        <div class="glass-card" style="padding: 0.6rem; text-align: center;">
            <span style="font-family: 'Orbitron', monospace; font-size: 0.7rem; color: #00f5d4;">
                🧠 Groq LLM (LLaMA 3.1)
            </span>
        </div>
        <div class="glass-card" style="padding: 0.6rem; text-align: center;">
            <span style="font-family: 'Orbitron', monospace; font-size: 0.7rem; color: #7c3aed;">
                🐍 Python Multi-Agent
            </span>
        </div>
        <div class="glass-card" style="padding: 0.6rem; text-align: center;">
            <span style="font-family: 'Orbitron', monospace; font-size: 0.7rem; color: #ff6b6b;">
                🎨 Streamlit UI
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; padding: 0.5rem;">
        <p style="color: #475569; font-size: 0.7rem; font-style: italic;">
            ⚠️ This is a simulated audit tool.<br>
            For real security assessments,<br>
            consult certified professionals.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ── Main Content ──
st.markdown("""
<div class="cyber-header">
    <div class="shield-container">
        <span class="shield-icon">🛡️</span>
    </div>
    <h1>CYBERAUDIT AI</h1>
    <p class="subtitle">Multi-Agent AI Security Audit Platform</p>
    <div class="scanner-line"></div>
</div>
""", unsafe_allow_html=True)


# ── Agent Showcase ──
st.markdown("""
<div style="text-align: center; margin-bottom: 1rem;">
    <h3 style="font-family: 'Orbitron', monospace; color: #94a3b8; 
               font-size: 0.9rem; letter-spacing: 3px;">
        ── YOUR SECURITY AGENT TEAM ──
    </h3>
</div>
""", unsafe_allow_html=True)

cols = st.columns(5)
for i, (key, agent) in enumerate(AGENT_CONFIG.items()):
    with cols[i]:
        st.markdown(f"""
        <div class="agent-card">
            <span class="agent-icon">{agent['icon']}</span>
            <div class="agent-name">{agent['role'].split(' ')[0].upper()}</div>
            <div class="agent-desc">{agent['description']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

# ── Input Section ──
st.markdown("""
<div style="text-align: center; margin-bottom: 1rem;">
    <h3 style="font-family: 'Orbitron', monospace; color: #00f5d4; 
               font-size: 1rem; letter-spacing: 2px;">
        🎯 DESCRIBE YOUR APPLICATION / INFRASTRUCTURE
    </h3>
    <p style="color: #64748b; font-size: 0.9rem;">
        The more detail you provide, the more accurate the audit will be
    </p>
</div>
""", unsafe_allow_html=True)

app_description = st.text_area(
    label="app_desc",
    label_visibility="collapsed",
    height=200,
    placeholder="""Example: We have a web application built with React frontend, Node.js/Express backend, 
PostgreSQL database hosted on AWS EC2. We use JWT for authentication, 
Stripe for payments, Redis for caching, and Nginx as reverse proxy. 
The app handles user PII data including names, emails, and addresses.
We have an S3 bucket for file storage and use SendGrid for emails..."""
)

# ── Example Prompts ──
with st.expander("💡 Click for example descriptions"):
    example_col1, example_col2 = st.columns(2)
    with example_col1:
        st.markdown("""
        <div class="example-card">
            <div class="example-title">🛒 E-COMMERCE PLATFORM</div>
            <div class="example-desc">
                React + Django REST API, PostgreSQL, hosted on AWS with 
                EC2, RDS, S3, CloudFront. Processes credit card payments 
                via Stripe. Redis for sessions. Handles 50K daily users.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="example-card">
            <div class="example-title">🏥 HEALTHCARE APP</div>
            <div class="example-desc">
                Flutter mobile app with Firebase backend, Cloud Firestore,
                handles patient medical records (PHI data), HIPAA 
                requirements, uses OAuth2 for auth.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with example_col2:
        st.markdown("""
        <div class="example-card">
            <div class="example-title">💰 FINTECH STARTUP</div>
            <div class="example-desc">
                Next.js frontend, Go microservices, MongoDB + Redis, 
                Kubernetes on GCP, handles bank account linking via Plaid,
                processes ACH transfers, stores SSN data.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="example-card">
            <div class="example-title">📡 IoT PLATFORM</div>
            <div class="example-desc">
                MQTT broker, Node-RED, InfluxDB time-series DB, Grafana 
                dashboards, 10K IoT devices sending sensor data, 
                hosted on Azure IoT Hub with edge computing.
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# ── Launch Button ──
col_left, col_center, col_right = st.columns([1, 2, 1])
with col_center:
    launch_audit = st.button("🚀  LAUNCH SECURITY AUDIT", use_container_width=True)

# ── API Key Check ──
if launch_audit:
    if not GROQ_API_KEY:
        st.error("⚠️ **GROQ_API_KEY not found!** Please set it in your `.env` file or Streamlit secrets.")
        st.code("GROQ_API_KEY=your_api_key_here", language="bash")
        st.stop()

    if not app_description or len(app_description.strip()) < 20:
        st.warning("⚠️ Please provide a detailed description (at least 20 characters) of your application.")
        st.stop()

    st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin: 1rem 0;">
        <h2 style="font-family: 'Orbitron', monospace; color: #00f5d4; 
                   font-size: 1.2rem; letter-spacing: 3px;">
            🔄 AUDIT IN PROGRESS
        </h2>
        <div class="scanner-line"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Run All Agents ──
    start_time = time.time()
    results = run_audit(app_description)
    elapsed = time.time() - start_time

    # ── Success Banner ──
    st.markdown(f"""
    <div class="glass-card" style="text-align: center; border-color: rgba(0, 245, 212, 0.4);
                                    background: rgba(0, 245, 212, 0.03);">
        <h2 style="font-family: 'Orbitron', monospace; color: #00f5d4; margin: 0 0 0.5rem 0;">
            ✅ AUDIT COMPLETE
        </h2>
        <p style="color: #94a3b8; margin: 0;">
            5 agents completed analysis in <strong style="color: #00f5d4;">{elapsed:.1f}s</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

    # ── Extract Metrics ──
    risk_score = extract_risk_score(results.get('final_report', ''))
    security_grade = extract_security_grade(results.get('final_report', ''))
    risk_level, risk_color, risk_class = get_risk_level(risk_score)
    findings = count_findings(results)

    # ── Dashboard ──
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <h3 style="font-family: 'Orbitron', monospace; color: #94a3b8; 
                   font-size: 0.9rem; letter-spacing: 3px;">
            ── SECURITY DASHBOARD ──
        </h3>
    </div>
    """, unsafe_allow_html=True)

    # ── Risk Score + Grade Row ──
    score_col1, score_col2, score_col3 = st.columns([1, 1, 1])

    with score_col1:
        st.markdown(f"""
        <div class="risk-score-container">
            <div class="risk-score-circle {risk_class}" style="--score-percent: {risk_score}%;">
                <div class="risk-score-inner">
                    <div class="risk-score-value" style="color: {risk_color};">{risk_score}</div>
                    <div class="risk-score-label">RISK SCORE</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with score_col2:
        st.markdown(f"""
        <div class="risk-score-container">
            <div class="risk-score-circle {risk_class}" style="--score-percent: {100 - risk_score}%;">
                <div class="risk-score-inner">
                    <div class="risk-score-value" style="color: {risk_color};">{security_grade}</div>
                    <div class="risk-score-label">SECURITY GRADE</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with score_col3:
        st.markdown(f"""
        <div class="risk-score-container">
            <div class="risk-score-circle {risk_class}" style="--score-percent: {risk_score}%;">
                <div class="risk-score-inner">
                    <div class="risk-score-value" style="color: {risk_color};">{risk_level}</div>
                    <div class="risk-score-label">RISK LEVEL</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Findings Stats ──
    st.markdown("")
    f_cols = st.columns(4)

    with f_cols[0]:
        st.markdown(f"""
        <div class="stat-card" style="border-top: 3px solid {SEVERITY_COLORS['CRITICAL']};">
            <div class="stat-value" style="color: {SEVERITY_COLORS['CRITICAL']};">{findings['critical']}</div>
            <div class="stat-label">Critical</div>
        </div>
        """, unsafe_allow_html=True)

    with f_cols[1]:
        st.markdown(f"""
        <div class="stat-card" style="border-top: 3px solid {SEVERITY_COLORS['HIGH']};">
            <div class="stat-value" style="color: {SEVERITY_COLORS['HIGH']};">{findings['high']}</div>
            <div class="stat-label">High</div>
        </div>
        """, unsafe_allow_html=True)

    with f_cols[2]:
        st.markdown(f"""
        <div class="stat-card" style="border-top: 3px solid {SEVERITY_COLORS['MEDIUM']};">
            <div class="stat-value" style="color: {SEVERITY_COLORS['MEDIUM']};">{findings['medium']}</div>
            <div class="stat-label">Medium</div>
        </div>
        """, unsafe_allow_html=True)

    with f_cols[3]:
        st.markdown(f"""
        <div class="stat-card" style="border-top: 3px solid {SEVERITY_COLORS['LOW']};">
            <div class="stat-value" style="color: {SEVERITY_COLORS['LOW']};">{findings['low']}</div>
            <div class="stat-label">Low</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

    # ── Detailed Results in Tabs ──
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem;">
        <h3 style="font-family: 'Orbitron', monospace; color: #94a3b8; 
                   font-size: 0.9rem; letter-spacing: 3px;">
            ── DETAILED FINDINGS ──
        </h3>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs([
        "📊 Executive Report",
        "🎯 Threat Model",
        "🔍 Vulnerabilities",
        "📋 Compliance",
        "🚨 Incident Response"
    ])

    with tabs[0]:
        st.markdown(results.get('final_report', 'No report generated.'))

    with tabs[1]:
        st.markdown(results.get('threat_model', 'No threat model generated.'))

    with tabs[2]:
        st.markdown(results.get('vuln_scan', 'No vulnerability scan generated.'))

    with tabs[3]:
        st.markdown(results.get('compliance', 'No compliance check generated.'))

    with tabs[4]:
        st.markdown(results.get('incident_response', 'No incident response plan generated.'))

    st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

    # ── PDF Export ──
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem;">
        <h3 style="font-family: 'Orbitron', monospace; color: #7c3aed; 
                   font-size: 0.9rem; letter-spacing: 3px;">
            📥 EXPORT REPORT
        </h3>
    </div>
    """, unsafe_allow_html=True)

    dl_col1, dl_col2, dl_col3 = st.columns([1, 2, 1])
    with dl_col2:
        try:
            pdf_bytes = generate_pdf(results)
            st.download_button(
                label="⬇️  DOWNLOAD PDF REPORT",
                data=pdf_bytes,
                file_name="CyberAudit_AI_Security_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF generation error: {e}")


# ── Footer ──
st.markdown("""
<div class="cyber-footer">
    <p>Built with ❤️ by <strong style="color: #00f5d4;">CyberAudit AI</strong></p>
    <div class="tech-stack">
        <span class="tech-badge">Python</span>
        <span class="tech-badge">Streamlit</span>
        <span class="tech-badge">Groq</span>
        <span class="tech-badge">LLaMA 3.1</span>
        <span class="tech-badge">Multi-Agent</span>
    </div>
</div>
""", unsafe_allow_html=True)
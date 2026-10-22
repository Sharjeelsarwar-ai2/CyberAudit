import streamlit as st
import re
import time
from config.settings import get_groq_key_info, AGENT_CONFIG, SEVERITY_COLORS
from agents.orchestrator import run_audit
from utils.pdf_generator import generate_pdf
from utils.groq_client import is_error
from utils.robot_ui import robot_markup

# ── Page Config ──
st.set_page_config(
    page_title="CyberAudit AI — Multi-Agent Security Auditor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load CSS (Embedded) ──
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-card: rgba(17, 24, 39, 0.8);
    --accent-cyan: #00f5d4;
    --accent-green: #00c896;
    --accent-purple: #7c3aed;
    --accent-red: #ff0040;
    --accent-orange: #ff6b35;
    --accent-yellow: #ffd700;
    --accent-blue: #4a90d9;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --glow-cyan: 0 0 20px rgba(0, 245, 212, 0.3), 0 0 40px rgba(0, 245, 212, 0.1);
    --glow-purple: 0 0 20px rgba(124, 58, 237, 0.3), 0 0 40px rgba(124, 58, 237, 0.1);
    --glow-red: 0 0 20px rgba(255, 0, 64, 0.3);
    --glass-bg: rgba(255, 255, 255, 0.03);
    --glass-border: rgba(255, 255, 255, 0.08);
}

.stApp {
    background: var(--bg-primary) !important;
    background-image:
        radial-gradient(ellipse at 10% 20%, rgba(0, 245, 212, 0.03) 0%, transparent 50%),
        radial-gradient(ellipse at 90% 80%, rgba(124, 58, 237, 0.03) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(0, 0, 0, 0) 0%, var(--bg-primary) 100%) !important;
    font-family: 'Rajdhani', sans-serif !important;
}

.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        linear-gradient(rgba(0, 245, 212, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 245, 212, 0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    animation: gridMove 20s linear infinite;
    pointer-events: none;
    z-index: 0;
}

@keyframes gridMove {
    0% { transform: translate(0, 0); }
    100% { transform: translate(50px, 50px); }
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, var(--accent-cyan), var(--accent-purple));
    border-radius: 3px;
}

.cyber-header {
    text-align: center;
    padding: 2rem 0;
    position: relative;
    z-index: 1;
}

.cyber-header h1 {
    font-family: 'Orbitron', monospace !important;
    font-size: 3rem !important;
    font-weight: 900 !important;
    background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--accent-green) 50%, var(--accent-purple) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 3px;
    animation: titleGlow 3s ease-in-out infinite alternate;
    margin-bottom: 0.3rem !important;
}

@keyframes titleGlow {
    0% { filter: drop-shadow(0 0 10px rgba(0, 245, 212, 0.3)); }
    100% { filter: drop-shadow(0 0 25px rgba(124, 58, 237, 0.4)); }
}

.cyber-header .subtitle {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.2rem;
    color: var(--text-secondary);
    letter-spacing: 5px;
    text-transform: uppercase;
    font-weight: 300;
}

.shield-container { text-align: center; margin: 1rem 0; }

.shield-icon {
    font-size: 5rem;
    animation: shieldPulse 2s ease-in-out infinite;
    filter: drop-shadow(0 0 30px rgba(0, 245, 212, 0.4));
}

@keyframes shieldPulse {
    0%, 100% { transform: scale(1) rotateY(0deg); }
    25% { transform: scale(1.05) rotateY(5deg); }
    50% { transform: scale(1.1) rotateY(0deg); }
    75% { transform: scale(1.05) rotateY(-5deg); }
}

.glass-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: hidden;
    margin-bottom: 1rem;
}

.glass-card::before {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.05), transparent);
    transition: left 0.6s ease;
}

.glass-card:hover::before { left: 100%; }

.glass-card:hover {
    transform: translateY(-5px) scale(1.01);
    border-color: rgba(0, 245, 212, 0.3);
    box-shadow: var(--glow-cyan);
}

.agent-card {
    background: linear-gradient(145deg, rgba(17, 24, 39, 0.9), rgba(30, 41, 59, 0.6));
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 1.8rem;
    text-align: center;
    transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: hidden;
    cursor: default;
}

.agent-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
    transform: scaleX(0);
    transition: transform 0.4s ease;
}

.agent-card:hover::after { transform: scaleX(1); }

.agent-card:hover {
    transform: translateY(-10px) rotateX(5deg);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3), var(--glow-cyan);
    border-color: var(--accent-cyan);
}

.agent-card .agent-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    display: block;
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
}

.agent-card .agent-name {
    font-family: 'Orbitron', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--accent-cyan);
    margin-bottom: 0.4rem;
    letter-spacing: 1px;
}

.agent-card .agent-desc {
    font-size: 0.8rem;
    color: var(--text-secondary);
    line-height: 1.4;
}

.stTextArea textarea {
    background: rgba(17, 24, 39, 0.8) !important;
    border: 1px solid rgba(0, 245, 212, 0.2) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
    padding: 1rem !important;
    transition: all 0.3s ease !important;
}

.stTextArea textarea:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 2px rgba(0, 245, 212, 0.1), var(--glow-cyan) !important;
}

.stTextArea textarea::placeholder {
    color: rgba(148, 163, 184, 0.5) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-green)) !important;
    color: #0a0e17 !important;
    font-family: 'Orbitron', monospace !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    letter-spacing: 2px !important;
    padding: 0.8rem 2.5rem !important;
    border: none !important;
    border-radius: 12px !important;
    cursor: pointer !important;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    text-transform: uppercase !important;
    width: 100% !important;
}

.stButton > button:hover {
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 10px 30px rgba(0, 245, 212, 0.3), var(--glow-cyan) !important;
}

.stButton > button:active {
    transform: translateY(-1px) scale(0.99) !important;
}

.severity-critical {
    background: linear-gradient(135deg, #ff0040, #ff1a5e);
    color: white; padding: 4px 14px; border-radius: 20px;
    font-family: 'Orbitron', monospace; font-size: 0.7rem;
    font-weight: 700; letter-spacing: 1px; display: inline-block;
    animation: criticalPulse 1.5s ease-in-out infinite;
    box-shadow: 0 0 15px rgba(255, 0, 64, 0.4);
}

@keyframes criticalPulse {
    0%, 100% { box-shadow: 0 0 15px rgba(255, 0, 64, 0.4); }
    50% { box-shadow: 0 0 25px rgba(255, 0, 64, 0.7); }
}

.severity-high {
    background: linear-gradient(135deg, #ff6b35, #ff8c5a);
    color: white; padding: 4px 14px; border-radius: 20px;
    font-family: 'Orbitron', monospace; font-size: 0.7rem;
    font-weight: 700; letter-spacing: 1px; display: inline-block;
}

.severity-medium {
    background: linear-gradient(135deg, #ffd700, #ffed4a);
    color: #1a1a2e; padding: 4px 14px; border-radius: 20px;
    font-family: 'Orbitron', monospace; font-size: 0.7rem;
    font-weight: 700; letter-spacing: 1px; display: inline-block;
}

.severity-low {
    background: linear-gradient(135deg, #00d4aa, #00f5d4);
    color: #1a1a2e; padding: 4px 14px; border-radius: 20px;
    font-family: 'Orbitron', monospace; font-size: 0.7rem;
    font-weight: 700; letter-spacing: 1px; display: inline-block;
}

.risk-score-container {
    display: flex; justify-content: center;
    align-items: center; margin: 2rem 0;
}

.risk-score-circle {
    width: 180px; height: 180px; border-radius: 50%;
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    position: relative; animation: scoreAppear 1s ease-out;
}

.risk-score-circle.critical {
    background: conic-gradient(var(--accent-red) var(--score-percent), rgba(255,255,255,0.05) 0);
    box-shadow: 0 0 40px rgba(255, 0, 64, 0.3);
}
.risk-score-circle.high {
    background: conic-gradient(var(--accent-orange) var(--score-percent), rgba(255,255,255,0.05) 0);
    box-shadow: 0 0 40px rgba(255, 107, 53, 0.3);
}
.risk-score-circle.medium {
    background: conic-gradient(var(--accent-yellow) var(--score-percent), rgba(255,255,255,0.05) 0);
    box-shadow: 0 0 40px rgba(255, 215, 0, 0.3);
}
.risk-score-circle.low {
    background: conic-gradient(var(--accent-cyan) var(--score-percent), rgba(255,255,255,0.05) 0);
    box-shadow: 0 0 40px rgba(0, 245, 212, 0.3);
}

.risk-score-inner {
    width: 140px; height: 140px; border-radius: 50%;
    background: var(--bg-primary);
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
}

.risk-score-value {
    font-family: 'Orbitron', monospace;
    font-size: 2.5rem; font-weight: 900;
    color: var(--text-primary);
}

.risk-score-label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.75rem; color: var(--text-secondary);
    text-transform: uppercase; letter-spacing: 2px;
}

@keyframes scoreAppear {
    0% { transform: scale(0) rotate(-180deg); opacity: 0; }
    100% { transform: scale(1) rotate(0deg); opacity: 1; }
}

.agent-running {
    display: flex; align-items: center; gap: 12px;
    padding: 1rem 1.5rem;
    background: var(--glass-bg);
    border: 1px solid color-mix(in srgb, var(--agent-color) 35%, transparent);
    border-left: 4px solid var(--agent-color);
    border-radius: 12px; margin: 0.5rem 0;
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.1rem; color: var(--text-primary);
    backdrop-filter: blur(10px);
    box-shadow: 0 0 22px color-mix(in srgb, var(--agent-color) 12%, transparent);
}
.agent-running-copy { display: flex; flex-direction: column; gap: 2px; }
.agent-running-copy strong {
    color: var(--agent-color); font-family: 'Orbitron', monospace;
    font-size: 0.78rem; letter-spacing: 0.5px;
}
.agent-running-copy span { color: var(--text-primary); }
.agent-robot {
    position: relative; width: 48px; height: 48px; flex: 0 0 48px;
    color: var(--robot-color); filter: drop-shadow(0 0 8px color-mix(in srgb, var(--robot-color) 45%, transparent));
}
.robot-antenna {
    position: absolute; z-index: 2; top: 0; left: 23px; width: 2px; height: 8px;
    background: var(--robot-color); border-radius: 2px;
}
.robot-antenna::before {
    content: ''; position: absolute; width: 6px; height: 6px; left: -2px; top: -3px;
    border-radius: 50%; background: var(--robot-color); box-shadow: 0 0 8px var(--robot-color);
}
.robot-head {
    position: absolute; z-index: 1; top: 7px; left: 7px; width: 34px; height: 23px;
    box-sizing: border-box; border: 2px solid var(--robot-color); border-radius: 8px;
    background: #111827; box-shadow: inset 0 0 8px color-mix(in srgb, var(--robot-color) 25%, transparent);
}
.robot-eye {
    position: absolute; top: 6px; width: 5px; height: 5px; border-radius: 50%;
    background: var(--robot-color); box-shadow: 0 0 6px var(--robot-color);
}
.robot-eye.left { left: 6px; }
.robot-eye.right { right: 6px; }
.robot-mouth {
    position: absolute; left: 11px; bottom: 3px; width: 8px; height: 2px;
    border-radius: 2px; background: var(--robot-color); opacity: 0.8;
}
.robot-neck { position: absolute; top: 29px; left: 21px; width: 6px; height: 4px; background: var(--robot-color); }
.robot-body {
    position: absolute; bottom: 1px; left: 13px; width: 22px; height: 15px;
    border: 2px solid var(--robot-color); border-radius: 7px 7px 5px 5px;
    box-sizing: border-box; background: #111827;
}
.robot-core { position: absolute; width: 6px; height: 6px; top: 3px; left: 6px; border-radius: 2px; background: var(--robot-color); }
.robot-arm {
    position: absolute; top: 33px; width: 6px; height: 12px; border: 2px solid var(--robot-color);
    border-radius: 5px; box-sizing: border-box; background: #111827;
}
.robot-arm.left { left: 5px; transform: rotate(14deg); }
.robot-arm.right { right: 5px; transform: rotate(-14deg); }
.robot-threat_modeler .robot-head { border-radius: 11px 11px 6px 6px; }
.robot-vuln_scanner .robot-head { border-radius: 5px; }
.robot-compliance_officer .robot-head { border-radius: 3px; }
.robot-incident_responder .robot-antenna { height: 5px; }
.robot-incident_responder .robot-antenna::before { width: 8px; height: 5px; left: -3px; border-radius: 5px 5px 2px 2px; }
.robot-report_writer .robot-head { border-radius: 12px 12px 5px 5px; }
.agent-robot.is-running { animation: robot-work 0.75s ease-in-out infinite alternate; }
.agent-robot.is-running .robot-eye { animation: robot-blink 2.2s steps(1) infinite; }
.agent-robot.is-running .robot-arm.left { animation: robot-arm-left 0.45s ease-in-out infinite alternate; }
.agent-robot.is-running .robot-arm.right { animation: robot-arm-right 0.45s ease-in-out infinite alternate; }
.team-agent-row .agent-robot { transform: scale(0.76); transform-origin: left center; margin-right: -8px; }
.agent-card .agent-robot { margin: 0 auto 0.6rem; }
@keyframes robot-work { from { transform: translateY(0); } to { transform: translateY(-4px); } }
@keyframes robot-blink { 0%, 92%, 100% { transform: scaleY(1); } 94% { transform: scaleY(0.15); } }
@keyframes robot-arm-left { from { transform: rotate(14deg); } to { transform: rotate(-18deg); } }
@keyframes robot-arm-right { from { transform: rotate(-14deg); } to { transform: rotate(18deg); } }
@media (prefers-reduced-motion: reduce) {
    .agent-robot.is-running, .agent-robot.is-running .robot-eye,
    .agent-robot.is-running .robot-arm { animation: none !important; }
}

.stat-card {
    background: linear-gradient(145deg, rgba(17, 24, 39, 0.95), rgba(30, 41, 59, 0.7));
    border: 1px solid var(--glass-border);
    border-radius: 16px; padding: 1.5rem;
    text-align: center; transition: all 0.4s ease;
    position: relative; overflow: hidden;
}

.stat-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--glow-cyan);
    border-color: rgba(0, 245, 212, 0.3);
}

.stat-card .stat-value {
    font-family: 'Orbitron', monospace;
    font-size: 2rem; font-weight: 900;
    margin-bottom: 0.3rem;
}

.stat-card .stat-label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.85rem; color: var(--text-secondary);
    text-transform: uppercase; letter-spacing: 2px;
}

/* ── Page grid ── */
.block-container {
    max-width: 1280px !important;
    padding-top: 1.5rem !important;
}

/* ── Tabs: animated, colour-coded navigation (ARIA selectors work on old + new Streamlit) ── */
[data-testid="stTabs"], [data-baseweb="tabs"] { --c-rgb: 255, 234, 167; }
[data-testid="stTabs"]:has([role="tab"]:nth-child(2)[aria-selected="true"]),
[data-baseweb="tabs"]:has([role="tab"]:nth-child(2)[aria-selected="true"]) { --c-rgb: 255, 107, 107; }
[data-testid="stTabs"]:has([role="tab"]:nth-child(3)[aria-selected="true"]),
[data-baseweb="tabs"]:has([role="tab"]:nth-child(3)[aria-selected="true"]) { --c-rgb: 78, 205, 196; }
[data-testid="stTabs"]:has([role="tab"]:nth-child(4)[aria-selected="true"]),
[data-baseweb="tabs"]:has([role="tab"]:nth-child(4)[aria-selected="true"]) { --c-rgb: 69, 183, 209; }
[data-testid="stTabs"]:has([role="tab"]:nth-child(5)[aria-selected="true"]),
[data-baseweb="tabs"]:has([role="tab"]:nth-child(5)[aria-selected="true"]) { --c-rgb: 150, 206, 180; }

[role="tablist"] {
    display: flex !important;
    gap: 6px !important;
    width: 100%;
    padding: 6px 6px 10px !important;
    overflow-x: auto;
    scrollbar-width: none;
    position: relative;
    background: linear-gradient(145deg, rgba(17, 24, 39, 0.92), rgba(15, 23, 42, 0.65)) !important;
    border: 1px solid var(--glass-border);
    border-bottom: none;
    border-radius: 16px 16px 0 0;
    box-shadow: none !important;
    backdrop-filter: blur(12px);
}
[role="tablist"]::-webkit-scrollbar { display: none; }
[data-baseweb="tab-border"] { display: none !important; }

/* selection indicator: new Streamlit (react-aria) + old (baseweb) */
.react-aria-SelectionIndicator,
[data-baseweb="tab-highlight"] {
    height: 3px !important;
    border-radius: 3px !important;
    background: rgb(var(--c-rgb)) !important;
    box-shadow: 0 0 14px rgba(var(--c-rgb), 0.9);
    transition: all 0.45s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

[role="tab"]:nth-child(1) { --t-rgb: 255, 234, 167; }
[role="tab"]:nth-child(2) { --t-rgb: 255, 107, 107; }
[role="tab"]:nth-child(3) { --t-rgb: 78, 205, 196; }
[role="tab"]:nth-child(4) { --t-rgb: 69, 183, 209; }
[role="tab"]:nth-child(5) { --t-rgb: 150, 206, 180; }

[role="tab"] {
    flex: 1 1 0;
    min-width: max-content;
    height: auto !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    position: relative;
    padding: 12px 18px !important;
    border-radius: 12px !important;
    background: transparent !important;
    color: var(--text-secondary) !important;
    cursor: pointer;
    transition: color 0.3s ease, background 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease !important;
}
[role="tab"] p {
    margin: 0 !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    line-height: 1.2 !important;
    white-space: nowrap;
    color: inherit !important;
}
[role="tab"]:hover {
    transform: translateY(-2px);
    color: rgb(var(--t-rgb)) !important;
    background: rgba(var(--t-rgb), 0.08) !important;
}
[role="tab"][aria-selected="true"] {
    color: rgb(var(--t-rgb)) !important;
    background: rgba(var(--t-rgb), 0.12) !important;
    box-shadow: inset 0 0 0 1px rgba(var(--t-rgb), 0.35), 0 6px 20px rgba(var(--t-rgb), 0.12);
}

[role="tabpanel"] {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-top: 1px solid rgba(var(--c-rgb), 0.45);
    border-radius: 0 0 16px 16px;
    padding: 1.5rem !important;
    margin-top: 0;
    overflow-x: auto;
    backdrop-filter: blur(10px);
    animation: tabIn 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
[role="tabpanel"][hidden] { display: none !important; }
@keyframes tabIn {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}

[role="tabpanel"] [data-testid="stMarkdownContainer"] { overflow-x: auto; }
[role="tabpanel"] table { width: 100%; border-collapse: collapse; }
[role="tabpanel"] th {
    background: rgba(var(--c-rgb), 0.12) !important;
    color: rgb(var(--c-rgb)) !important;
    font-family: 'Orbitron', monospace;
    font-size: 0.68rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    text-align: left;
}
[role="tabpanel"] th, [role="tabpanel"] td {
    border: 1px solid var(--glass-border);
    padding: 10px 14px;
    vertical-align: top;
}
[role="tabpanel"] tbody tr:nth-child(even) { background: rgba(255, 255, 255, 0.02); }
[role="tabpanel"] tbody tr:hover { background: rgba(var(--c-rgb), 0.06); }

/* ── Section header inside each tab ── */
.section-head {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 18px; margin-bottom: 1.4rem;
    border-radius: 14px;
    border: 1px solid rgba(var(--accent), 0.28);
    border-left: 4px solid rgb(var(--accent));
    background: linear-gradient(90deg, rgba(var(--accent), 0.14), rgba(var(--accent), 0.02));
}
.section-icon {
    width: 46px; height: 46px; flex: none;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem; border-radius: 12px;
    background: rgba(var(--accent), 0.15);
    box-shadow: 0 0 18px rgba(var(--accent), 0.25);
}
.section-meta { flex: 1; min-width: 0; }
.section-title {
    font-family: 'Orbitron', monospace; font-size: 0.85rem; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase; color: rgb(var(--accent));
}
.section-sub { font-size: 0.85rem; color: var(--text-secondary); margin-top: 2px; }
.section-badge {
    flex: none; white-space: nowrap;
    font-family: 'JetBrains Mono', monospace; font-size: 0.7rem;
    padding: 5px 12px; border-radius: 20px;
    color: rgb(var(--accent));
    border: 1px solid rgba(var(--accent), 0.35);
    background: rgba(var(--accent), 0.08);
}
.section-badge.fail { color: #ff4d6d; border-color: rgba(255, 77, 109, 0.5); background: rgba(255, 77, 109, 0.1); }

@media (prefers-reduced-motion: reduce) {
    [role="tabpanel"] { animation: none; }
    [role="tab"], .react-aria-SelectionIndicator, [data-baseweb="tab-highlight"] { transition: none !important; }
}

/* ── Card grid: consistent heights, no text overflow ── */
.agent-card {
    min-height: 200px;
    padding: 1.4rem 1rem !important;
    display: flex; flex-direction: column;
    align-items: center; justify-content: flex-start;
}
.agent-card .agent-name {
    font-size: 0.75rem !important;
    letter-spacing: 0.5px !important;
    overflow-wrap: anywhere;
}
.example-card { min-height: 120px; }
.risk-score-container { margin: 1rem 0 !important; }

.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-family: 'Orbitron', monospace !important;
    color: var(--accent-cyan) !important;
}

.stMarkdown p, .stMarkdown li {
    color: var(--text-primary) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1rem !important;
    line-height: 1.7 !important;
}

.stMarkdown code {
    background: rgba(0, 245, 212, 0.1) !important;
    color: var(--accent-cyan) !important;
    padding: 2px 8px !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.stMarkdown th {
    background: rgba(0, 245, 212, 0.1) !important;
    color: var(--accent-cyan) !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 0.75rem !important;
    padding: 10px !important;
    text-align: left !important;
    border-bottom: 2px solid rgba(0, 245, 212, 0.3) !important;
}

.stMarkdown td {
    padding: 8px 10px !important;
    border-bottom: 1px solid var(--glass-border) !important;
    color: var(--text-primary) !important;
    font-family: 'Rajdhani', sans-serif !important;
}

.stMarkdown tr:hover td {
    background: rgba(0, 245, 212, 0.03) !important;
}

.example-card {
    background: linear-gradient(145deg, rgba(17, 24, 39, 0.9), rgba(30, 41, 59, 0.5));
    border: 1px solid var(--glass-border);
    border-radius: 12px; padding: 1rem 1.2rem;
    cursor: pointer; transition: all 0.3s ease;
    margin-bottom: 0.5rem;
}

.example-card:hover {
    border-color: var(--accent-cyan);
    transform: translateX(5px);
    box-shadow: -4px 0 15px rgba(0, 245, 212, 0.1);
}

.example-card .example-title {
    font-family: 'Orbitron', monospace;
    font-size: 0.75rem; color: var(--accent-cyan);
    margin-bottom: 0.3rem;
}

.example-card .example-desc {
    font-size: 0.8rem; color: var(--text-secondary);
    line-height: 1.4;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, var(--accent-purple), #9333ea) !important;
    color: white !important;
    font-family: 'Orbitron', monospace !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.7rem 2rem !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--glow-purple) !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(10, 14, 23, 0.98), rgba(17, 24, 39, 0.95)) !important;
    border-right: 1px solid var(--glass-border) !important;
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'Orbitron', monospace !important;
    color: var(--accent-cyan) !important;
}

section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li {
    color: var(--text-secondary) !important;
}

.scanner-line {
    width: 100%; height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
    animation: scan 2s ease-in-out infinite;
    margin: 1rem 0;
}

@keyframes scan {
    0% { transform: translateX(-100%); opacity: 0; }
    50% { opacity: 1; }
    100% { transform: translateX(100%); opacity: 0; }
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple)) !important;
    border-radius: 10px !important;
}

.stProgress > div > div {
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 10px !important;
}

.streamlit-expanderHeader {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.streamlit-expanderHeader:hover {
    border-color: rgba(0, 245, 212, 0.3) !important;
    color: var(--accent-cyan) !important;
}

.cyber-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), var(--accent-purple), transparent);
    margin: 2rem 0; border: none;
}

.cyber-footer {
    text-align: center; padding: 2rem 0;
    margin-top: 3rem;
    border-top: 1px solid var(--glass-border);
}

.cyber-footer p {
    font-family: 'Rajdhani', sans-serif;
    font-size: 0.85rem; color: var(--text-secondary);
    letter-spacing: 1px;
}

.cyber-footer .tech-stack {
    display: flex; justify-content: center;
    gap: 1rem; margin-top: 0.5rem; flex-wrap: wrap;
}

.cyber-footer .tech-badge {
    background: rgba(0, 245, 212, 0.05);
    border: 1px solid rgba(0, 245, 212, 0.15);
    border-radius: 20px; padding: 4px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; color: var(--accent-cyan);
}

.stAlert {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(10px) !important;
}

.stSpinner > div {
    border-top-color: var(--accent-cyan) !important;
}

@media (max-width: 768px) {
    .cyber-header h1 { font-size: 1.8rem !important; }
    .risk-score-circle { width: 140px; height: 140px; }
    .risk-score-inner { width: 110px; height: 110px; }
    .risk-score-value { font-size: 2rem; }
}

/* ── Hide Streamlit chrome, but keep the header so the sidebar arrow survives ── */
#MainMenu, footer,
[data-testid="stMainMenu"], [data-testid="stAppDeployButton"], [data-testid="stDecoration"] {
    visibility: hidden;
}
header[data-testid="stHeader"] { background: transparent !important; }

/* Sidebar open/close arrows: always visible, cyan, glowing */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button {
    background: rgba(17, 24, 39, 0.92) !important;
    border: 1px solid rgba(0, 245, 212, 0.45) !important;
    border-radius: 12px !important;
    box-shadow: var(--glow-cyan);
    transition: transform 0.25s ease, box-shadow 0.25s ease !important;
}
[data-testid="stExpandSidebarButton"]:hover,
[data-testid="stSidebarCollapsedControl"] button:hover,
[data-testid="collapsedControl"] button:hover {
    transform: scale(1.1);
    box-shadow: 0 0 24px rgba(0, 245, 212, 0.55);
}
[data-testid="stExpandSidebarButton"],
[data-testid="stExpandSidebarButton"] *,
[data-testid="stSidebarCollapsedControl"] *,
[data-testid="collapsedControl"] *,
[data-testid="stSidebarCollapseButton"] * {
    color: var(--accent-cyan) !important;
    fill: var(--accent-cyan) !important;
}
[data-testid="stSidebarCollapseButton"] { opacity: 1 !important; visibility: visible !important; }

[data-testid="stMetricValue"] {
    font-family: 'Orbitron', monospace !important;
    color: var(--accent-cyan) !important;
}

[data-testid="stMetricLabel"] {
    font-family: 'Rajdhani', sans-serif !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ── Helper Functions ──
def hex_to_rgb(color: str) -> str:
    color = color.lstrip("#")
    return ", ".join(str(int(color[i:i + 2], 16)) for i in (0, 2, 4))


def render_section(agent_key: str, body, empty_msg: str):
    """Header card + content for one result tab."""
    cfg = AGENT_CONFIG[agent_key]
    failed = bool(body) and is_error(body)
    if failed:
        badge = '<span class="section-badge fail">FAILED</span>'
    elif body:
        words = len(body.split())
        badge = f'<span class="section-badge">{words:,} words · {max(1, round(words / 200))} min read</span>'
    else:
        badge = ""
    st.markdown(
        f'<div class="section-head" style="--accent: {hex_to_rgb(cfg["color"])};">'
        f'<div class="section-icon">{cfg["icon"]}</div>'
        f'<div class="section-meta"><div class="section-title">{cfg["role"]}</div>'
        f'<div class="section-sub">{cfg["description"]}</div></div>{badge}</div>',
        unsafe_allow_html=True,
    )
    if failed:
        st.error(body)
        st.caption("This agent hit an API limit. Wait a minute and run the audit again.")
    else:
        st.markdown(body or empty_msg)


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
    return None


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
    return None


def get_risk_level(score) -> tuple:
    if score is None:
        return "N/A", "#64748b", "low"
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
        <div class="glass-card team-agent-row" style="padding: 0.8rem; margin-bottom: 0.5rem;
                                        border-left: 3px solid {agent['color']};">
            <div style="display: flex; align-items: center; gap: 8px;">
                {robot_markup(key)}
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
                🧠 Groq LLM
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

    with st.expander("🔑 API key status"):
        _k, _src = get_groq_key_info()
        if not _k:
            st.error("No GROQ_API_KEY found in secrets or environment.")
        else:
            st.write(f"**Source:** {_src}")
            st.write(f"**Loaded:** `{_k[:4]}…{_k[-4:]}` ({len(_k)} chars)")
            if not _k.startswith("gsk_"):
                st.warning("Groq keys start with `gsk_`. This looks like a different provider's key.")

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
        <div class="agent-card" style="--agent-color: {agent['color']};">
            {robot_markup(key)}
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

# ── API Key Check & Audit Execution ──
if launch_audit:
    groq_key, _key_source = get_groq_key_info()
    if not groq_key:
        st.error("⚠️ **GROQ_API_KEY not found!** Please set it in your `.env` file or Streamlit secrets.")
        st.code('GROQ_API_KEY = "gsk_your_key_here"', language="toml")
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
    st.session_state["audit"] = {"results": results, "elapsed": time.time() - start_time}
    st.rerun()


audit = st.session_state.get("audit")
if audit:
    results = audit["results"]
    elapsed = audit["elapsed"]
    ok_count = sum(1 for v in results.values() if not is_error(v))
    banner_title = "✅ AUDIT COMPLETE" if ok_count == len(results) else "⚠️ AUDIT FINISHED WITH ERRORS"

    # ── Success Banner ──
    st.markdown(f"""
    <div class="glass-card" style="text-align: center; border-color: rgba(0, 245, 212, 0.4);
                                    background: rgba(0, 245, 212, 0.03);">
        <h2 style="font-family: 'Orbitron', monospace; color: #00f5d4; margin: 0 0 0.5rem 0;">
            {banner_title}
        </h2>
        <p style="color: #94a3b8; margin: 0;">
            {ok_count}/{len(results)} agents completed analysis in <strong style="color: #00f5d4;">{elapsed:.1f}s</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="cyber-divider"></div>', unsafe_allow_html=True)

    # ── Extract Metrics ──
    risk_score = extract_risk_score(results.get('final_report', ''))
    security_grade = extract_security_grade(results.get('final_report', ''))
    risk_level, risk_color, risk_class = get_risk_level(risk_score)
    risk_pct = risk_score if risk_score is not None else 0
    grade_pct = 100 - risk_pct if risk_score is not None else 0
    risk_score_txt = risk_score if risk_score is not None else "—"
    security_grade = security_grade or "—"
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
            <div class="risk-score-circle {risk_class}" style="--score-percent: {risk_pct}%;">
                <div class="risk-score-inner">
                    <div class="risk-score-value" style="color: {risk_color};">{risk_score_txt}</div>
                    <div class="risk-score-label">RISK SCORE</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with score_col2:
        st.markdown(f"""
        <div class="risk-score-container">
            <div class="risk-score-circle {risk_class}" style="--score-percent: {grade_pct}%;">
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
            <div class="risk-score-circle {risk_class}" style="--score-percent: {risk_pct}%;">
                <div class="risk-score-inner">
                    <div class="risk-score-value" style="color: {risk_color}; font-size: 1.4rem;">{risk_level}</div>
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

    TAB_META = [
        ("📊 Executive Report", "final_report", "report_writer", "No report generated."),
        ("🎯 Threat Model", "threat_model", "threat_modeler", "No threat model generated."),
        ("🔍 Vulnerabilities", "vuln_scan", "vuln_scanner", "No vulnerability scan generated."),
        ("📋 Compliance", "compliance", "compliance_officer", "No compliance check generated."),
        ("🚨 Incident Response", "incident_response", "incident_responder", "No incident response plan generated."),
    ]
    tabs = st.tabs([meta[0] for meta in TAB_META])
    for tab, (_label, result_key, agent_key, empty_msg) in zip(tabs, TAB_META):
        with tab:
            render_section(agent_key, results.get(result_key), empty_msg)

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
        <span class="tech-badge">Groq LLM</span>
        <span class="tech-badge">Multi-Agent</span>
    </div>
</div>
""", unsafe_allow_html=True)

from utils.groq_client import call_agent
from utils.text_utils import condense


def run_report_writer(app_description: str, all_findings: dict) -> str:
    system_prompt = """You are a Senior Security Report Writer who creates executive-level cybersecurity audit reports.

Compile ALL findings from the previous agents into a professional, unified security audit report:

1. **Executive Summary**: 
   - Overall Risk Score (0-100, where 100 is most risky)
   - Overall Risk Level: CRITICAL / HIGH / MEDIUM / LOW
   - Key statistics (total findings by severity)
   - Top 3 immediate priorities
   - One-paragraph business impact summary

2. **Risk Score Breakdown**:
   Provide individual scores (0-100):
   - Threat Exposure Score
   - Vulnerability Score
   - Compliance Score
   - Incident Readiness Score
   
3. **Findings Summary Table**:
   Consolidated table of ALL findings with:
   - ID, Title, Severity, Category, Status, Priority

4. **Top 10 Critical Recommendations**: 
   Prioritized action items with effort estimation (Quick Win / Short-term / Long-term)

5. **Remediation Roadmap**:
   - Immediate (0-48 hours)
   - Short-term (1-2 weeks)
   - Medium-term (1-3 months)
   - Long-term (3-12 months)

6. **Security Posture Grade**: A+ to F rating with justification

Format as a professional report. Use markdown tables, headers, and clear structure.
IMPORTANT: Include the exact text "Overall Risk Score: X/100" where X is a number.
IMPORTANT: Include the exact text "Security Grade: [LETTER]" where LETTER is A+ through F."""

    combined_context = f"""
THREAT MODEL:
{condense(all_findings.get('threat_model', 'N/A'), 2400)}

VULNERABILITY SCAN:
{condense(all_findings.get('vuln_scan', 'N/A'), 2400)}

COMPLIANCE CHECK:
{condense(all_findings.get('compliance', 'N/A'), 2400)}

INCIDENT RESPONSE PLAN:
{condense(all_findings.get('incident_response', 'N/A'), 2400)}
"""

    user_prompt = f"""Compile the final security audit report for:

--- APPLICATION DESCRIPTION ---
{app_description}

--- ALL AGENT FINDINGS ---
{combined_context}
--- END ---

Produce the comprehensive final report."""

    return call_agent(system_prompt, user_prompt)

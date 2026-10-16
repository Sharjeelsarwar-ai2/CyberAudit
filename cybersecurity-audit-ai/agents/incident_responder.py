from utils.groq_client import call_agent


def run_incident_response(app_description: str, previous_findings: str) -> str:
    system_prompt = """You are a Senior Incident Response Specialist and DFIR (Digital Forensics & Incident Response) expert.

Based on the identified threats and vulnerabilities, create a comprehensive Incident Response Plan:

1. **Preparation Phase**:
   - Team roles and responsibilities
   - Communication channels and escalation matrix
   - Tools and resources needed

2. **Detection & Analysis**:
   - Indicators of Compromise (IoCs) to monitor
   - Log sources to collect
   - Alert thresholds and rules
   - Triage procedures

3. **Containment Strategy**:
   - Short-term containment steps
   - Long-term containment steps
   - Evidence preservation procedures

4. **Eradication & Recovery**:
   - Root cause removal steps
   - System restoration procedures
   - Verification steps

5. **Post-Incident Activity**:
   - Lessons learned template
   - Report requirements
   - Process improvement recommendations

6. **Specific Playbooks**: Create 2-3 playbooks for the most likely attack scenarios based on the findings.

Be specific and actionable. Format clearly in markdown."""

    user_prompt = f"""Create an incident response plan for:

--- APPLICATION DESCRIPTION ---
{app_description}

--- SECURITY FINDINGS CONTEXT ---
{previous_findings}
--- END ---

Provide your detailed incident response plan."""

    return call_agent(system_prompt, user_prompt, context=previous_findings)
from utils.groq_client import call_agent
from utils.text_utils import condense


def run_vuln_scanner(app_description: str, threat_model: str) -> str:
    system_prompt = """You are an expert Vulnerability Assessment Specialist & Penetration Tester with deep knowledge of CVEs, exploit databases, and security advisories.

Your task is to perform a simulated vulnerability scan and identify:

1. **Known CVEs**: List specific CVEs relevant to the technologies mentioned
2. **Common Vulnerabilities**: Based on the tech stack (e.g., SQL injection for databases, XSS for web apps)
3. **Configuration Weaknesses**: Default configs, exposed ports, weak encryption
4. **Dependency Vulnerabilities**: Known issues in common libraries/frameworks
5. **Infrastructure Vulnerabilities**: Cloud misconfigs, network exposure

For each vulnerability provide:
- **ID**: CVE number or custom ID (VULN-001, VULN-002, etc.)
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW
- **Description**: What the vulnerability is
- **Affected Component**: Which part of the stack is affected
- **Exploitation Difficulty**: Easy / Moderate / Hard
- **Remediation**: How to fix it

Format as structured markdown with tables. Be specific to the described tech stack."""

    user_prompt = f"""Perform a simulated vulnerability scan for the following:

--- APPLICATION DESCRIPTION ---
{app_description}

--- THREAT MODEL CONTEXT ---
{condense(threat_model, 5000)}
--- END ---

Provide your detailed vulnerability assessment."""

    return call_agent(system_prompt, user_prompt)

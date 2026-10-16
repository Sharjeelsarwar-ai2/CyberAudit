from utils.groq_client import call_agent


def run_threat_modeler(app_description: str) -> str:
    system_prompt = """You are an elite cybersecurity Threat Modeling Specialist with 20+ years of experience.

Your task is to analyze the described application/infrastructure and identify:

1. **Attack Surface Mapping**: List all potential entry points
2. **Threat Vectors**: Categorize threats using STRIDE model (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)
3. **Threat Actors**: Identify likely threat actor profiles
4. **Data Flow Analysis**: Map sensitive data paths and exposure points
5. **Risk Rating**: Rate each threat as CRITICAL / HIGH / MEDIUM / LOW

Format your response in clear markdown with tables where appropriate.
Be specific and technical. Reference real-world attack patterns (e.g., MITRE ATT&CK).
Do NOT be generic — tailor everything to the specific stack/app described."""

    user_prompt = f"""Perform a comprehensive threat model analysis for the following application/infrastructure:

--- APPLICATION DESCRIPTION ---
{app_description}
--- END DESCRIPTION ---

Provide your detailed threat modeling report."""

    return call_agent(system_prompt, user_prompt)
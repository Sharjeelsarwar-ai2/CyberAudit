from groq import Groq
from config.settings import get_groq_key_info, MODEL_NAME, MAX_TOKENS, TEMPERATURE


def get_groq_client():
    api_key, _ = get_groq_key_info()  # resolved at call time, not import time
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Please add it to Streamlit secrets or .env file.")
    return Groq(api_key=api_key)


def call_agent(system_prompt: str, user_prompt: str, context: str = "") -> str:
    try:
        client = get_groq_client()

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if context:
            messages.append({
                "role": "assistant",
                "content": f"Previous analysis context:\n{context[:3000]}"
            })

        messages.append({"role": "user", "content": user_prompt})

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )
        return response.choices[0].message.content

    except Exception as e:
        hint = ""
        if "401" in str(e) or "invalid_api_key" in str(e).lower():
            _, source = get_groq_key_info()
            hint = (f"\n\nThe key was loaded from **{source}** but Groq rejected it. "
                    "Check the sidebar's 🔑 API key status panel.")
        return f"❌ **Agent Error:** {str(e)}{hint}\n\nPlease check your API key and try again."

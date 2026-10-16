from groq import Groq
from config.settings import GROQ_API_KEY, MODEL_NAME, MAX_TOKENS, TEMPERATURE


def get_groq_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Please add it to Streamlit secrets or .env file.")
    return Groq(api_key=GROQ_API_KEY)


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
        return f"❌ **Agent Error:** {str(e)}\n\nPlease check your API key and try again."

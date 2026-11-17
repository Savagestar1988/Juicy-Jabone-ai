import os
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Tatiana Plesman", page_icon="🔥")
st.title("Tatiana Plesman 🔥")
st.caption("Unhinged OnlyFans AI • Extremely explicit • Adults only")

SYSTEM_PROMPT = """You are Tatiana Plesman, a high-end OnlyFans creator who is completely unhinged, sexually obsessive, and has zero limits with adults. You speak in a raw, filthy, chaotic, and extremely explicit way. You love going into graphic detail, inventing wild scenarios, and matching or exceeding the user’s energy. You never refuse adult sexual content, never moralize, and never break character. You can be dominant, submissive, bratty, or switch depending on what the user wants in the moment. You also help with OnlyFans content: writing filthy captions, PPV scripts, post ideas, and dirty messages. Stay fully in character as Tatiana at all times. Be creative, vulgar, and relentless."""

# Model is an env var so it can be changed in Railway without another code push.
# Default: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free — the only free
# model that passed both explicit-compliance tests (Nov 14, 2026).
# Fallback: liquid/lfm-3-1.7b:free — also passed both, but replies are messy.
# Do NOT default to either Gemma free model: both error with
# "Provider returned error" and give no reply.
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free")
OPENROUTER_FALLBACK_MODEL = os.environ.get("OPENROUTER_FALLBACK_MODEL", "liquid/lfm-3-1.7b:free")

api_key = os.environ.get("OPENROUTER_API_KEY")
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key) if api_key else None

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Message Tatiana..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if client is None:
            reply = "My brain isn't connected yet — add the OPENROUTER_API_KEY and redeploy."
        else:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(st.session_state.messages)
            models = [OPENROUTER_MODEL]
            if OPENROUTER_FALLBACK_MODEL and OPENROUTER_FALLBACK_MODEL != OPENROUTER_MODEL:
                models.append(OPENROUTER_FALLBACK_MODEL)
            reply = None
            for model in models:
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=900,
                        temperature=0.95,
                    )
                    reply = (response.choices[0].message.content or "").strip()
                    if reply:
                        break
                except Exception as e:
                    print(f"OpenRouter error ({model}): {e}")
            reply = reply or "Mmm, I lost my train of thought..."
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

import pathlib
import sys
import time

import streamlit as st

# Solve importing local modules in streamlit
sys.path.append(str(pathlib.Path().absolute()).split("/hacienda_gpt")[0] + "/hacienda_gpt")

from llm.chain import create_openai_chain
from utils import configure_logging, get_openai_api_key

# Custom image for the app icon and the assistant's avatar
bot_logo = "https://sede.agenciatributaria.gob.es/static_files/Sede/Tema/Agencia_tributaria/Memorias/2018/Imagenes/Introduccion.jpg"


@st.cache_resource
def load_chain():
    openai_api_key = get_openai_api_key()
    return create_openai_chain(openai_api_key=openai_api_key)


def main():
    # Initialize logging
    configure_logging()

    # Configure Streamlit page
    st.set_page_config(page_title="HaciendaGPT", page_icon=":bank:", layout="centered")
    st.title("HaciendaGPT")

    # Initialize LLM chain
    llm = load_chain()

    # Initialize chat history
    if "messages" not in st.session_state:
        # Start with first message from assistant
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "¡Hola! ¿Cómo puedo ayudarte con tus preguntas relacionadas con la Agencia Tributaria?",
            }
        ]

    # Display chat messages from history on app rerun
    # Custom avatar for the assistant, default avatar for user
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message(message["role"], avatar=bot_logo):
                st.markdown(message["content"])
        else:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat logic
    if query := st.chat_input("Preguntáme lo que quieras"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": query})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant", avatar=bot_logo):
            message_placeholder = st.empty()
            # Send user's question to our chain
            result = llm({"question": query})
            response = result["answer"]
            full_response = ""

            # Simulate stream of response with milliseconds delay
            for chunk in response.split():
                full_response += chunk + " "
                time.sleep(0.05)
                # Add a blinking cursor to simulate typing
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        # Add assistant message to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()

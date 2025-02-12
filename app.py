import streamlit as st
import requests

# Configuración de la API FastAPI
API_URL = "http://0.0.0.0:5000"  # Cambia esto si tu API está en otro lugar

def submit_pdf(file):
    """
    Envía un archivo PDF a la API FastAPI para su procesamiento.

    Args:
        file: El archivo PDF subido por el usuario.

    Returns:
        dict: La respuesta JSON de la API.
    """
    url = f"{API_URL}/upload/"
    files = {"file": (file.name, file.getvalue(), "application/pdf")}
    response = requests.post(url, files=files)
    return response.json()

def delete_pdf(filename: str):
    """
    Envía una solicitud a la API FastAPI para eliminar un archivo PDF.

    Args:
        filename (str): El nombre del archivo PDF a eliminar.

    Returns:
        dict: La respuesta JSON de la API.
    """
    url = f"{API_URL}/delete-pdf/"
    payload = {"filename": filename}
    response = requests.post(url, json=payload)
    return response.json()

def get_response(user_question, reset=False):
    """
    Obtiene una respuesta del chatbot a través de la API FastAPI.

    Args:
        user_question (str): La pregunta del usuario.

    Returns:
        str: La respuesta del chatbot.
    """
    api_url = f"{API_URL}/chat/"
    payload = {"msg": user_question, "reset":reset}

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()  # Lanza un error para respuestas no exitosas
        return response.json().get('response', 'Lo siento, no pude encontrar una respuesta.')
    except requests.exceptions.RequestException as e:
        return f'Error al comunicarse con la API: {str(e)}'

def reset(word="reset", reset=True):
    api_url = f"{API_URL}/chat/"
    payload = {"msg": word, "reset":reset}

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()  # Lanza un error para respuestas no exitosas
        return response.json().get('response', 'Lo siento, no pude encontrar una respuesta.')
    except requests.exceptions.RequestException as e:
        return f'Error al comunicarse con la API: {str(e)}'

def reset_chat():
    """
    Resetea el historial de chat y el buffer de la conversación.
    """
    # Limpiar el historial de chat en la sesión de Streamlit
    st.session_state.chat_history = []

    # Llamar al endpoint para resetear el buffer de la conversación
    reset()

def main():
    """
    Función principal para configurar y ejecutar la aplicación Streamlit.
    """
    st.set_page_config(page_title="RAG edge Ai chat", page_icon=":books:")

    # Inicializa el estado de la sesión si no existe
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "uploaded_pdfs" not in st.session_state:
        st.session_state.uploaded_pdfs = []

    st.header("AI chat")

    # Mostrar el historial de chat
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("Human"):
                st.write(message["content"])
        else:
            with st.chat_message("AI"):
                st.write(message["content"])

    # Entrada del usuario
    user_question = st.chat_input("Ask a question about your documents:")
    if user_question:
        # Obtener la respuesta del chatbot
        bot_response = get_response(user_question)

        # Guardar la pregunta y respuesta en el historial de chat
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        st.session_state.chat_history.append({"role": "bot", "content": bot_response})

        # Mostrar la pregunta y respuesta inmediatamente
        with st.chat_message("Human"):
            st.write(user_question)
        with st.chat_message("AI"):
            st.write(bot_response)

    # Barra lateral para cargar PDFs y resetear el chat
    with st.sidebar:
        st.subheader("Your documents")
        
        # Cargar PDFs
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'", accept_multiple_files=False)
        if st.button("Process"):
            with st.spinner("Processing"):
                response = submit_pdf(file=pdf_docs)
                if response:
                    st.success("Archivo subido exitosamente!")
                    st.json(response)
                    # Agregar el nombre del archivo a la lista de PDFs cargados
                    st.session_state.uploaded_pdfs.append(pdf_docs.name)
                else:
                    st.error("Error al subir el archivo.")

        # Mostrar la lista de PDFs cargados con botones de eliminación
        st.markdown("---")
        st.subheader("PDFs cargados")
        for pdf_name in st.session_state.uploaded_pdfs:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(pdf_name)
            with col2:
                if st.button("🗑️", key=f"delete_{pdf_name}"):
                    with st.spinner("Eliminando..."):
                        response = delete_pdf(pdf_name)
                        if response.get("message"):
                            st.success(response["message"])
                            # Eliminar el archivo de la lista de PDFs cargados
                            st.session_state.uploaded_pdfs.remove(pdf_name)
                            st.rerun()  # Recargar la interfaz para reflejar los cambios
                        else:
                            st.error("Error al eliminar el archivo.")

        # Botón para resetear el chat en la parte inferior del sidebar
        st.markdown("---")
        if st.button("Reset Chat", key="reset_chat_button"):
            reset_chat()
            st.success("El chat ha sido reseteado.")
            st.rerun()

if __name__ == '__main__':
    main()
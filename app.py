import streamlit as st
import requests
from datetime import datetime

# Configuración de la API 
API_URL = "http://127.0.0.1:8000"  # Cambia esto si tu API está en otro lugar

# Función para manejar el login
def login(username: str, password: str):
    url = f"{API_URL}/token"
    data = {
        "username": username,
        "password": password,
        "grant_type": "password"
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error en el login: Usuario o contraseña incorrectos.")
        return None

# Función para manejar el registro
def register(username: str, email: str, password: str):
    url = f"{API_URL}/register/"
    data = {
        "username": username,
        "email": email,
        "password": password
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error en el registro: Usuario ya existe o datos inválidos.")
        return None

# Función para manejar el logout
def logout():
    """
    Limpia el estado de la sesión al hacer logout.
    """
    # Limpiar el estado de la sesión
    st.session_state.token = None
    st.session_state.username = None
    st.session_state.chat_history = []
    st.session_state.uploaded_pdfs = []
    st.session_state.current_chat_id = None

    # Limpiar la memoria de la conversación (si está en uso)
    if "conversation_memory" in st.session_state:
        st.session_state.conversation_memory.clear()

    st.success("Sesión cerrada correctamente.")
    st.rerun()  # Recargar la aplicación para reflejar los cambios

# Función para enviar un archivo PDF a la API
def submit_pdf(file, token: str):
    url = f"{API_URL}/upload/"
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": (file.name, file.getvalue(), "application/pdf")}
    response = requests.post(url, files=files, headers=headers)
    return response.json()

# Función para eliminar un PDF
def delete_pdf(filename: str, token: str):
    url = f"{API_URL}/delete-pdf/"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"filename": filename}
    response = requests.delete(url, json=payload, headers=headers)
    return response.json()

# Función para obtener la respuesta del chatbot
def get_response(user_question: str, token: str, chat_id: str):
    url = f"{API_URL}/chat/"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"msg": user_question, "chat_id": chat_id}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error al obtener la respuesta del chatbot.")
        return None

# Función para obtener la lista de PDFs procesados
def get_processed_pdfs(token: str):
    url = f"{API_URL}/get-pdfs/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("pdfs", [])
    else:
        st.error("Error al obtener la lista de PDFs procesados.")
        return []

# Función para obtener la lista de chats
def get_chat_list(token: str):
    url = f"{API_URL}/chat-list/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("chats", [])
    else:
        st.error("Error al obtener la lista de chats.")
        return []

# Función para cargar un chat específico
def load_chat(chat_id: str, token: str):
    url = f"{API_URL}/chat-history/{chat_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("history", [])
    else:
        st.error("Error al cargar el historial del chat.")
        return []

# Función para crear un nuevo chat
def new_chat(token: str):
    url = f"{API_URL}/new-chat/"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error al crear un nuevo chat.")
        return None

# Función principal
def main():
    st.set_page_config(page_title="RAG edge AI chat", page_icon=":books:")

    # Inicializa el estado de la sesión si no existe
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "uploaded_pdfs" not in st.session_state:
        st.session_state.uploaded_pdfs = []
    if "token" not in st.session_state:
        st.session_state.token = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "conversation_memory" not in st.session_state:
        st.session_state.conversation_memory = {}  # Memoria de la conversación

    # Página de autenticación
    if st.session_state.token is None:
        st.title("Autenticación")
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])

        with tab1:
            with st.form("login_form"):
                st.write("Iniciar Sesión")
                username = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Login"):
                    response = login(username, password)
                    if response:
                        st.session_state.token = response.get("access_token")
                        st.session_state.username = username
                        # Obtener la lista de PDFs al iniciar sesión
                        st.session_state.uploaded_pdfs = get_processed_pdfs(st.session_state.token)
                        st.success("Login exitoso!")
                        st.rerun()

        with tab2:
            with st.form("register_form"):
                st.write("Registrarse")
                new_username = st.text_input("Nuevo Usuario")
                new_email = st.text_input("Email")
                new_password = st.text_input("Nueva Contraseña", type="password")
                if st.form_submit_button("Registrar"):
                    response = register(new_username, new_email, new_password)
                    if response:
                        st.success("Registro exitoso! Por favor, inicia sesión.")
        return

    # Si el usuario está autenticado, mostrar el contenido principal
    st.title("AI Chat")
    st.write(f"Bienvenido, {st.session_state.username}!")

    # Barra lateral para gestionar PDFs, chats y logout
    with st.sidebar:
        st.subheader("Gestión de PDFs")
        
        # Cargar PDFs
        pdf_docs = st.file_uploader(
            "Sube tus PDFs aquí y haz clic en 'Procesar'", accept_multiple_files=False)
        if st.button("Procesar"):
            with st.spinner("Procesando..."):
                if pdf_docs is not None:
                    response = submit_pdf(pdf_docs, st.session_state.token)
                    if response:
                        st.success("Archivo subido exitosamente!")
                        st.json(response)
                        # Actualizar la lista de PDFs cargados
                        st.session_state.uploaded_pdfs = get_processed_pdfs(st.session_state.token)
                    else:
                        st.error("Error al subir el archivo.")
                else:
                    st.error("Por favor, sube un archivo PDF.")

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
                        # Eliminar el PDF del servidor y del vectorstore
                        response = delete_pdf(pdf_name, st.session_state.token)
                        if response.get("message"):
                            st.success(response["message"])
                            # Actualizar la lista de PDFs
                            st.session_state.uploaded_pdfs = get_processed_pdfs(st.session_state.token)
                            st.rerun()  # Recargar la interfaz para reflejar los cambios
                        else:
                            st.error("Error al eliminar el archivo.")

        # Botón para crear un nuevo chat
        st.markdown("---")
        if st.button("Nuevo Chat"):
            response = new_chat(st.session_state.token)
            if response:
                st.success("Nuevo chat creado correctamente.")
                st.session_state.current_chat_id = response.get("chat_id")
                st.session_state.chat_history = []
                st.rerun()

        # Mostrar la lista de chats (solo nombre, limitado a 20 caracteres)
        st.subheader("Chats Recientes")
        chat_list = get_chat_list(st.session_state.token)
        for chat in chat_list:
            # Limitar el título a 20 caracteres
            chat_title = chat["title"][:20] + "..." if len(chat["title"]) > 20 else chat["title"]
            if st.button(chat_title, key=f"chat_{chat['chat_id']}"):
                st.session_state.current_chat_id = chat["chat_id"]
                st.session_state.chat_history = load_chat(chat["chat_id"], st.session_state.token)
                st.rerun()

        # Botón de Cerrar Sesión en el sidebar
        st.markdown("---")
        if st.button("Cerrar Sesión"):
            logout()

    # Mostrar el historial de chat con estilo mejorado
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("Human", avatar="🧑‍💻"):
                st.markdown(f"**Tú:** {message['text']}")
        else:
            with st.chat_message("AI", avatar="🤖"):
                st.markdown(f"**Asistente:** {message['text']}")

    # Entrada del usuario
    user_question = st.chat_input("Haz una pregunta sobre tus documentos:")
    if user_question:
        # Obtener la respuesta del chatbot
        response = get_response(user_question, st.session_state.token, st.session_state.current_chat_id)
        if response:
            bot_response = response.get("response")
            chat_id = response.get("chat_id")

            # Guardar la pregunta y respuesta en el historial de chat
            st.session_state.chat_history.append({"role": "user", "text": user_question})
            st.session_state.chat_history.append({"role": "assistant", "text": bot_response})

            # Mostrar la pregunta y respuesta inmediatamente
            with st.chat_message("Human", avatar="🧑‍💻"):
                st.markdown(f"**Tú:** {user_question}")
            with st.chat_message("AI", avatar="🤖"):
                st.markdown(f"**Asistente:** {bot_response}")

if __name__ == '__main__':
    main()
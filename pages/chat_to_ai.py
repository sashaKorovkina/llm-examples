import streamlit as st

if 'chat_file_name' in st.session_state:
    chat_file_name = st.session_state['chat_file_name']
    pdf_images = st.session_state['pdf_images']
    pdf_texts = st.session_state['pdf_texts']
    file_name = st.session_state['file_name']
    st.title(f"Chat about {chat_file_name}")
    st.write("Starting chat session for:", chat_file_name)
    st.write(pdf_texts)
    # Optionally, clear the session state if no longer needed after initiating the chat
    # del st.session_state['chat_file_name']
else:
    st.error("No file specified for the chat session.")

import streamlit as st
from firebase_admin import firestore, storage

db = firestore.client()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

st.title("Chat To AI")

if 'logged_in' in st.session_state and st.session_state.logged_in:
    if 'username' in st.session_state:
        username = st.session_state['username']
        st.write(f"Logged in as: {username}")

        chats_ref = db.collection('users').document(username).collection('chats')
        chats = chats_ref.get()
        chats_all = [chat.to_dict() for chat in chats]
        chat_names = [chat['filename'] for chat in chats_all if 'filename' in chat]
        selected_chat_name = st.sidebar.radio("Select a Chat:", chat_names)
        selected_chat_data = next((chat for chat in chats_all if chat['filename'] == selected_chat_name), None)

        if selected_chat_data:
            st.write(f"Starting chat session FOR: {selected_chat_data['filename']}")
            st.write(f"The text in the selected file is: {selected_chat_data['pdf_text']}")
            if 'messages' in selected_chat_data:
                st.write("Messages:")
                for message in selected_chat_data['messages']:
                    st.write(message)
else:
    st.write('Please register or login to continue.')


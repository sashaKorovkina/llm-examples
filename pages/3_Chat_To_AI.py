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

        for chat in chats_all:
            if chat['filename'] == selected_chat_name:
                st.write(f"Starting chat session FOR: {chat['filename']}")

else:
    st.write('Please register or login to continue.')


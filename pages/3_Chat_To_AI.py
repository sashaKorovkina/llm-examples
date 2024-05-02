import streamlit as st
from firebase_admin import firestore, storage

db = firestore.client()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

st.title("Chat To AI")

# MAIN SCRIPT
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

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if selected_chat_data:
            st.write(f"Starting chat session FOR: {selected_chat_data['filename']}")
            st.write(f"The text in the selected file is: {selected_chat_data['pdf_text']}")
            # Display chat messages from history on app rerun
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            if prompt := st.chat_input("What is up?"):
                # Display user message in chat message container
                with st.chat_message("user"):
                    st.markdown(prompt)
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                response = f"Echo: {prompt}"
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    st.markdown(response)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.write('Please register or login to continue.')


import streamlit as st
from firebase_admin import firestore, storage
import streamlit as st
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.callbacks import get_openai_callback

db = firestore.client()

# FUNCTIONS
def response_func(prompt, text):
    text = str(text)
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    embeddings = OpenAIEmbeddings()
    knowledge_base = FAISS.from_texts(chunks, embeddings)
    docs = knowledge_base.similarity_search(prompt)
    llm = OpenAI()
    chain = load_qa_chain(llm, chain_type="stuff")
    with get_openai_callback() as cb:
        result = chain.run(input_documents=docs, question=prompt)

    st.write(result)
    return result

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

st.title("Chat To AI")

# MAIN SCRIPT
if 'logged_in' in st.session_state and st.session_state.logged_in:
    api_key = st.text_input("OpenAI API Key", key="file_docs_api_key", type="password")
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
            # for message in st.session_state.messages:
            #     with st.chat_message(message["role"]):
            #         st.markdown(message["content"])
            if prompt := st.chat_input("What is up?"):
                with st.chat_message("user"):
                    st.markdown(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})
                response = response_func(prompt, selected_chat_data['pdf_text'])
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.write('Please register or login to continue.')


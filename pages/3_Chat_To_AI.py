import streamlit as st
from langchain.vectorstores import ElasticVectorSearch, Pinecone, Weaviate, FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI

# with st.sidebar:
#     api_key = st.text_input("OpenAI API Key", key="file_qa_api_key", type="password")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

st.title("Chat To AI")

if st.session_state.logged_in:
    api_key = st.text_input("OpenAI API Key", key="file_qa_api_key", type="password")
    if api_key:
        if 'chats' not in st.session_state:
            st.session_state.chats = []

        if st.button('Add Chat'):
            new_chat_name = f"Chat {len(st.session_state.chats) + 1}"
            st.session_state.chats.append({
                'name': new_chat_name,
                'pdf_images': [],
                'pdf_texts': [],
                'file_name': '',
            })

        for chat in st.session_state.chats:
            st.write(f"Starting chat session FOR: {chat['name']}")
            if chat['pdf_texts']:
                accumulated_text = '\n'.join(chat['pdf_texts'])
                st.write(accumulated_text)
            else:
                st.write("No text was extracted from the PDF, or the list is empty.")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=512,
                chunk_overlap=32,
                length_function=len,
            )

            texts = text_splitter.split_text(accumulated_text)

            embeddings = OpenAIEmbeddings(openai_api_key=api_key)
            docsearch = FAISS.from_texts(texts, embeddings)
            chain = load_qa_chain(OpenAI(openai_api_key=api_key), chain_type="stuff")

            query = st.text_input(f"Enter your query for {chat['name']}:")

            if query:
                docs = docsearch.similarity_search(query)
                result = chain.run(input_documents=docs, question=query)

                # Display the result for each chat
                st.write(f"Result for {chat['name']}:")
                st.write(result)
else:
    st.write('Please register or login to continue.')

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
        if 'chat_file_name' in st.session_state:
            chat_file_name = st.session_state['chat_file_name']
            pdf_images = st.session_state['pdf_images']
            pdf_texts = st.session_state['pdf_texts']
            file_name = st.session_state['file_name']
            st.write("Starting chat session FOR:", chat_file_name)
            if pdf_texts:
                accumulated_text = '\n'.join(pdf_texts)
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

            query = st.text_input("Enter your query:")

            if query:
                docs = docsearch.similarity_search(query)
                result = chain.run(input_documents=docs, question=query)

                # Display the result
                st.write("Result:")
                st.write(result)
else:
    st.write('Please register or login to continue.')

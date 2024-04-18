import streamlit as st
import base64
import streamlit as st
import requests
from PIL import Image
import fitz
import io
import pytesseract
import shutil
from langchain.vectorstores import ElasticVectorSearch, Pinecone, Weaviate, FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
import os
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI

pytesseract.pytesseract.tesseract_cmd = None
# search for tesseract binary in path
@st.cache_resource
def find_tesseract_binary() -> str:
    return shutil.which("tesseract")

# set tesseract binary path
pytesseract.pytesseract.tesseract_cmd = find_tesseract_binary()
if not pytesseract.pytesseract.tesseract_cmd:
    st.error("Tesseract binary not found in PATH. Please install Tesseract.")

with st.sidebar:
    api_key = st.text_input("OpenAI API Key", key="file_qa_api_key", type="password")

models = {
    "GPT-4": "gpt-4",
    "GPT-4 Turbo": "gpt-4-turbo",
    "GPT-3.5 Turbo": "gpt-3.5-turbo",
    "Code Davinci 002": "code-davinci-002",
    "Text Davinci 003": "text-davinci-003",
    "Text Davinci 004": "text-davinci-004",
}

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def save_uploaded_file(uploaded_file, target_path):
    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
def send_image_to_openai(base64_image):
    headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {api_key}"
    }

    payload = {
              "model": "gpt-4-vision-preview",
              "messages": [
                {
                  "role": "user",
                  "content": [
                    {
                      "type": "text",
                      "text": "What’s in this image? Explain the image content"
                    },
                    {
                      "type": "image_url",
                      "image_url": {
                      "url": f"data:image/jpeg;base64,{base64_image}"
                      }
                    }
                  ]
                }
              ],
              "max_tokens": 100
            }
    if st.button("Get Explanation"):
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            print(response.json())
            st.success("Explanation: {}".format(response.json()['choices'][0]['message']['content']))
        except Exception as e:
            st.error(f"Error: {e}")

def send_text_to_openai(text_content, model_engine, unique_key):
    headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {api_key}"
    }

    payload = {
              "model": f"{model_engine}",
              "messages": [
                {
                    "role": "user",
                    "content": f"Summarise this text for me: ... {text_content}"
                }
              ],
              "max_tokens": 100
            }

    if st.button("Get Explanation", key=unique_key):
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            explanation = response.json()['choices'][0]['message']['content']
            st.success(f"Explanation: {explanation}")
        except Exception as e:
            st.error(f"Error: {e}")



st.title("Image Explanation Chatbot!")

uploaded_file = st.file_uploader("Choose an image or PDF...", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file is None:
    st.write("What are you doing? No file was chosen")

selected_model_name = st.selectbox("Select a model:", options=list(models.keys()))
model_engine = models[selected_model_name]

st.write(f"Drivers, start your engine : {model_engine}")
user_question = st.text_input("Ask your question")

file_extension = uploaded_file.name.split(".")[-1].lower()

if file_extension in ["jpg", "jpeg", "png"]:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded image", use_column_width=True)
    save_uploaded_file(uploaded_file, 'temp.jpg')
    base64_image = encode_image('temp.jpg')
    send_image_to_openai(base64_image)

if file_extension == "pdf":
    pdf_bytes = uploaded_file.getvalue()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pdf_images = []
    pdf_texts = []  # List to store text from all pages

    for page_index in range(len(doc)):
        page = doc[page_index]
        pix = page.get_pixmap()
        image_data = pix.tobytes()
        pdf_image = Image.open(io.BytesIO(image_data))
        pdf_images.append(pdf_image)

    for page_index, pdf_image in enumerate(pdf_images):
        st.image(pdf_image, caption=f"Uploaded PDF to image Page {page_index + 1}", use_column_width=True)

        text = pytesseract.image_to_string(pdf_image)
        pdf_texts.append(text)  # Accumulate text from each page

        st.write(f"Text from Page {page_index + 1}:")
        st.write(text)

        texts_to_process = [text]
        for text_index, text_content in enumerate(texts_to_process):
            send_text_to_openai(text_content, model_engine, f"button_key_{page_index}_{text_index}")

    # Processing the text from the whole PDF
    st.write("Accumulated Text from all Pages:")
    accumulated_text = '\n'.join(pdf_texts)
    st.write(accumulated_text)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=32,
        length_function=len,
    )
    texts = text_splitter.split_text(accumulated_text)

    embeddings = OpenAIEmbeddings()
    docsearch = FAISS.from_texts(texts, embeddings)
    chain = load_qa_chain(OpenAI(), chain_type="stuff")

    # Create a text input box for the user to enter their query
    query = st.text_input("Enter your query:")

    # Check if the query is not empty
    if query:
        # Assuming docsearch and chain are defined elsewhere in your code
        docs = docsearch.similarity_search(query)
        chain.run(input_documents=docs, question=query)





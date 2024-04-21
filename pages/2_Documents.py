import base64
import streamlit as st
import requests
from PIL import Image
import fitz
import io
import pytesseract
import shutil
from streamlit.components.v1 import html
from firebase_admin import firestore

# CHANGE FOR CLOUD DEPLOY!!!!!!!
pytesseract.pytesseract.tesseract_cmd = None
# pytesseract.pytesseract.tesseract_cmd = r'C:\Users\sasha\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# search for tesseract binary in path
@st.cache_resource
def find_tesseract_binary() -> str:
    return shutil.which("tesseract")

# set tesseract binary path
pytesseract.pytesseract.tesseract_cmd = find_tesseract_binary()
if not pytesseract.pytesseract.tesseract_cmd:
    st.error("Tesseract binary not found in PATH. Please install Tesseract.")

# with st.sidebar:
#     api_key = st.text_input("OpenAI API Key", key="file_qa_api_key", type="password")

# models = {
#     "GPT-4": "gpt-4",
#     "GPT-4 Turbo": "gpt-4-turbo",
#     "GPT-3.5 Turbo": "gpt-3.5-turbo",
#     "Code Davinci 002": "code-davinci-002",
#     "Text Davinci 003": "text-davinci-003",
#     "Text Davinci 004": "text-davinci-004",
# }

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

def chat_to_ai(file_name):
    # Functionality to chat about the specific PDF
    st.write(f"Chatting about {file_name}...")

def get_summary(file_name):
    # Functionality to summarize the specific PDF
    st.write(f"Getting summary for {file_name}...")

def nav_page(page_name, timeout_secs=3):
    nav_script = """
        <script type="text/javascript">
            function attempt_nav_page(page_name, start_time, timeout_secs) {
                var links = window.parent.document.getElementsByTagName("a");
                for (var i = 0; i < links.length; i++) {
                    if (links[i].href.toLowerCase().endsWith("/" + page_name.toLowerCase())) {
                        links[i].click();
                        return;
                    }
                }
                var elasped = new Date() - start_time;
                if (elasped < timeout_secs * 1000) {
                    setTimeout(attempt_nav_page, 100, page_name, start_time, timeout_secs);
                } else {
                    alert("Unable to navigate to page '" + page_name + "' after " + timeout_secs + " second(s).");
                }
            }
            window.addEventListener("load", function() {
                attempt_nav_page("%s", new Date(), %d);
            });
        </script>
    """ % (page_name, timeout_secs)
    html(nav_script)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

st.title("Documents")
# Page access control
if st.session_state.logged_in:
    # database test
    # db = firestore.client()
    # st.session_state.db = db
    # docs = db.collection('users').get()
    # for doc in docs:
    #     d = doc.to_dict()
    #     if d['Username'] == st.session_state.username:
    #         st.text(doc.to_dict())  # Print each document's data

    # api_key = st.text_input("OpenAI API Key", key="file_qa_api_key", type="password")
    uploaded_files = st.file_uploader("Choose images or PDFs...", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    if uploaded_files:
        # selected_model_name = st.selectbox("Select a model:", options=list(models.keys()))
        # model_engine = models[selected_model_name]

        # CONTAINERIZED OUTPUT DISPLAY
        num_files = len(uploaded_files)
        num_rows = (num_files + 2) // 3

        rows = [st.container() for _ in range(num_rows)]

        file_index = 0
        for row in rows:
            with row:
                cols = st.columns(3)
                for col in cols:
                    if file_index < num_files:
                        uploaded_file = uploaded_files[file_index]
                        file_extension = uploaded_file.name.split(".")[-1].lower()
                        with col:
                            if file_extension in ["jpg", "jpeg", "png"]:
                                bytes_data = io.BytesIO(uploaded_file.getvalue())
                                image = Image.open(bytes_data)
                                if st.checkbox(f"Select PDF: {uploaded_file.name}"):
                                    st.session_state['selected_file'] = uploaded_file.name
                                    st.image(image, caption=f"Selected Image: {uploaded_file.name}", use_column_width=True)
                                    st.write(f"You have selected: {uploaded_file.name}")
                                else:
                                    st.image(image, caption=f"Image: {uploaded_file.name}", use_column_width=True)
                            elif file_extension == "pdf":
                                doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                                page = doc.load_page(0)
                                pix = page.get_pixmap()
                                img = Image.open(io.BytesIO(pix.tobytes("png")))
                                # Using a checkbox to select the image
                                if st.checkbox(f"Select PDF: {uploaded_file.name}"):
                                    st.session_state['selected_file'] = uploaded_file.name
                                    st.image(img, caption=f"Selected PDF: {uploaded_file.name}", use_column_width=True)
                                    st.write(f"You have selected: {uploaded_file.name}")
                                    if st.button("Chat to AI", key=f"chat_{uploaded_file.name}"):
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

                                            text = pytesseract.image_to_string(pdf_image)
                                            pdf_texts.append(text)  # Accumulate text from each page

                                        st.session_state['pdf_images'] = pdf_images
                                        st.session_state['pdf_texts'] = pdf_texts
                                        st.session_state['file_name'] = uploaded_file.name
                                        st.session_state['chat_file_name'] = uploaded_file.name

                                        nav_page("chat_to_ai")
                                    if st.button("Get Summary", key=f"summary_{uploaded_file.name}"):
                                        # Handle summary action here
                                        st.write(f"Getting summary for {uploaded_file.name}...")
                                else:
                                    st.image(img, caption=f"PDF: {uploaded_file.name}", use_column_width=True)
                                doc.close()
                            else:
                                st.write(f"Unsupported file format for {uploaded_file.name}")
                        file_index += 1
else:
    st.write('Please register or log in to continue.')
# file_extension = uploaded_file.name.split(".")[-1].lower()
#
# if file_extension in ["jpg", "jpeg", "png"]:
#     image = Image.open(uploaded_file)
#     st.image(image, caption="Uploaded image", use_column_width=True)
#     save_uploaded_file(uploaded_file, 'temp.jpg')
#     base64_image = encode_image('temp.jpg')
#     send_image_to_openai(base64_image)


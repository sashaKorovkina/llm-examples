import base64
import streamlit as st
import requests
from PIL import Image
import io
import pytesseract
import shutil
from streamlit.components.v1 import html
from firebase_admin import firestore, storage
import uuid
import datetime
import fitz

# CHANGE FOR CLOUD DEPLOY!!!!
pytesseract.pytesseract.tesseract_cmd = None
# pytesseract.pytesseract.tesseract_cmd = r'C:\Users\sasha\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# search for tesseract binary in path
@st.cache_resource
def find_tesseract_binary() -> str:
    return shutil.which("tesseract")

# INITIALISE VARIABLES #################################################################################################

# pytesseract
pytesseract.pytesseract.tesseract_cmd = find_tesseract_binary()
if not pytesseract.pytesseract.tesseract_cmd:
    st.error("Tesseract binary not found in PATH. Please install Tesseract.")

# firestore database
db = firestore.client()
bucket = storage.bucket('elmeto-12de0.appspot.com')

# logged in parameter
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# with st.sidebar:
#     api_key = st.text_input("OpenAI API Key", key="file_qa_api_key", type="password")

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


def get_existing_files():
    docs_ref = db.collection('users').document(username).collection('documents')
    docs = docs_ref.get()
    files = [doc.to_dict() for doc in docs]
    return files


def get_last_file():
    docs_ref = db.collection('users').document(username).collection('documents')
    docs = docs_ref.get()
    files = [doc.to_dict() for doc in docs]
    file = files[len(files)-1]
    return file


def check_file(file):
    st.write(f'The existing files are {file}')
    response = requests.get(file['url'])
    if response.status_code == 200:
        st.write(f"Succes: {file['url']}")
    else:
        st.write(f"Failed: {response.status_code}")


st.title("Documents")
# Page access control
if st.session_state.logged_in:
    username = st.session_state.username

    files = get_existing_files()
    for file in files:
        check_file(file)

    uploaded_file = st.file_uploader("Choose images or PDFs...", type=["jpg", "jpeg", "png", "pdf"],
                                      accept_multiple_files=False)

    if uploaded_file:
        blob = bucket.blob(f"{st.session_state.username}/{uuid.uuid4()}_{uploaded_file.name}")
        blob.upload_from_string(uploaded_file.getvalue(), content_type=uploaded_file.type)

        # Get the URL of the uploaded file
        url = blob.generate_signed_url(version="v4", expiration=datetime.timedelta(minutes=10000), method='GET')

        # Store the document metadata in Firestore under the user's 'documents' subcollection
        doc_ref = db.collection('users').document(st.session_state.username).collection('documents').document()
        doc_ref.set({
            'filename': uploaded_file.name,
            'content_type': uploaded_file.type,
            'url': url,  # This is a temporary URL for access, you may want to handle this differently
            'uploaded_at': firestore.SERVER_TIMESTAMP
        })
        st.write(f'Current document is: {doc_ref}')
        file = get_last_file()
        check_file(file)


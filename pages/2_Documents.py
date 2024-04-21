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

# CHANGE FOR CLOUD DEPLOY!!!!!!!
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

st.title("Documents")
# Page access control
if st.session_state.logged_in:
    username = st.session_state.username

    # step 1: see if user has prior documents
    # step 2: ask user to upload a file

    uploaded_files = st.file_uploader("Choose images or PDFs...", type=["jpg", "jpeg", "png", "pdf"],
                                      accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Generate a unique ID for the file within Firebase storage
            blob = bucket.blob(f"{st.session_state.username}/{uuid.uuid4()}_{uploaded_file.name}")
            blob.upload_from_string(uploaded_file.getvalue(), content_type=uploaded_file.type)

            # Get the URL of the uploaded file
            url = blob.generate_signed_url(version="v4", expiration=datetime.timedelta(minutes=10), method='GET')

            # Store the document metadata in Firestore under the user's 'documents' subcollection
            doc_ref = db.collection('users').document(st.session_state.username).collection('documents').document()
            doc_ref.set({
                'filename': uploaded_file.name,
                'content_type': uploaded_file.type,
                'url': url,  # This is a temporary URL for access, you may want to handle this differently
                'uploaded_at': firestore.SERVER_TIMESTAMP
            })

    docs_ref = db.collection('users').document(username).collection('documents')
    docs = docs_ref.get()

    files = [doc.to_dict() for doc in docs]

    if files:
        st.write(f"Files uploaded by {username}:")
        num_files = len(files)
        num_rows = (num_files + 2) // 3
        rows = [st.container() for _ in range(num_rows)]

        file_index = 0
        for row in rows:
            with row:
                cols = st.columns(3)
                for col in cols:
                    if file_index < num_files:
                        file_metadata = files[file_index]
                        file_extension = file_metadata['filename'].split('.')[-1].lower()
                        with col:
                            try:
                                response = requests.get(file_metadata['url'])
                                if response.status_code == 200:
                                    bytes_data = io.BytesIO(response.content)
                                    if file_extension == 'pdf':
                                        doc = fitz.open("pdf", bytes_data.getvalue())  # Open PDF with PyMuPDF
                                        page = doc.load_page(0)  # Assume you want the first page
                                        pix = page.get_pixmap()
                                        img = Image.open(io.BytesIO(pix.tobytes()))
                                        st.image(img, caption=f"{file_metadata['filename']}", use_column_width=True)
                                        checkbox_key = f"select_{file_metadata['filename']}_{file_index}"  # Unique key
                                        if st.checkbox(f"Select PDF: {file_metadata['filename']}", key=checkbox_key):
                                            st.session_state['selected_file'] = file_metadata['filename']
                                            st.write(f"You have selected: {file_metadata['filename']}")
                                            if st.button("Chat to AI", key=f"chat_{file_metadata['filename']}"):
                                                pdf_bytes = file_metadata.getvalue()
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
                                                st.session_state['file_name'] = file_metadata.name
                                                st.session_state['chat_file_name'] = file_metadata.name

                                                nav_page("chat_to_ai")

                                        #doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                                        #                                 # Using a checkbox to select the image
                                        #                                 if st.checkbox(f"Select PDF: {uploaded_file.name}"):
                                        #                                     st.image(img, caption=f"Selected PDF: {uploaded_file.name}", use_column_width=True)
                                        #                                     st.write(f"You have selected: {uploaded_file.name}")
                                        #                                     if st.button("Chat to AI", key=f"chat_{uploaded_file.name}"):
                                        #                                         pdf_bytes = uploaded_file.getvalue()
                                        #                                         doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                                        #                                         pdf_images = []
                                        #                                         pdf_texts = []  # List to store text from all pages
                                        #
                                        #                                         for page_index in range(len(doc)):
                                        #                                             page = doc[page_index]
                                        #                                             pix = page.get_pixmap()
                                        #                                             image_data = pix.tobytes()
                                        #                                             pdf_image = Image.open(io.BytesIO(image_data))
                                        #                                             pdf_images.append(pdf_image)
                                        #
                                        #                                             text = pytesseract.image_to_string(pdf_image)
                                        #                                             pdf_texts.append(text)  # Accumulate text from each page
                                        #
                                        #                                         st.session_state['pdf_images'] = pdf_images
                                        #                                         st.session_state['pdf_texts'] = pdf_texts
                                        #                                         st.session_state['file_name'] = uploaded_file.name
                                        #                                         st.session_state['chat_file_name'] = uploaded_file.name
                                        #
                                        #                                         nav_page("chat_to_ai")
                                        doc.close()
                                else:
                                    st.error(
                                        f"Failed to load file {file_metadata['filename']} with status code {response.status_code}")
                            except Exception as e:
                                st.error(f"Failed to open file {file_metadata['filename']}. Error: {str(e)}")
                        file_index += 1
    else:
        st.write("No files found for this user.")
else:
    st.write('Please register or log in to continue.')


#
#     if uploaded_files:
#         # selected_model_name = st.selectbox("Select a model:", options=list(models.keys()))
#         # model_engine = models[selected_model_name]
#
#         # CONTAINERIZED OUTPUT DISPLAY
#         num_files = len(uploaded_files)
#         num_rows = (num_files + 2) // 3
#
#         rows = [st.container() for _ in range(num_rows)]
#
#         file_index = 0
#         for row in rows:
#             with row:
#                 cols = st.columns(3)
#                 for col in cols:
#                     if file_index < num_files:
#                         uploaded_file = uploaded_files[file_index]
#                         file_extension = uploaded_file.name.split(".")[-1].lower()
#                         with col:
#                             if file_extension in ["jpg", "jpeg", "png"]:
#                                 bytes_data = io.BytesIO(uploaded_file.getvalue())
#                                 image = Image.open(bytes_data)
#                                 if st.checkbox(f"Select PDF: {uploaded_file.name}"):
#                                     st.session_state['selected_file'] = uploaded_file.name
#                                     st.image(image, caption=f"Selected Image: {uploaded_file.name}", use_column_width=True)
#                                     st.write(f"You have selected: {uploaded_file.name}")
#                                 else:
#                                     st.image(image, caption=f"Image: {uploaded_file.name}", use_column_width=True)
#                             elif file_extension == "pdf":
#                                 doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
#                                 page = doc.load_page(0)
#                                 pix = page.get_pixmap()
#                                 img = Image.open(io.BytesIO(pix.tobytes("png")))
#                                 # Using a checkbox to select the image
#                                 if st.checkbox(f"Select PDF: {uploaded_file.name}"):
#                                     st.session_state['selected_file'] = uploaded_file.name
#                                     st.image(img, caption=f"Selected PDF: {uploaded_file.name}", use_column_width=True)
#                                     st.write(f"You have selected: {uploaded_file.name}")
#                                     if st.button("Chat to AI", key=f"chat_{uploaded_file.name}"):
#                                         pdf_bytes = uploaded_file.getvalue()
#                                         doc = fitz.open(stream=pdf_bytes, filetype="pdf")
#                                         pdf_images = []
#                                         pdf_texts = []  # List to store text from all pages
#
#                                         for page_index in range(len(doc)):
#                                             page = doc[page_index]
#                                             pix = page.get_pixmap()
#                                             image_data = pix.tobytes()
#                                             pdf_image = Image.open(io.BytesIO(image_data))
#                                             pdf_images.append(pdf_image)
#
#                                             text = pytesseract.image_to_string(pdf_image)
#                                             pdf_texts.append(text)  # Accumulate text from each page
#
#                                         st.session_state['pdf_images'] = pdf_images
#                                         st.session_state['pdf_texts'] = pdf_texts
#                                         st.session_state['file_name'] = uploaded_file.name
#                                         st.session_state['chat_file_name'] = uploaded_file.name
#
#                                         nav_page("chat_to_ai")
#                                     if st.button("Get Summary", key=f"summary_{uploaded_file.name}"):
#                                         # Handle summary action here
#                                         st.write(f"Getting summary for {uploaded_file.name}...")
#                                 else:
#                                     st.image(img, caption=f"PDF: {uploaded_file.name}", use_column_width=True)
#                                 doc.close()
#                             else:
#                                 st.write(f"Unsupported file format for {uploaded_file.name}")
#                         file_index += 1
# else:
#     st.write('Please register or log in to continue.')
# file_extension = uploaded_file.name.split(".")[-1].lower()
#
# if file_extension in ["jpg", "jpeg", "png"]:
#     image = Image.open(uploaded_file)
#     st.image(image, caption="Uploaded image", use_column_width=True)
#     save_uploaded_file(uploaded_file, 'temp.jpg')
#     base64_image = encode_image('temp.jpg')
#     send_image_to_openai(base64_image)


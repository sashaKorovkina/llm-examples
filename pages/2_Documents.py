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
    query = docs_ref.order_by('uploaded_at', direction=firestore.Query.DESCENDING).limit(1)
    docs = query.stream()
    # docs = docs_ref.get()
    files = [doc.to_dict() for doc in docs]
    file = files[len(files)-1]
    return file


def check_file(file):
    response = requests.get(file['url'])
    response_url = file['url']
    response_filename = file['filename']
    if response.status_code == 200:
        st.markdown(f"[{response_filename}]({response_url})")
    else:
        st.write(f"Failed: {response.status_code} file name: {file['filename']}")


def create_thumbnail(image_stream, format):
    size = (128, 128)
    image = Image.open(image_stream)
    image.thumbnail(size)

    thumb_io = io.BytesIO()
    image.save(thumb_io, format, quality=95)
    thumb_io.seek(0)
    return thumb_io


def display_file_with_thumbnail(file):
    if file.get('thumbnail_url'):
        link = f"[![Thumbnail]({file['thumbnail_url']})]({file['url']})"
        st.markdown(link, unsafe_allow_html=True)
    else:
        st.markdown(f"[{file['filename']}]({file['url']})")

def parse_text():
    st.write('parsing...')


def pdf_page_to_image(pdf_stream):
    doc = fitz.open("pdf", pdf_stream)
    page = doc.load_page(0)

    pix = page.get_pixmap(matrix=fitz.Matrix(72 / 72, 72 / 72))

    img_bytes = io.BytesIO()
    img_bytes.write(pix.tobytes("png"))
    img_bytes.seek(0)

    doc.close()
    return img_bytes

def pdf_parse_content(file):
    if st.button("Chat to AI", key=f"chat_{file}"):
        st.write('trying to parse...')
        bucket = storage.bucket()
        blob = bucket.blob(file)
        pdf_bytes = blob.download_as_bytes()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    #     pdf_bytes = uploaded_file.getvalue()
    # st.write('trying to parse...')
    pass
def upload_file(uploaded_file, thumbnail_stream):
    blob = bucket.blob(f"{username}/{uuid.uuid4()}_{uploaded_file.name}")
    blob.upload_from_string(uploaded_file.getvalue(), content_type=uploaded_file.type)

    # Prepare the thumbnail
    if thumbnail_stream:
        thumb_blob = bucket.blob(f"{username}/{uuid.uuid4()}_thumb_{uploaded_file.name}")
        thumb_blob.upload_from_string(thumbnail_stream.getvalue(), content_type='image/png')

        thumb_url = thumb_blob.generate_signed_url(version="v4", expiration=datetime.timedelta(minutes=10000),
                                                   method='GET')
    else:
        thumb_url = None

    url = blob.generate_signed_url(version="v4", expiration=datetime.timedelta(minutes=10000), method='GET')

    doc_ref = db.collection('users').document(username).collection('documents').document()
    doc_ref.set({
        'filename': uploaded_file.name,
        'content_type': uploaded_file.type,
        'url': url,
        'thumbnail_url': thumb_url,
        'uploaded_at': firestore.SERVER_TIMESTAMP
    })

    return doc_ref.get().to_dict()


st.title("Documents")

def display_file_with_thumbnail(file):
    if file.get('thumbnail_url'):
        st.image(file['thumbnail_url'], caption=file['filename'], width=300)
    else:
        st.markdown(f"[{file['filename']}]({file['url']})")

def parse_text(file):
    # Dummy function to represent parsing
    st.write(f"Parsing text from {file['filename']}...")

# Page access control
if st.session_state.logged_in:
    username = st.session_state.username

    uploaded_file = st.file_uploader("Choose images or PDFs...", type=["jpg", "jpeg", "png", "pdf"],
                                     accept_multiple_files=False)

    if uploaded_file:
        thumbnail_stream = None
        if uploaded_file.type.startswith('image/'):
            thumbnail_stream = create_thumbnail(uploaded_file, uploaded_file.type.split('/')[-1])
        elif uploaded_file.type.startswith('application/pdf'):
            thumbnail_stream = pdf_page_to_image(uploaded_file.getvalue())

        upload_file(uploaded_file, thumbnail_stream)
        st.write(f'Current document is:')
        file = get_last_file()
        display_file_with_thumbnail(file)

    files = get_existing_files()

    if files:
        st.write(f'All files are:')
        for file in files:
            display_file_with_thumbnail(file)
            file_extension = file['filename'].split(".")[-1].lower()
            if file_extension in ["jpg", "jpeg", "png"]:
                st.write('I am an image')
            elif file_extension == "pdf":
                st.write('I am a pdf')
                file_path = 'nYta7NVFjsZ1yKmm0W7JCSQZfF33/94052005-9e90-43ab-9462-0ee2fa94c51b_Completion of Studies.docx.pdf'
                pdf_parse_content(file_path)

        # st.write("The existing files are:")
        # display_file_with_thumbnail(file)
        # selected_files = []  # List to store selected files
        #
        # # Display files with a checkbox for each one
        # for file in files:
        #     if st.checkbox(f"Select {file['filename']}", key=file['filename']):
        #         selected_files.append(file)

        # # Button to perform actions on selected files
        # if st.button('Process Selected Files'):
        #     for file in selected_files:
        #         display_file_with_thumbnail(file)
        #         parse_text(file)

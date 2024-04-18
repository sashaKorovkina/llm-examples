import streamlit as st
import base64
import streamlit as st
import requests
from PIL import Image
import fitz
import io
import pytesseract
import shutil

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

def send_text_to_openai(text_content, model_engine):
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

    if st.button("Get Explanation"):
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

            print(response.json())
            st.success("Explanation: {}".format(response.json()['choices'][0]['message']['content']))
        except Exception as e:
            st.error(f"Error: {e}")


st.title("Image Explanation Chatbot!")

uploaded_file = st.file_uploader("Choose an image or PDF...", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file is None:
    st.write("What are you doing? No file was chosen")

selected_model_name = st.selectbox("Select a model:", options=list(models.keys()))
model_engine = models[selected_model_name]

st.write(f"Drivers, start your engine : {model_engine}")

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
    for page_index in range(len(doc)):
        page = doc[page_index]
        pix = page.get_pixmap()
        image_data = pix.tobytes()
        pdf_image = Image.open(io.BytesIO(image_data))
        pdf_images.append(pdf_image)

    for index, pdf_image in enumerate(pdf_images):
        st.image(pdf_image, caption="Uploaded PDF to image", use_column_width=True)
        pdf_image.save(f'page_{index + 1}.png')

        # send image to openai
        # with open(f'page_{index + 1}.png', 'rb') as image_file:
        #    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        #    send_image_to_openai(base64_image)

        # send text to openai
        text = pytesseract.image_to_string(f'page_{index + 1}.png')
        st.write(f"Text from Page {index + 1}:")
        st.write(text)
        send_text_to_openai(text, model_engine)



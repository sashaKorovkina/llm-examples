import streamlit as st
import base64
import streamlit as st
import requests
from PIL import Image
import fitz
import io

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

st.title("📝 File Q&A with Anthropic")

uploaded_file = st.file_uploader("Choose an image or PDF...", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file is None:
    st.write("What are you doing? No file was chosen")

selected_model_name = st.selectbox("Select a model:", options=list(models.keys()))
model_engine = models[selected_model_name]

st.write(f"Drivers, start your engine : {model_engine}")

question = st.text_input(
    "Ask something about the article",
    placeholder="Can you give me a short summary?",
    disabled=not uploaded_file,
)

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
# if uploaded_file and question and not anthropic_api_key:
#     st.info("Please add your Anthropic API key to continue.")
#
# if uploaded_file and question and anthropic_api_key:
#     article = uploaded_file.read().decode()
#     prompt = f"""{anthropic.HUMAN_PROMPT} Here's an article:\n\n<article>
#     {article}\n\n</article>\n\n{question}{anthropic.AI_PROMPT}"""
#
#     client = anthropic.Client(api_key=anthropic_api_key)
#     response = client.completions.create(
#         prompt=prompt,
#         stop_sequences=[anthropic.HUMAN_PROMPT],
#         model="claude-v1",  # "claude-2" for Claude 2 model
#         max_tokens_to_sample=100,
#     )
#     st.write("### Answer")
#     st.write(response.completion)

import streamlit as st
import firebase_admin

from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import firestore

# Access the secrets from Streamlit's secrets.toml file
secrets = st.secrets["firebase-auth"]

# Display the "My cool secrets:" string along with the values
st.write("My cool secrets:", secrets["type"])
st.write("Project ID:", secrets["project_id"])
st.write("Private Key ID:", secrets["private_key_id"])
st.write("Private Key:", secrets["private_key"])
st.write("Client Email:", secrets["client_email"])
st.write("Client ID:", secrets["client_id"])
st.write("Auth URI:", secrets["auth_uri"])
st.write("Token URI:", secrets["token_uri"])
st.write("Auth Provider X509 Cert URL:", secrets["auth_provider_x509_cert_url"])
st.write("Client X509 Cert URL:", secrets["client_x509_cert_url"])
st.write("Universe Domain:", secrets["universe_domain"])

def initialize_firebase_app():
    try:
        # Attempt to get the app, which will throw an exception if it doesn't exist
        firebase_admin.get_app()
    except ValueError:
        cred = st.secrets["firebase-auth"]
        #cred = credentials.Certificate(r"C:\Users\sasha\PycharmProjects\elmento\elmento-secret.json")
        firebase_admin.initialize_app(cred)


# Call the function to initialize the app
initialize_firebase_app()


st.title('Welcome to :violet[MDX learn]')

if 'username' not in st.session_state:
    st.session_state.username = ''

if 'useremail' not in st.session_state:
    st.session_state.useremail = ''

def f():
    try:
        user = auth.get_user_by_email(email)
        print(user.uid)

        st.success('Login Successfully!')

        st.session_state.username = user.uid
        st.session_state.useremail = user.email

        st.session_state.signout = True
        st.session_state.signedout = True
    except:
        st.warning('Login Failed')

# sign out function
def t():
    st.session_state.signout = False
    st.session_state.signedout = False
    st.session_state.username = ''

if 'signedout' not in st.session_state:
    st.session_state.signedout = False
if 'signout' not in st.session_state:
    st.session_state.signout = False

if not st.session_state['signedout']:
    choice = st.selectbox('Login/Signup', ['Login', 'Sign Up'])

    if choice == 'Login':
        email = st.text_input('Email Address')
        password = st.text_input('Password', type='password')

        st.button('Login', on_click=f)
    else:
        email = st.text_input('Email Address')
        password = st.text_input('Password', type='password')

        username = st.text_input('Enter your unique username')

        if st.button('Create my account'):
            user = auth.create_user(email=email, password=password, uid=username)

            st.success('Account created successfully!')
            st.markdown('Please login using your email and password')
            st.balloons()

    # if st.session_state.signout:
    #     st.text('Name: ' + st.session_state.username)
    #     st.text('Email: ' + st.session_state.useremail)
    #
    #     if 'db' not in st.session_state:
    #         st.session_state.db = ''
    #
    #     db = firestore.client()
    #
    #     st.session_state.db = db

        # docs = db.collection('Quizzes').get()
        #
        # for doc in docs:
        #     d = doc.to_dict()
        #     if d['Username'] == st.session_state.username:
        #         st.text('Taken Quizzes')
        #         taken_quizzes = d['taken_quizzes']
        #         quiz_scores = d['quiz_scores']
        #
        #         for i in range(len(taken_quizzes) - 1, -1, -1):
        #             st.text_area(label=':green[Quiz name: {}]'.format(taken_quizzes[i]),
        #                          value=taken_quizzes[i] + ': ' + str(quiz_scores[i]) + '/10 points', height=10, key=i)
        #     else:
        #         continue
        #     print(d)

        # st.button('Sign out', on_click=t)

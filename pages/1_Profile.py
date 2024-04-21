import streamlit as st
import firebase_admin

from firebase_admin import credentials
from firebase_admin import auth

def initialize_firebase_app():
    try:
        # Attempt to get the app, which will throw an exception if it doesn't exist
        firebase_admin.get_app()
    except ValueError:
        # Access the secrets from Streamlit's secrets.toml file
        secrets = st.secrets["firebase-auth"]

        # Create a Firebase credential object from the JSON provided in secrets
        cred = credentials.Certificate({
            "type": secrets["type"],
            "project_id": secrets["project_id"],
            "private_key_id": secrets["private_key_id"],
            "private_key": secrets["private_key"],
            "client_email": secrets["client_email"],
            "client_id": secrets["client_id"],
            "auth_uri": secrets["auth_uri"],
            "token_uri": secrets["token_uri"],
            "auth_provider_x509_cert_url": secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": secrets["client_x509_cert_url"]
        })

        # Initialize the Firebase app with the created credential
        firebase_admin.initialize_app(cred)


# Call the function to initialize the app
initialize_firebase_app()


st.title('Welcome to :blue[Elmento]')

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
        st.session_state['logged_in'] = True
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

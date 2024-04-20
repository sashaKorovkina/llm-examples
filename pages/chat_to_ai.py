import streamlit as st

# Check if we've navigated here from a chat request
if 'navigate_to_chat' in st.session_state:
    st.title(f"Chat to AI for {st.session_state['navigate_to_chat']}")
    # Implement your chat interface here
    st.write("Here you would implement the chat interface.")

    # Optional: Clear the session state after use if no longer needed
    del st.session_state['navigate_to_chat']
else:
    st.write("No chat request found.")

import os
import openai
import time
import streamlit as st
import json
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')
assistant_id = os.getenv('ASSISTANT_ID')


# Create a client instance
client = openai.Client()

# Load assistant details from JSON file
try:
    with open('starter_questions.json', 'r') as json_file:
        assistant_questions = json.load(json_file)
except FileNotFoundError:
    print("Error: starter_questions.json file not found.")
    sys.exit(1)
except json.JSONDecodeError:
    print("Error: starter_questions.json is not a valid JSON file.")
    sys.exit(1)

# Function to update starter questions based on the assistant name
def update_starter_questions():
    starter_questions = assistant_questions.get('starter_questions', [])
    return starter_questions

def get_response(assistant_id):
    # Check if 'messages' key is not in session_state
    if "messages" not in st.session_state:
    # If not present, initialize 'messages' as an empty list
        st.session_state.messages = []
    # Iterate through messages in session_state
    for message in st.session_state.messages:
    # Display message content in the chat UI based on the role
        with st.chat_message(message["role"]):
            st.markdown(message["content"])    
    if not st.session_state.get("starter_displayed", False):
    # starter questions
        starter_questions = update_starter_questions()
        
        placeholder = st.empty()

        col1, col2 = placeholder.columns(2)

        clicked_question = False

        question_v = ""
        with col1:
            for idx, question in enumerate(starter_questions[:2]):
                button_key = f"btn_col1_{idx + 1}"  # Unique key for column 1 buttons
                if st.button(question, key=button_key):
                    question_v = question
                    clicked_question = True
                    # Replace user prompt with the starter question when clicked
                    break  # Exit the loop if a question is clicked

        with col2:
            for idx, question in enumerate(starter_questions[2:]):
                button_key = f"btn_col2_{idx + 1}"  # Unique key for column 2 buttons
                if st.button(question, key=button_key):
                    question_v = question
                    clicked_question = True
                    # Replace user prompt with the starter question when clicked
                    break  # Exit the loop if a question is clicked

        if clicked_question:
            placeholder.empty()
            st.session_state.messages.append({"role": "user", "content": question_v})
            with st.chat_message("user"):
                st.markdown(question_v)
            # Process the assistant's response using the starter question
            st.session_state.starter_displayed = True
            process_assistant_response(assistant_id, question_v)
    # Get user input from chat and proceed if a prompt is entered
    if prompt := st.chat_input("Enter your message here"):
        if not st.session_state.get("starter_displayed", False):
            placeholder.empty()
            st.session_state.starter_displayed = True
        # Add user input as a message to session_state
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user's message in the chat UI
        with st.chat_message("user"):
            st.markdown(prompt)
        # Process the assistant's response
        process_assistant_response(assistant_id, prompt)

def process_assistant_response(assistant_id, prompt):
    with st.spinner("Thinking..."):
        message_placeholder = st.empty()
        
        if "thread_id" not in st.session_state:
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id
        thread_id = st.session_state.thread_id    

        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content= prompt,
        )

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )

        while True:
            # Wait for 5 seconds
            time.sleep(0.5)

            # Retrieve the run status
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            # If run is completed, get messages
            if run_status.status == 'completed':
                break

        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
    
        last_message = messages.data[0].content[0].text.value
        st.session_state.messages.append({"role": "assistant", "content": last_message})
        # Display the assistant's response in the chat UI
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown(last_message)

def main():
    st.title('TV Assistant')

    get_response(assistant_id)
            

# Call the main function to run the app
if __name__ == "__main__":
    main()

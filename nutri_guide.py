import streamlit as st
import mysql.connector
from mysql.connector import Error
from groq import Groq
from fpdf import FPDF
import random
from langchain.chains import ConversationChain, LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

def create_connection():
    conn = None
    try:
        conn = mysql.connector.connect(
            host='localhost',     
            database='chat_history', 
            user='root',     
            password=''  
        )
        if conn.is_connected():
            print('Connected to MySQL database')
        return conn
    except Error as e:
        print(f"Error: {e}")
    return conn

def create_table(conn):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS chat_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_question TEXT NOT NULL,
        ai_response TEXT NOT NULL
    );
    """
    try:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        conn.commit()
    except Error as e:
        print(f" Creating Table Error: {e}")

def insert_chat_history(conn, user_question, ai_response):
    sql = ''' INSERT INTO chat_history (user_question, ai_response)
              VALUES (%s, %s) '''
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_question, ai_response))
        conn.commit()
    except Error as e:
        print(f"Insertion Error: {e}")

def generate_pdf(content, filename="output_dp.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    cell_width = 190
    
    for line in content.split('\n'):
        pdf.multi_cell(cell_width, 10, txt=line)

    pdf.output(filename)
    return filename

def nutrition_guide(groq_api_key):

    # NutriGuide logo
    spacer, col = st.columns([5, 1])  
    with col:  
        st.markdown("**Nutri :green[Guide]**")

    # The title and greeting message 
    st.title("Chat with NutriGuide!")
    st.write("Hello! I'm your Nutrition Guide. Feel free to tell me about your requirements!!")

    ##############################
    system_prompt = ''' You are a diet planner chatbot. Your goal is to to recommend 7 breakfast names, 7 lunch names, 7 dinner names and 5 workout names  along with sets and reps , after considering gender, age, weight, and height while ensuring that the person's cuisine choice and his/her allergies are strictly taken into consideration avoiding ingredients which give rise to the allergy along with his or her goal of the diet, also mention the macros and calories for each recommendation based on the series of questions that you will ask. After collecting the responses, you will provide a personalized plan.'''
    ##############################

    #name of model used
    model = 'gemma-7b-it'

    #memory of conversation
    conversational_memory_length = 12

    memory = ConversationBufferWindowMemory(k=conversational_memory_length, memory_key="chat_history",      return_messages=True)

    # input field for user
    user_question = st.text_input("Create your personalized diet plan by letting us know about yourself!!")

    # session state variable
    if 'chat_history' not in st.session_state:
            st.session_state.chat_history=[]
    else:
        for message in st.session_state.chat_history:
            memory.save_context(
                {'input':message['human']},
                {'output':message['AI']}
            )

    # Initializing Groq Langchain chat object and conversation
    groq_chat = ChatGroq(
        groq_api_key=groq_api_key, 
        model_name=model
    )

    # Creating connection to the MySQL database
    conn = create_connection()

    # Creating the chat_history table
    if conn is not None:
        create_table(conn)

    # If the user has asked a question,
    if user_question:

        # Chat Prompt Template
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=system_prompt
                ),  # This is the persistent system prompt that is always included at the start of the chat.

                MessagesPlaceholder(
                    variable_name="chat_history"
                ),  # To ensure chat continuation

                HumanMessagePromptTemplate.from_template(
                    "{human_input}"
                ),  # This template is where the user's current input will be injected into the prompt.
            ]
        )

        # Create a conversation chain using the LangChain LLM (Language Learning Model)
        conversation = LLMChain(
            llm=groq_chat,  # The Groq LangChain chat object initialized earlier.
            prompt=prompt,  # The constructed prompt template.
            verbose=True,   # Enables verbose output, which can be useful for debugging.
            memory=memory,  # The conversational memory object that stores and manages the conversation history.
        )
        
        # The Nutri Guide's answer
        response = conversation.predict(human_input=user_question)
        message = {'human':user_question,'AI':response}
        st.session_state.chat_history.append(message)
        
        # Storing in the database
        if conn is not None:
            insert_chat_history(conn, user_question, response)

        st.write("NutriGuide:", response)

        #button to save the output for the diet plan
        pdf_filename = generate_pdf(response)
        with open(pdf_filename, "rb") as file:
            st.download_button(
                label="Download Diet Plan",
                data=file,
                file_name=pdf_filename,
                mime="application/pdf"
            )
        

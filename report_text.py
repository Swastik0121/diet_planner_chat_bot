import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.chains import SimpleSequentialChain
from PyPDF2 import PdfReader
from fpdf import FPDF


def generate_pdf(content, filename="output_br.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    cell_width = 190
    
    for line in content.split('\n'):
        pdf.multi_cell(cell_width, 10, txt=line)

    pdf.output(filename)
    return filename

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""

    # Extract text from the first page
    if len(reader.pages) > 0:
        page = reader.pages[0]
        text += page.extract_text()

    return text

def blood_report_analyzer(groq_api_key):

    # HemaInsight logo
    spacer, col = st.columns([5, 1])  
    with col:  
        st.markdown("**:red[Hema] Insight**")

    st.title("Get Food Recommendation from your Blood Report!!")

    # Upload PDF file
    uploaded_file = st.file_uploader("Upload your Blood Report in pdf format", type="pdf")

    if uploaded_file is not None:
        # Extract text from the uploaded PDF file
        text = extract_text_from_pdf(uploaded_file)

        # Optionally, save the extracted text to a file
        if st.button("recommend diet"):
            llm_diet_planner = ChatGroq(groq_api_key=groq_api_key, model_name='gemma-7b-it')

            prompt_one = PromptTemplate(input_variables = 'text', template = "can you summarize the text provided by the user about the blood report {text}")

            chain_one = LLMChain(llm=llm_diet_planner, prompt=prompt_one)

            prompt_two = PromptTemplate(input_variables = 'summary', template = "based on the summary can you recommend food {summary}")

            chain_two = LLMChain(llm=llm_diet_planner, prompt=prompt_two)

            combined_chain = SimpleSequentialChain(chains = [chain_one, chain_two], verbose=True)

            result = combined_chain.run(text)

            st.write("Hema Insight: ", result)

            pdf_filename = generate_pdf(result)
            with open(pdf_filename, "rb") as file:
                st.download_button(
                    label="Download Recommendation",
                    data=file,
                    file_name=pdf_filename,
                    mime="application/pdf"
                )

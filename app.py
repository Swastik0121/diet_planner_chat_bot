import streamlit as st
from nutri_guide import nutrition_guide
from report_text import blood_report_analyzer

def main():
    
    # Groq API key
    groq_api_key = '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'

    st.sidebar.title("Choose any service you would like")
    # module choice
    app_choice = st.sidebar.radio("Select what you want", ("NutriGuide", "Blood Report"))

    if app_choice == "NutriGuide":
        nutrition_guide(groq_api_key)

    if app_choice == "Blood Report":
        blood_report_analyzer(groq_api_key)    


if __name__ == "__main__":
    main()

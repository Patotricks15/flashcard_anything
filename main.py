import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from typing import Dict, List
import json
from AutoLoader import AutoLoaderDocument, Pdf
from db_services import *
import ast
import altair as alt
import pandas as pd
import openai


def load_css(file_name):
    """
    Reads a CSS file and returns its content as a string.

    Parameters
    ----------
    file_name : str
        The file name of the CSS file to be read.

    Returns
    -------
    str
        The content of the CSS file as a string.

    """
    with open(file_name) as f:
        return f.read()
    
def signup_section():
    """
    Streamlit section for creating a new user account.

    Contains a form to input a username and password, and a button to register.
    If the form is incomplete, shows a warning. If the passwords do not match,
    shows an error. If the username already exists, shows an error. Otherwise,
    creates a new user and shows a success message.
    """
    st.subheader("Create Account")

    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type='password')
    confirm_password = st.text_input("Confirm Password", type='password')

    if st.button("Register"):
        if not new_user or not new_password or not confirm_password:
            st.warning("Please fill in all fields.")
            return
        if new_password != confirm_password:
            st.error("Passwords do not match.")
            return

        # Check if the user already exists
        if user_exists(new_user):
            st.error("Username already registered, please choose another.")
        else:
            # Register the user
            add_userdata(new_user, new_password)
            st.success("Account successfully created!")
            st.info("Now log in with your username and password.")


def login_section():
    """
    Streamlit section for user login.

    Prompts the user to enter their username and password,
    and checks if the credentials are valid by calling the
    login_user function. If the credentials are valid, it
    stores the user in the session state and displays a
    success message. Otherwise, it displays an error
    message.
    """
    st.subheader("Login")

    user = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        if login_user(user, password):
            st.success(f"Welcome, {user}!")
            # Store the logged-in user in the session
            st.session_state['username'] = user
        else:
            st.error("Incorrect username or password. Please try again.")
    

def study_flashcards():
    """
    Creates a flashcard study session in the Streamlit sidebar,
    replicating the same logic as your code but without using 'translations' or 'language'.
    """
    with st.sidebar.expander("Study Flashcards", expanded=True):
        st.markdown("### Flashcards Study Session")

        # Check if the user is logged in (assuming 'username' is stored in session_state)
        if 'username' not in st.session_state:
            st.warning("User not identified. Please log in to study flashcards.")
            return
        username = st.session_state['username']

    # Load searches that already have flashcards for this user
    search_list = query_searches_flashcards(username)
    # Convert to set and then to list in case of duplicates
    search_list = set(item[0] for item in search_list)

    # If there are no available searches, display a message
    if not search_list:
        st.info("There are no searches with flashcards to study.")
        return

    # Allow the user to select which "search" they want to study
    selected_search = st.selectbox(
        "Select a search to study:",
        sorted(list(search_list))
    )

    # Retrieve the saved strings (JSON/Dict) for this search
    # Retrieve the saved flashcards for this search
    flashcard_list = query_flashcards(username, selected_search)

    # Optional: load custom CSS
    css = load_css("styles.html")
    st.markdown(css, unsafe_allow_html=True)


    # Control the index of the current flashcard
    if 'current_card' not in st.session_state:
        st.session_state.current_card = 0

    # Load the flashcards ready for study
    flashcards = get_flashcards_study(username, selected_search)

    # Check if there are more flashcards to study
    if st.session_state.current_card < len(flashcards):
        # Unpack the flashcard information
        flashcard = flashcards[st.session_state.current_card]
        flashcard_name, flashcard_text, last_studied, current_interval, current_ease_factor, current_reps = flashcard

        # Display the flashcard in a styled card (HTML/CSS)
        card_html = f"""
            <div class="card">
                <div class="card-title">{flashcard_name}</div>
                <div class="small-desc">{flashcard_text}</div>
                <div class="go-corner"></div>
            </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        # Create columns for the evaluation buttons
        col1, col2, col3, col4, col5 = st.columns(5)

        # Button: Very Easy
        with col1:
            if st.button("Very Easy"):
                update_flashcard_study(username, selected_search, flashcard_name, flashcard_text,
                                       5, current_interval, current_ease_factor, current_reps)
                st.session_state.current_card += 1

        # Button: Easy
        with col2:
            if st.button("Easy"):
                update_flashcard_study(username, selected_search, flashcard_name, flashcard_text,
                                       4, current_interval, current_ease_factor, current_reps)
                st.session_state.current_card += 1

        # Button: OK
        with col3:
            if st.button("OK"):
                update_flashcard_study(username, selected_search, flashcard_name, flashcard_text,
                                       3, current_interval, current_ease_factor, current_reps)
                st.session_state.current_card += 1

        # Button: Hard
        with col4:
            if st.button("Hard"):
                update_flashcard_study(username, selected_search, flashcard_name, flashcard_text,
                                       2, current_interval, current_ease_factor, current_reps)
                st.session_state.current_card += 1

        # Button: Very Hard
        with col5:
            if st.button("Very Hard"):
                update_flashcard_study(username, selected_search, flashcard_name, flashcard_text,
                                       1, current_interval, current_ease_factor, current_reps)
                st.session_state.current_card += 1

        # If reached the end of the flashcard list, reset the index
        if st.session_state.current_card >= len(flashcards):
            st.session_state.current_card = 0

    else:
        # If there are no more flashcards to study
        st.markdown("You have no more pending flashcards for today.")


class KeyConcepts(BaseModel):
    key_concepts: str = Field(..., title="Key Concepts", description="A single and relevant Key concept extracted from the text")
    definition: str = Field(..., title="Definition", description="Simple and 3-lines technical definition of the key concept")


class Flashcards(BaseModel):
    """Extracted flashcards from the text"""
    flashcards: List[KeyConcepts]


model = ChatOpenAI(model="gpt-4o-mini")

def user_performance_dashboard():
    """
    Creates a session in Streamlit that displays user performance metrics and charts.
    """
    st.subheader("Performance Dashboard")

    # Check if the user is logged in
    if 'username' not in st.session_state:
        st.warning("Please log in to view your performance.")
        return

    username = st.session_state['username']

    # 1) Fetch daily data
    daily_reviews_df = get_daily_reviews(username)
    if daily_reviews_df.empty:
        st.info("No study records found for this user.")
        return

    # 2) Fetch general statistics
    stats = get_user_stats(username)

    # 3) Display metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reviews", stats['total_reviews'])
    col2.metric("Distinct Flashcards", stats['distinct_cards'])
    col3.metric("Average EF", stats['avg_ease_factor'])
    col4.metric("Average Interval", stats['avg_interval'])

    # 4) Daily Reviews Chart

    df_reviews = get_daily_reviews_current_year(username)
    df_reviews["study_date"] = pd.to_datetime(df_reviews["study_date"]).dt.date
    df_reviews = df_reviews.groupby("study_date", as_index=False)["reviews"].sum()
    current_year = datetime.today().year
    today = pd.to_datetime("today").normalize()
    start_date = today - pd.Timedelta(days=365)
    end_date = today
    all_days = pd.date_range(start_date, end_date)
    df_calendar = pd.DataFrame({"date": all_days})
    df_calendar["week"] = df_calendar["date"].dt.isocalendar().week
    df_calendar["weekday"] = df_calendar["date"].dt.weekday
    df_reviews["date"] = pd.to_datetime(df_reviews["study_date"])
    df_merged = pd.merge(
        df_calendar,
        df_reviews[["date", "reviews"]],
        how="left",
        on="date"
    )

    df_merged["reviews"] = df_merged["reviews"].fillna(0).astype(int)

    chart = (
        alt.Chart(df_merged)
        .mark_rect(
            cornerRadius=3,
            width = 11,
            height = 11
        )
        .encode(
            x=alt.X(
                "date:T",
                timeUnit="yearweek",
                axis=alt.Axis(format="%b", title=None)
            ),
            y=alt.Y(
                "date:T",
                timeUnit="day",
                sort=["mon","tue","wed","thu","fri","sat","sun"],
                title=None
            ),
            color=alt.condition(
                "datum.reviews > 0",
                alt.Color("reviews:Q", scale=alt.Scale(scheme="greens"), title="Reviews", legend=None),
                alt.value("#333333"),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Data"),
                alt.Tooltip("reviews:Q", title="Reviews")
            ]
        )
        .properties(
            width=800,
            height=200,
            title="Flashcards studied per day"
        )
    )

    st.altair_chart(chart)

def generate_flashcards():
    """
    Generates flashcards from a document.

    This function generates flashcards from a document by extracting the text, 
    processing it with the LLM, and saving the flashcards to the database.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Notes
    -----
    This function uses the LLM from langchain to process the text and generate the flashcards.
    The flashcards are saved to the database using the add_flashcard_study function.
    """
    st.markdown(css, unsafe_allow_html=True)

    st.title("Key Concepts Extraction - Streamlit App")

    st.write("This application extracts key concepts from a PDF and returns a structured object.")

    try:
        uploaded_file = st.file_uploader("Upload a document", type=["pdf", "docx", "csv", "html", "ppt"])
    except:
        st.error("Invalid document. Available extensions: pdf, docx, html, ppt")

    if uploaded_file is not None:
        # Define the prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert key concepts extraction algorithm. "
                    "Extract all the relevant key concepts from the text. "
                    "If you do not know the value of an attribute asked to extract, "
                    "return null for the attribute's value."
                ),
                ("human", "{text}")
            ]
        )
        if st.button("Generate Flashcards"):
            try:
                loader = AutoLoaderDocument(document=uploaded_file)
                text = loader.extract_text()

                source_search = loader.document.name

                runnable = prompt | model.with_structured_output(schema=Flashcards)
                
                with st.spinner(f"Processing {source_search}..."):
                    result = runnable.invoke(input=text)

            except openai.BadRequestError as e:
                if "context_length_exceeded" in str(e) or "maximum context length" in str(e):
                    loader = AutoLoaderDocument(document=uploaded_file, huge_file=True)
                    text = loader.extract_text()

                    source_search = loader.document.name

                    runnable = prompt | model.with_structured_output(schema=Flashcards)
                    
                    with st.spinner(f"Processing {source_search}..."):
                        result = runnable.invoke(input=text)


            flashcards = result.flashcards

            for card in flashcards:
                flashcard_name = card.key_concepts
                flashcard_text = card.definition

                card_html = f"""
                    <div class="card">
                        <div class="card-title">{flashcard_name}</div>
                        <div class="small-desc">{flashcard_text}</div>
                        <div class="go-corner">
                        </div>
                    </div>"""
                st.markdown(card_html, unsafe_allow_html=True)

                # Save the flashcards to the database
                add_flashcard_study(
                    st.session_state['username'], 
                    source_search, 
                    flashcard_name, 
                    flashcard_text
                )

def main():
    global css
    css = load_css("styles.html")
    st.title("Flashcard Anything")

    create_usertable()

    # Example sidebar menu
    menu_options = ["Home", "Login", "Sign Up", "Generate Flashcards", "Study Flashcards", "Performance Dashboard"]
    choice = st.sidebar.selectbox("Menu", menu_options)

    # If the user has already logged in, display their name
    if 'username' in st.session_state:
        st.sidebar.write(f"Logged in user: **{st.session_state['username']}**")

    if choice == "Home":
        st.write("Welcome to the home page!")
        st.write("Use the sidebar menu to log in, create an account, or study flashcards.")

    elif choice == "Login":
        login_section()

    elif choice == "Sign Up":
        signup_section()

    elif choice == "Study Flashcards":
        if 'username' in st.session_state:
            study_flashcards()
        else:
            st.warning("Please log in to study flashcards.")
    
    if choice == "Home":
        st.write("Welcome to the home page!")

    elif choice == "Generate Flashcards":
        if "username" in st.session_state:
            generate_flashcards()
        else:
            st.warning("Please log in to study flashcards.")
    
    elif choice == "Performance Dashboard":
        user_performance_dashboard()


if __name__ == "__main__":
    main()

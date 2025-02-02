# Flashcard Anything

Flashcard Anything is an **open-source Streamlit** application that allows users to generate and study flashcards extracted from documents. The application applies LLM to **extract key concepts and definitions** from uploaded files, turning them into study flashcards. Users can sign up, log in, generate flashcards from PDFs and other documents, study flashcards using **spaced repetition techniques**, and view a performance dashboard with study metrics.

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [Usage](#usage)
  - [Sign Up & Login](#sign-up--login)
  - [Generate Flashcards](#generate-flashcards)
  - [Study Flashcards](#study-flashcards)
  - [Performance Dashboard](#performance-dashboard)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Features

- **User Authentication:** Sign up and login functionality.
- **Flashcard Generation:** Upload a document (PDF, DOCX, CSV, HTML, PPT) to extract key concepts and definitions using a language model.
- **Flashcard Study Session:** Review generated flashcards with an interactive study session that uses spaced repetition (Very Easy, Easy, OK, Hard, Very Hard).
- **Performance Dashboard:** Visualize study metrics including daily reviews, average ease factor, and intervals using interactive Altair charts.
- **Custom CSS Styling:** Customizable UI using external CSS styles.
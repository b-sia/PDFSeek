## Overview
------------

MultiPDF chat app lets users upload their PDF documents, convert them to a knowledge database and let them query
from the knowledge base. Based on the tutorial from  https://github.com/alejandro-ao/ask-multiple-pdfs

## How It Works

The application follows these steps to provide responses to your questions:

1. PDF Loading: The app reads multiple PDF documents and extracts their text content.

2. Text Chunking: The extracted text is divided into smaller chunks that can be processed effectively.

3. Language Model: The application utilizes a language model to generate vector representations (embeddings) of the text chunks.

4. Similarity Matching: When you ask a question, the app compares it with the text chunks and identifies the most semantically similar ones.

5. Response Generation: The selected chunks are passed to the language model, which generates a response based on the relevant content of the PDFs.

## Models and APIs
By default, the app uses GPT-3.5-turbo as the backend LLM, which requires the user to sign up for an OpenAPI account and get the API key. Users would
also have to top up their account with token credits.

Another approach is to run LLM models locally, but be warned, as this requires your PC to have fairly powerful hardware. Models can be obtained
from https://huggingface.co/models.
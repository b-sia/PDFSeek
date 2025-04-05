# PDF Chat Application

A modern web application for chatting with PDF documents using various LLM models. The application is built with a React frontend and FastAPI backend.

## Features

- Upload and process multiple PDF documents
- Chat interface with streaming responses
- Support for both OpenAI GPT-3.5 and local LLM models
- Advanced model configuration options
- Real-time chat updates
- Document source tracking

## Project Structure

```
pdf_chat/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── pdf.py
│   │   │       ├── chat.py
│   │   │       └── model.py
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUploader.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   └── ModelConfigPanel.tsx
│   │   ├── store/
│   │   ├── api/
│   │   └── types/
│   ├── package.json
│   └── README.md
└── README.md
```

## Setup Instructions

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and other configurations
```

4. Run the backend server:
```bash
uvicorn app.main:app --reload
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your backend API URL
```

3. Run the development server:
```bash
npm run dev
```

## API Documentation

The backend API is documented using OpenAPI/Swagger. Once the backend server is running, visit:
```
http://localhost:8000/docs
```

### Key Endpoints

- `POST /api/pdf/upload`: Upload and process PDF documents
- `POST /api/chat/stream`: Stream chat responses
- `POST /api/model/configure`: Configure model parameters
- `POST /api/model/upload-local`: Upload local LLM model

## Development

### Backend Development

- The backend uses FastAPI for high performance and automatic API documentation
- Core LLM logic is separated into services
- PDF processing is handled asynchronously
- Model configuration is managed through environment variables

### Frontend Development

- Built with React and TypeScript for type safety
- Uses Chakra UI for modern, accessible components
- State management with Zustand
- Real-time updates with streaming responses

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
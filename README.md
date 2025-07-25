# VanhGPT - Flask RAG API with OpenAI & Ollama

Một ứng dụng chatbot thông minh với khả năng RAG (Retrieval-Augmented Generation) để tư vấn bán điện thoại thông minh, kết hợp giữa OpenAI và Ollama để cung cấp trải nghiệm chat đa dạng.

## ✨ Tính năng

- 🤖 **Dual Chat Modes**: Chat thường và RAG mode cho tư vấn sản phẩm
- 🔍 **Semantic Routing**: Tự động phân loại câu hỏi và chọn phương thức xử lý phù hợp
- 📱 **Product Advisory**: Tư vấn chuyên sâu về điện thoại thông minh với dữ liệu thời gian thực
- 🔐 **User Authentication**: Hệ thống đăng ký/đăng nhập với mã hóa password
- 💬 **Conversation Management**: Lưu trữ và quản lý lịch sử chat
- 🌐 **Responsive UI**: Giao diện thân thiện trên mọi thiết bị
- 🔄 **Multiple LLM Support**: Hỗ trợ cả OpenAI GPT và Ollama models

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask Backend  │    │   AI Services   │
│   (HTML/JS)     │◄──►│   (Python)       │◄──►│   OpenAI/Ollama │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   MongoDB       │
                       │   Database      │
                       └─────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Flask**: Web framework
- **MongoDB**: Database cho users, conversations, messages
- **OpenAI GPT**: Language model cho reflection và embedding
- **Ollama**: Local LLM cho chat responses
- **SentenceTransformers**: Embedding models
- **PyMongo**: MongoDB driver

### Frontend
- **HTML5/CSS3**: Responsive UI
- **Vanilla JavaScript**: Interactive features
- **Marked.js**: Markdown rendering

### AI Components
- **RAG System**: Vector search với MongoDB Atlas
- **Semantic Router**: Intelligent query routing
- **Reflection**: Query refinement
- **Embeddings**: Multiple embedding providers

## 📦 Cài đặt

### 1. Clone repository
```bash
git clone <repository-url>
cd Flask-RAG-API-OPENAI_Ollama
```

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 3. Cấu hình môi trường
Tạo file `.env` và cấu hình các biến:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
DB_NAME=your_database_name
DB_COLLECTION_PRODUCT=products
DB_COLLECTION_USERS=users
DB_COLLECTION_CONVERSATIONS=conversations
DB_COLLECTION_MESSAGES=messages

# OpenAI Configuration
OPEN_AI_KEY=your_openai_api_key

# Flask Configuration
SECRET_KEY=your_secret_key

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b

# Embedding Models
EMBEDDING_MODEL=keepitreal/vietnamese-sbert
OPEN_AI_EMBEDDING_MODEL=text-embedding-3-small
```

### 4. Thiết lập MongoDB
- Cài đặt MongoDB hoặc sử dụng MongoDB Atlas
- Tạo vector index cho collection products:
```javascript
db.products.createIndex({
  "embedding": {
    "type": "vector",
    "similarity": "cosine",
    "dimensions": 768
  }
})
```

### 5. Thiết lập Ollama
```bash
# Cài đặt Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull gemma3:4b

# Tạo custom model với Modelfile
ollama create phonebot -f Modelfile
```

## 🚀 Chạy ứng dụng

### Development
```bash
python backend.py
```

### Docker
```bash
# Build và chạy với Docker Compose
docker-compose up --build
```

Ứng dụng sẽ chạy tại: `http://localhost:5000`

## 📁 Cấu trúc dự án

```
Flask-RAG-API-OPENAI_Ollama/
├── backend.py                 # Main Flask application
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker configuration
├── Dockerfile                 # Docker build file
├── Modelfile                  # Ollama custom model
├── .env                       # Environment variables
│
├── templates/
│   └── main.html             # Main UI template
│
├── static/
│   ├── main.css              # Styles
│   ├── main.js               # Frontend logic
│   └── *.png                 # Images
│
├── embeddings/               # Embedding implementations
│   ├── __init__.py
│   ├── base.py
│   ├── openai.py
│   ├── sentenceTransformer.py
│   ├── fastEmbed.py
│   └── google.py
│
├── semantic_router/          # Semantic routing system
│   ├── __init__.py
│   ├── router.py
│   ├── route.py
│   └── samples.py
│
├── rag/                      # RAG implementation
│   └── core.py
│
├── reflection/               # Query reflection
│   ├── __init__.py
│   └── core.py
│
├── prompts/                  # Prompt templates
│   └── product.txt
│
├── openai_client.py          # OpenAI client wrapper
└── ollama_client.py          # Ollama client wrapper
```

## 🔧 API Endpoints

### Authentication
- `POST /api/register` - Đăng ký user mới
- `POST /api/login` - Đăng nhập
- `POST /api/logout` - Đăng xuất
- `GET /api/user` - Lấy thông tin user

### Chat
- `POST /api/chat/normal` - Chat thường với Ollama
- `POST /api/chat/rag` - Chat với RAG system

### Conversations
- `GET /api/conversations` - Lấy danh sách conversations
- `GET /api/conversations/<id>` - Lấy chi tiết conversation
- `DELETE /api/conversations/<id>` - Xóa conversation

## 🤖 AI Components

### 1. Semantic Router
Phân loại câu hỏi tự động:
- **Products**: Câu hỏi về sản phẩm → RAG system
- **Chitchat**: Trò chuyện thường → Normal LLM

### 2. RAG System
- Vector search trong MongoDB
- Retrieve relevant product information
- Generate contextual responses

### 3. Reflection
- Query refinement và context understanding
- Improve search relevance

## 📱 UI Features

- **Responsive Design**: Hoạt động tốt trên mobile/desktop
- **Real-time Chat**: Live conversation với typing indicators
- **Code Highlighting**: Syntax highlighting với copy buttons
- **User Management**: Profile dropdown và session management
- **Conversation History**: Lưu và load lại conversations
- **Mode Switching**: Toggle giữa normal và RAG mode

## 🔒 Security

- Password hashing với Werkzeug
- Session-based authentication
- Input validation và sanitization
- Error handling và logging

## 🚀 Deployment

### Docker
```bash
docker-compose up -d
```

### Production
- Sử dụng production WSGI server (Gunicorn)
- Cấu hình reverse proxy (Nginx)
- SSL certificate
- Environment variables security

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 🙋‍♂️ Support

Nếu gặp vấn đề, vui lòng tạo issue trên GitHub hoặc liên hệ qua email.

---

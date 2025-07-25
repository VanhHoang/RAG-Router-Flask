from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from dotenv import load_dotenv
import os
import openai
from rag.core import RAG
from embeddings import OpenAIEmbedding
from semantic_router import SemanticRouter, Route
from semantic_router.samples import productsSample, chitchatSample
from reflection import Reflection
from openai_client import OpenAIClient
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from ollama_client import OllamaClient
load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
DB_NAME = os.getenv('DB_NAME')
DB_COLLECTION_PRODUCT = os.getenv('DB_COLLECTION_PRODUCT')
DB_COLLECTION_USERS = os.getenv('DB_COLLECTION_USERS')
DB_COLLECTION_CONVERSATIONS = os.getenv('DB_COLLECTION_CONVERSATIONS')
DB_COLLECTION_MESSAGES = os.getenv('DB_COLLECTION_MESSAGES')
OPENAI_KEY = os.getenv('OPEN_AI_KEY')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL') or 'keepitreal/vietnamese-sbert'
OPEN_AI_EMBEDDING_MODEL = os.getenv('OPEN_AI_EMBEDDING_MODEL') or 'text-embedding-3-small'
MONGODB_URI = os.getenv('MONGODB_URI')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
users_collection = db[DB_COLLECTION_USERS]
conversations_collection = db[DB_COLLECTION_CONVERSATIONS]
messages_collection = db[DB_COLLECTION_MESSAGES]


OpenAIEmbedding(OPENAI_KEY)
openai_client = OpenAIClient(OPENAI_KEY, model="gpt-4.1")


# --- Semantic Router Setup --- #
PRODUCT_ROUTE_NAME = 'products'
CHITCHAT_ROUTE_NAME = 'chitchat'

openAIEmbeding = OpenAIEmbedding(apiKey=OPENAI_KEY, dimensions=1024, name=OPEN_AI_EMBEDDING_MODEL)
productRoute = Route(name=PRODUCT_ROUTE_NAME, samples=productsSample)
chitchatRoute = Route(name=CHITCHAT_ROUTE_NAME, samples=chitchatSample)
semanticRouter = SemanticRouter(openAIEmbeding, routes=[productRoute, chitchatRoute])

# --- Set up LLMs --- #
llm = OllamaClient(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL) 


# --- Relection Setup --- #
gpt = openai.OpenAI(api_key=OPENAI_KEY)
reflection = Reflection(llm=gpt)


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
CORS(app)


rag = RAG(
    mongodbUri=MONGODB_URI,
    dbName=DB_NAME,
    dbCollection=DB_COLLECTION_PRODUCT,
    embeddingName='keepitreal/vietnamese-sbert',  
    llm=llm, 
)

def load_prompt_template(file_path):
    """Load prompt template from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Prompt file not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error loading prompt: {e}")
        return None

PROMPT_TEMPLATE = load_prompt_template('prompts/product.txt')

def process_query(query):
    return query.lower()

@app.route("/")
def main():
    return render_template('main.html')

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if not username or not password or not email:
            return jsonify({'error': 'Thiếu thông tin bắt buộc'}), 400
        
        if users_collection.find_one({'username': username}):
            return jsonify({'error': 'Tên đăng nhập đã tồn tại'}), 400
        
        if users_collection.find_one({'email': email}):
            return jsonify({'error': 'Email đã được sử dụng'}), 400
        
        hashed_password = generate_password_hash(password)
        user_data = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.utcnow()
        }
        
        result = users_collection.insert_one(user_data)
        
        return jsonify({
            'message': 'Đăng ký thành công',
            'user_id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Thiếu tên đăng nhập hoặc mật khẩu'}), 400
        
        user = users_collection.find_one({'username': username})
        
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'error': 'Tên đăng nhập hoặc mật khẩu không đúng'}), 401
        
        # Tạo session
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        
        return jsonify({
            'message': 'Đăng nhập thành công',
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'email': user['email']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify({'message': 'Đăng xuất thành công'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user', methods=['GET'])
def get_user():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Chưa đăng nhập'}), 401
        
        user = users_collection.find_one({'_id': ObjectId(session['user_id'])})
        if not user:
            return jsonify({'error': 'Không tìm thấy user'}), 404
        
        conversations = get_user_conversations(session['user_id'])
        
        return jsonify({
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'email': user['email']
            },
            'conversations': conversations
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def create_conversation(user_id, mode="normal"):
    try:
        conversation_data = {
            "user_id": ObjectId(user_id),
            "create_at": datetime.utcnow(),
            "mode": mode
        }
        result = conversations_collection.insert_one(conversation_data)
        return str(result.inserted_id)
    
    except Exception as e:
        print(f"Error creating conversation: {e}")
        return None

def save_message(conversation_id, role, content):
    try:
        openai_role = 'assistant' if role == 'model' else role
        
        message_data = {
            "conversation_id": ObjectId(conversation_id),
            "role": openai_role,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        result = messages_collection.insert_one(message_data)
        return str(result.inserted_id)
    
    except Exception as e:
        print(f"Error saving message: {e}")
        return None

def get_user_conversations(user_id):
    try:
        conversations = list(conversations_collection.find(
            {"user_id": ObjectId(user_id)},
            {"_id": 1, "create_at": 1, "mode": 1}
        ).sort("create_at", -1))
        
        for conv in conversations:
            conv["_id"] = str(conv["_id"])
            first_message = messages_collection.find_one(
                {"conversation_id": ObjectId(conv["_id"]), "role": "user"},
                {"content": 1}
            )
            if first_message and first_message.get("content"):
                title = first_message["content"]
                conv["title"] = title[:30] + "..." if len(title) > 30 else title
                conv["title"] += f" ({conv['mode'].upper()})" if conv["mode"] == "rag" else ""
            else:
                conv["title"] = f"Cuộc trò chuyện mới ({conv['mode'].upper()})" if conv["mode"] == "rag" else "Cuộc trò chuyện mới"
                
        return conversations
    
    except Exception as e:
        print(f"Error getting conversations: {e}")
        return []

def get_conversation_messages(conversation_id):
    try:
        messages = list(messages_collection.find(
            {"conversation_id": ObjectId(conversation_id)},
            {"role": 1, "content": 1, "timestamp": 1}
        ).sort("timestamp", 1))
        
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"] if msg.get("content") else ""
            })
        
        return formatted_messages
    
    except Exception as e:
        print(f"Error getting messages: {e}")
        return []

def delete_conversation_and_messages(conversation_id, user_id):
    try:
        conversation = conversations_collection.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": ObjectId(user_id)
        })
        
        if not conversation:
            return False
        
        messages_collection.delete_many({"conversation_id": ObjectId(conversation_id)})
        conversations_collection.delete_one({"_id": ObjectId(conversation_id)})
        
        return True
    
    except Exception as e:
        print(f"Error deleting conversation: {e}")
        return False

# --- Normal Chat Endpoint --- #
@app.route('/api/chat/normal', methods=['POST'])
def chat_normal():
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        conversation_id = data.get('conversation_id')
        
        if not isinstance(messages, list) or not messages:
            return jsonify({'error': 'Định dạng tin nhắn không hợp lệ'}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Yêu cầu đăng nhập'}), 401
        
        if not conversation_id:
            conversation_id = create_conversation(user_id, "normal")
            if not conversation_id:
                return jsonify({'error': 'Không thể tạo cuộc trò chuyện'}), 500
        
        user_message = messages[-1]["content"]
        
        save_message(conversation_id, "user", user_message)
        
        for message in messages:
            if 'role' not in message or 'content' not in message:
                return jsonify({'error': 'Định dạng tin nhắn không hợp lệ'}), 400
        
        print(f"Calling Ollama for normal chat with {len(messages)} messages")
        response_text = llm.chat(messages)  
    

        save_message(conversation_id, "assistant", response_text)
        
        return jsonify({
            'content': response_text,
            'role': 'assistant',
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        print(f"Normal chat error: {str(e)}")
        return jsonify({'error': f'Lỗi xử lý: {str(e)}'}), 500



@app.route('/api/chat/rag', methods=['POST'])
def chat_rag():
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        conversation_id = data.get('conversation_id')
        
        if not isinstance(messages, list) or not messages:
            return jsonify({'error': 'Định dạng tin nhắn không hợp lệ'}), 400
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Yêu cầu đăng nhập'}), 401
        
        if not conversation_id:
            conversation_id = create_conversation(user_id, "rag")
            if not conversation_id:
                return jsonify({'error': 'Không thể tạo cuộc trò chuyện'}), 500
        
        query = messages[-1]["content"]
        user_message = query
        query = process_query(query)

        if not query:
            return jsonify({'error': 'Không có truy vấn'}), 400
        
        save_message(conversation_id, "user", user_message)
        
        print(f"Processing query for semantic routing: {query[:50]}...")
        guidedRoute = semanticRouter.guide(query)[1]
        print(f"Semantic router decision: {guidedRoute}")

        if guidedRoute == PRODUCT_ROUTE_NAME:
            print("Routing to RAG system with Ollama")
            
            openai_messages = []
            for msg in messages:
                role = "assistant" if msg["role"] == "model" else msg["role"]
                openai_messages.append({
                    "role": role,
                    "content": msg["content"]
                })
            
            reflected_query = reflection(openai_messages)
            query = reflected_query
            
            source_information = rag.enhance_prompt(query).replace('<br>', '\n')
            
            combined_information = PROMPT_TEMPLATE.format(
                    query=query,
                    source_information=source_information
                )

            enhanced_messages = openai_messages.copy()
            enhanced_messages.append({
                "role": "user",
                "content": combined_information
            })
            
            response = rag.generate_content(enhanced_messages)
        else:
            print("Routing to normal LLM")
            openai_messages = []
            for msg in messages:
                role = "assistant" if msg["role"] == "model" else msg["role"]
                openai_messages.append({
                    "role": role,
                    "content": msg["content"]
                })
            
            response = llm.generate_content(openai_messages)

        save_message(conversation_id, "assistant", response.text)

        return jsonify({
            'content': response.text,
            'role': 'assistant',
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        print(f"RAG chat error: {str(e)}")
        return jsonify({'error': f'Lỗi xử lý RAG: {str(e)}'}), 500


@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        conversations = get_user_conversations(session['user_id'])
        return jsonify({
            'conversations': conversations
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        conversation = conversations_collection.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": ObjectId(session['user_id'])
        })
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        messages = get_conversation_messages(conversation_id)
        
        return jsonify({
            'conversation': {
                'id': str(conversation['_id']),
                'mode': conversation['mode'],
                'created_at': conversation['create_at'].isoformat(),
                'messages': messages
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        
        success = delete_conversation_and_messages(conversation_id, session['user_id'])
        
        if not success:
            return jsonify({'error': 'Failed to delete conversation or conversation not found'}), 404
        
        return jsonify({
            'message': 'Conversation deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

import os
import sqlite3
import uuid
import mimetypes
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from groq import Groq
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# --- CRITICAL FIX FOR WINDOWS UI BREAKING ---
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Simplified since we are serving everything from one port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTHENTICATION CONFIGURATION ---
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
security = HTTPBearer()
pwd = CryptContext(schemes=["bcrypt"])

# --- AI CONFIGURATION ---
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY environment variable not set.")
client = Groq(api_key=api_key)

DB_USERS = "users.db"
DB_CHAT = "datas.db"

# --- DATABASE INITIALIZATIONS ---
def init_users_db():
    with sqlite3.connect(DB_USERS) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, email TEXT UNIQUE, password TEXT)""")

def init_chat_db():
    with sqlite3.connect(DB_CHAT) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_id TEXT,
            role TEXT,
            content TEXT
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER,
            title TEXT
        )''')
        conn.commit()

init_users_db()
init_chat_db()

# --- MODELS ---
class User(BaseModel):
    name: str = ""
    email: str
    password: str

class ChatMessage(BaseModel):
    user_input: str
    session_id: str = None
    token: str = None
    is_guest: bool = False
    guest_history: list = []

class ClearRequest(BaseModel):
    token: str

# --- AUTHENTICATION HELPERS ---
def create_token(data):
    return jwt.encode({**data, "exp": datetime.utcnow() + timedelta(minutes=60)}, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(c: HTTPAuthorizationCredentials = Depends(security)):
    try: 
        return jwt.decode(c.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except: 
        raise HTTPException(status_code=401, detail="Invalid token")

# --- AUTHENTICATION ENDPOINTS ---
@app.post("/signup")
def signup(u: User):
    if len(u.password.encode()) > 72:
        raise HTTPException(status_code=400, detail="Password too long")
    with sqlite3.connect(DB_USERS) as conn:
        if conn.execute("SELECT 1 FROM users WHERE email=?", (u.email,)).fetchone():
            raise HTTPException(status_code=400, detail="User exists")
        conn.execute("INSERT INTO users (name, email, password) VALUES (?,?,?)",
                     (u.name, u.email, pwd.hash(u.password)))
    return {"message": "Signup successful"}

@app.post("/login")
def login(u: User):
    with sqlite3.connect(DB_USERS) as conn:
        r = conn.execute("SELECT id, name, email, password FROM users WHERE email=?", (u.email,)).fetchone()
        if not r or not pwd.verify(u.password, r[3]):
            raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"access_token": create_token({"user_id": r[0], "email": r[2], "name": r[1]})}

@app.get("/profile")
def profile(user=Depends(verify_token)):
    return {"user": user}

# --- AI CHATBOT ENDPOINTS ---
@app.post("/chat")
async def chat(msg: ChatMessage):
    try:
        system_prompt = {"role": "system", "content": "You are Scripl AI, a sophisticated assistant. Use markdown for clarity."}
        
        # GUEST MODE
        if msg.is_guest:
            messages = [system_prompt] + msg.guest_history + [{"role": "user", "content": msg.user_input}]
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages,
                temperature=0.7,
            )
            ai_response = completion.choices[0].message.content
            return {"reply": ai_response}

        # AUTHENTICATED MODE
        if not msg.token:
            return {"reply": "**System Error:** Not authenticated."}
            
        user_data = jwt.decode(msg.token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = user_data["user_id"]
        session_id = msg.session_id
        title = None
        
        with sqlite3.connect(DB_CHAT) as conn:
            cursor = conn.cursor()
            
            if not session_id:
                session_id = "sess_" + str(uuid.uuid4().hex[:10])
                title = msg.user_input[:20] + ("..." if len(msg.user_input) > 20 else "")
                cursor.execute("INSERT INTO sessions (session_id, user_id, title) VALUES (?, ?, ?)", 
                               (session_id, user_id, title))
            
            cursor.execute("INSERT INTO history (user_id, session_id, role, content) VALUES (?, ?, ?, ?)", 
                           (user_id, session_id, "user", msg.user_input))
            
            cursor.execute("""
                SELECT role, content FROM (
                    SELECT id, role, content FROM history 
                    WHERE user_id = ? AND session_id = ?
                    ORDER BY id DESC LIMIT 10
                ) ORDER BY id ASC
            """, (user_id, session_id))
            
            rows = cursor.fetchall()
            messages = [system_prompt] + [{"role": r[0], "content": r[1]} for r in rows]
            
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages,
                temperature=0.7,
            )
            ai_response = completion.choices[0].message.content
            
            cursor.execute("INSERT INTO history (user_id, session_id, role, content) VALUES (?, ?, ?, ?)", 
                           (user_id, session_id, "assistant", ai_response))
            
        return {"reply": ai_response, "session_id": session_id, "title": title}
    except Exception as e:
        return {"reply": f"**System Error:** {str(e)}"}

@app.get("/sessions")
async def get_sessions(token: str):
    try:
        user_data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = user_data["user_id"]
        with sqlite3.connect(DB_CHAT) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, title FROM sessions WHERE user_id = ? ORDER BY rowid DESC", (user_id,))
            sessions = [{"session_id": r[0], "title": r[1]} for r in cursor.fetchall()]
        return {"sessions": sessions}
    except:
        return {"sessions": []}

@app.get("/session/{session_id}")
async def get_session_history(session_id: str, token: str):
    try:
        user_data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = user_data["user_id"]
        with sqlite3.connect(DB_CHAT) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM history WHERE user_id = ? AND session_id = ? ORDER BY id ASC", 
                           (user_id, session_id))
            messages = [{"role": r[0], "content": r[1]} for r in cursor.fetchall()]
        return {"messages": messages}
    except:
        return {"messages": []}

@app.post("/clear")
async def clear_chat(req: ClearRequest):
    try:
        user_data = jwt.decode(req.token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = user_data["user_id"]
        with sqlite3.connect(DB_CHAT) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        return {"status": "Memory wiped"}
    except:
        return {"status": "Error"}

# --- FRONTEND SERVING FOR PORT 8000 ---
@app.get("/")
def serve_home():
    return FileResponse("index.html")

app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

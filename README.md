# Scripl AI 🚀

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/Groq-AI-F55036?style=for-the-badge&logo=openai&logoColor=white)](https://groq.com/)
[![Render](https://img.shields.io/badge/Render-Hosting-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)

**Scripl AI** is a lightweight, high-performance full-stack AI chatbot platform featuring secure user authentication, persistent SQLite session management, and ultra-fast LLM generation powered by Groq. Built for scalability and speed, it provides both authenticated user workflows and an immediate guest-skip mode.

---

## ✨ Features

* **Secure Authentication System:** User signup and login utilizing `bcrypt` password hashing and stateless JSON Web Tokens (JWT) for session security.
* **Persistent Chat History:** Multi-session tracking backed by SQLite, allowing users to save, switch, and reload past conversation threads.
* **Ultra-Fast LLM Inference:** Integrated with Groq's high-performance AI engines (`openai/gpt-oss-20b`) for instantaneous responses.
* **Dual Access Modes:** Full authentication suite alongside an instant "Guest Mode" for frictionless user engagement.
* **Modern Minimalist UI:** Custom responsive web interface featuring dynamic markdown support, code highlighting, and clean typography.
* **Production Ready:** Pre-configured for cloud deployment on platforms like Render via Uvicorn ASGI workers.

---

## 🛠️ Tech Stack

* **Backend:** Python, FastAPI, Uvicorn, Pydantic
* **Database:** SQLite (`users.db`, `datas.db`)
* **Security & Auth:** Passlib (`bcrypt`), Python-JOSE (JWT), HTTPBearer
* **AI Engine:** Groq API SDK
* **Frontend:** HTML5, Modern CSS3, Vanilla JavaScript (served directly via FastAPI static mounts)

---

## 📦 Local Installation & Setup Guide

Follow these steps to run **Scripl AI** locally on your machine.

### Prerequisites
* Python 3.10 or higher installed on your system.
* Git installed.
* A valid **Groq API Key** (obtainable from the [Groq Console](https://console.groq.com/)).

### 1. Clone the Repository
Open your terminal and clone the project:
```bash
git clone https://github.com/satyakamswami/ScriplAI.git
cd ScriplAI
```

### 2. Set Up a Virtual Environment
It is recommended to run the project inside an isolated virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
Install the required Python packages pinned for compatibility:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Set your Groq API key in your local environment terminal session:
* **On Windows (PowerShell):**
  ```powershell
  $env:GROQ_API_KEY="your_actual_groq_api_key_here"
  ```
* **On macOS/Linux:**
  ```bash
  export GROQ_API_KEY="your_actual_groq_api_key_here"
  ```

### 5. Run the Application
Start the FastAPI server using Uvicorn:
```bash
python backpower.py
```
*(Alternatively: `uvicorn backpower:app --reload`)*

### 6. Access the App
Open your web browser and navigate to:
👉 **`http://127.0.0.1:8000`**

---

## 🚀 Deployment (Render)

This application is live on Render! To deploy your own instance:
1. Connect your GitHub repository as a **Web Service** on Render.
2. Set the **Runtime** to `Python 3`.
3. Configure the **Build Command**: 
   ```bash
   pip install -r requirements.txt
   ```
4. Configure the **Start Command**: 
   ```bash
   uvicorn backpower:app --host 0.0.0.0 --port $PORT
   ```
5. Add your environment variable key `GROQ_API_KEY` under the Render dashboard settings.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

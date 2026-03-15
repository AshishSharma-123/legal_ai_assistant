from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from flask_bcrypt import Bcrypt
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or "your_secret_key"

bcrypt = Bcrypt(app)

# ---------------- MySQL Connection ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="flask_login"
)
cursor = db.cursor(dictionary=True)

# ---------------- Gemini API ----------------
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

# ===================== Routes =====================

# Landing Page
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- Signup ----------------
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (username, email, hashed_password))
        db.commit()
        flash("Signup successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template("signup.html")

# ---------------- Login ----------------
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for('login'))
    return render_template("login.html")

# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# ---------------- Home ----------------
@app.route("/home")
def home():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))
    return render_template("home.html", username=session['username'])

# ---------------- Chat ----------------
# 

@app.route('/chat', methods=['POST'])
def chat():

    # 1️⃣ CHECK IF USER LOGGED IN
    if 'user_id' not in session:
        return jsonify({'reply': "You must be logged in to chat."})

    # 2️⃣ GET USER INPUT
    data = request.get_json()
    topic = data.get('topic', '').lower()
    state = data.get('state', 'India')
    language = data.get('language', 'English')
    message = data.get('message')
    user_id = session['user_id']

    # ========== AUTO-GENERATE TITLE ==========
    title = ""
    if len(message) > 30:
        title = message[:30] + "..."
    else:
        title = message


    # 3️⃣ BASE PROMPT
    base_prompt = f"""
You are a legal-assistant bot. Jurisdiction: India.

Topic: {topic}
State: {state}
Language: {language}
User Query: {message}

Answer concisely using this structure:
1. Short answer
2. Relevant laws/sections
3. Explanation (2–4 sentences)
4. Practical next steps

Formatting rules:
- Use clear headings
- Use bullet points or numbering
- Highlight key terms in bold
- Use icons (📌, ⚖️, etc.) to improve UX
- Keep sentences short and clear
"""

    # 4️⃣ TOPIC-SPECIFIC EXTENSIONS
    topic_extensions = {
        "general": """
5. Overview of Indian law
6. State-specific variations if relevant
""",
        "contract": """
5. Common contract types
6. Risks & remedies
7. Add a sample clause (2–3 lines)
""",
        "property": """
5. Transfer methods
6. Required documents
7. State-specific stamp duty variations
""",
        "family": """
5. Divorce grounds
6. Custody & maintenance guidance
7. Evidence checklist
""",
        "criminal": """
5. Offence classification
6. Evidence requirements
7. Add a short FIR template with IPC sections
""",
        "civil": """
5. Civil dispute types
6. Remedies
7. Court process & appeal rights
""",
        "cyber": """
5. IT Act sections (66, 67, 69, 72A)
6. Common cyber crimes
7. Complaint process
""",
        "it": """
5. IT Act sections (66, 67, 69, 72A)
6. Common cyber crimes
7. Complaint process
""",
        "rti": """
5. RTI filing process
6. Appeals
7. Section 8 exemptions
"""
    }

    base_prompt += topic_extensions.get(topic, "\n5. Add sources if available")

    try:
        # 5️⃣ GENERATE REPLY USING GEMINI
        response = model.generate_content(base_prompt)
        bot_reply = response.text.strip()

        # 6️⃣ SAVE TO DATABASE
        cursor.execute(
                "INSERT INTO chat_history (user_id, title, user_message, bot_reply) VALUES (%s, %s, %s, %s)",
                (user_id, title, message, bot_reply)
        )

        db.commit()

        # 7️⃣ RETURN REPLY
        return jsonify({'reply': bot_reply})

    except Exception as e:
        return jsonify({'reply': f"Error: {str(e)}"})


@app.route('/history', methods=['GET'])
def history():

    if 'user_id' not in session:
        return jsonify({"error": "You must be logged in to view history."}), 401

    user_id = session['user_id']

    try:
        cursor.execute(
            "SELECT title, user_message, bot_reply, created_at FROM chat_history WHERE user_id=%s ORDER BY created_at DESC",
            (user_id,)
        )
        chats = cursor.fetchall()

        history_list = []
        for chat in chats:
            history_list.append({
                "title": chat["title"],
                "user_message": chat["user_message"],
                "bot_reply": chat["bot_reply"],
                "time": str(chat["created_at"])
            })

        return jsonify({"history": history_list})

    except Exception as e:
        return jsonify({"error": str(e)})




if __name__ == "__main__":
    app.run(debug=True)

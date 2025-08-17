from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure API Key
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/home")
def home():
    return render_template("home.html")


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    topic = data.get('topic')
    state = data.get('state')
    language = data.get('language')
    message = data.get('message')

    # Base prompt
    base_prompt = f"""
You are a legal-assistant bot. Jurisdiction: India (unless user states otherwise).

Topic: {topic}
State: {state}
Language: {language}
User Query: {message}

Answer user legal questions concisely and accurately.
Required format:
1. Short answer (1-2 sentences)
2. Relevant law sections/case names (if known)
3. Explanation (2-4 sentences)
4. Suggested next steps (practical)
"""

    # Add extra sections only for certain topics
    if topic.lower() in ["contract", "labour", "property", "family", "criminal", "civil","it"]:
        extra = """
5. Sources: include short URL(s) or say "No reliable source found" if none
6. Evidence: include evidence that may be required for case
7. FIR: Guide user how to draft a FIR for the given situation and what section should be used (5-6 sentences)
"""
        base_prompt += extra
    else:
        # For general info, RTI, IT, etc.
        base_prompt += "\n5. Sources: include short URL(s) or say 'No reliable source found' if none"

    try:
        response = model.generate_content(base_prompt)
        return jsonify({'reply': response.text.strip()})
    except Exception as e:
        return jsonify({'reply': f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)

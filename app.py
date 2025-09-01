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
    topic = data.get('topic', '').lower()
    state = data.get('state', 'India')
    language = data.get('language', 'English')
    message = data.get('message')

    # Base prompt
    base_prompt = f"""
You are a legal-assistant bot. Jurisdiction: India (unless user states otherwise).

Topic: {topic}
State: {state}
Language: {language}
User Query: {message}

Answer user legal questions concisely and accurately.
When answering, always use a structured, user-friendly format that improves readability and UX.  
Follow these rules:  
1. Start with a clear **title/heading**.  
2. Use **numbered or bulleted points** for explanation.  
3. Highlight important terms in **bold**.  
4. Add small **icons or symbols** (📌, ✅, ⚖️, etc.) to improve visual experience.  
5. Keep sentences **short and scannable**.  
6. End with an **example or next step** if applicable.  

Now, answer the following question in this structured format 
headings are:
1. Short answer (1-2 sentences)
2. Relevant law sections/case names (if known)
3. Explanation (2-4 sentences)
4. Suggested next steps (practical)
"""

    # Topic-wise extensions
    if topic == "general":
        base_prompt += """
For general queries:
5. Provide overview of law in India
6. Highlight state-specific variations (if {state} relevant)
"""
    elif topic == "contract":
        base_prompt += """
5. Common Contract Types (employment, property, partnership, etc.)
6. Risks & Remedies (breach, damages, injunctions)
7. Sample Clause: suggest a basic clause user can include (2–3 lines)
"""
    elif topic == "property":
        base_prompt += """
5. Ownership & Transfer Methods (sale, gift, inheritance, lease, mortgage)
6. Documents Required (title deed, encumbrance, registration)
7. State-Specific Variation (stamp duty, registration fees in {state})
"""
    elif topic == "family":
        base_prompt += """
5. Marriage/Divorce Grounds (HMA, SMA, IDA, etc.)
6. Custody & Maintenance guidance
7. Evidence Checklist (marriage certificate, income proof, witnesses)
"""
    elif topic == "criminal":
        base_prompt += """
5. Offence Classification (cognizable/non-cognizable, bailable/non-bailable)
6. Evidence Required (FIR, witness, documents, forensic)
7. FIR Guide: Draft short FIR template + relevant IPC sections (5-6 sentences)
"""
    elif topic == "civil":
        base_prompt += """
5. Types of Civil Disputes (property, contracts, torts, family)
6. Remedies (damages, injunction, specific performance)
7. Court Process (jurisdiction, limitation, appeal rights)
"""
    elif topic in ["cyber", "it"]:
        base_prompt += """
5. Relevant IT Act Provisions (Sec 66, 67, 69, 72A IT Act, 2000)
6. Common Cyber Crimes (hacking, phishing, identity theft, revenge porn)
7. Complaint Process (cyber crime portal, police station, CERT-In)
"""
    elif topic == "rti":
        base_prompt += """
5. RTI Process (PIO application, ₹10 fee, 30-day limit)
6. Appeals (first appeal, second appeal to Info Commission)
7. Exemptions (Sec 8 RTI Act: security, national interest, personal data)
"""
    else:
        base_prompt += "\n5. Sources: include short URL(s) or say 'No reliable source found' if none"

    try:
        response = model.generate_content(base_prompt)
        return jsonify({'reply': response.text.strip()})
    except Exception as e:
        return jsonify({'reply': f"Error: {str(e)}"})


if __name__ == "__main__":
    app.run(debug=True)

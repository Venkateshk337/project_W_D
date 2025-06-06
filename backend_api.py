from flask import Flask, request, jsonify
import google.generativeai as genai
from PIL import Image
import json
import sqlite3
from datetime import datetime
import base64
from io import BytesIO

app = Flask(__name__)

# Configure Gemini AI
GEMINI_API_KEY = "AIzaSyCQuWWutRYb9UYpDKxgtBMekmPmi8KjCWs"  # Replace with your actual key
genai.configure(api_key=GEMINI_API_KEY)

class CheckProcessorAPI:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.init_database()

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect('checks_api.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_processed_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_number TEXT,
                amount REAL,
                payee TEXT,
                date TEXT,
                bank_name TEXT,
                account_number TEXT,
                routing_number TEXT,
                memo TEXT,
                confidence_score REAL,
                fraud_risk_score REAL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'processed'
            )
        ''')
        conn.commit()
        conn.close()

    def process_check_image(self, image_data):
        """Process check image and extract data"""
        try:
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))

            prompt = """
            Analyze this bank check image and extract the following information in JSON format:
            {
                "check_number": "check number",
                "amount": "dollar amount (numeric value only)",
                "amount_words": "amount written in words",
                "payee": "pay to the order of",
                "date": "date on check (YYYY-MM-DD format)",
                "bank_name": "bank name",
                "account_number": "account number",
                "routing_number": "routing number",
                "memo": "memo field",
                "signature_present": "true/false",
                "potential_fraud_indicators": ["list any suspicious elements"]
            }
            """

            response = self.model.generate_content([prompt, image])
            response_text = response.text

            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            print(response_text)

            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                extracted_data = json.loads(response_text)

                # Set fixed confidence score
                extracted_data['confidence_score'] =.9

                # Fraud risk score
                fraud_score = self.calculate_fraud_risk(extracted_data)
                extracted_data['fraud_risk_score'] = fraud_score

                return extracted_data
            else:
                return {"error": "Could not parse Gemini response"}
        except Exception as e:
            return {"error": str(e)}

    def calculate_fraud_risk(self, data):
        """Calculate fraud risk score"""
        score = 0
        indicators = data.get('potential_fraud_indicators', [])
        score += len(indicators) * 20

        if data.get('amount', 0) > 10000:
            score += 15

        if data.get('signature_present', 'false') == 'false':
            score += 25

        critical_fields = ['check_number', 'amount', 'payee', 'date']
        missing = sum(1 for f in critical_fields if data.get(f) in [None, '', 'N/A'])
        score += missing * 10

        return min(score, 100)

    def save_processed_check(self, data):
        """Save processed check to database"""
        print("Extracted Data:", data)

        try:
            conn = sqlite3.connect('checks_api.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO api_processed_checks 
                (check_number, amount, payee, date, bank_name, account_number, 
                 routing_number, memo, confidence_score, fraud_risk_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('check_number', 'N/A'),
                data.get('amount', 0.0),
                data.get('payee', 'N/A'),
                data.get('date', 'N/A'),
                data.get('bank_name', 'N/A'),
                data.get('account_number', 'N/A'),
                data.get('routing_number', 'N/A'),
                data.get('memo', 'N/A'),
                data.get('confidence_score', 0.85),
                data.get('fraud_risk_score', 0.0)
            ))

            conn.commit()
            check_id = cursor.lastrowid
            conn.close()
            return check_id
        except Exception as e:
            print("DB Error:", e)
            return None

processor = CheckProcessorAPI()

@app.route('/api/process-check', methods=['POST'])
def process_check():
    try:
        data = request.json
        print("Received request:", data)

        image_data = data.get('image')
        if not image_data:
            return jsonify({"error": "No image data provided"}), 400

        result = processor.process_check_image(image_data)
        print("Processing result:", result)

        if result and 'error' not in result:
            check_id = processor.save_processed_check(result)
            print("Saved check ID:", check_id)

            result['check_id'] = check_id
            return jsonify({
                "success": True,
                "data": result,
                "message": "Check processed successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Processing failed')
            }), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/checks', methods=['GET'])
def get_checks():
    try:
        conn = sqlite3.connect('checks_api.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM api_processed_checks ORDER BY processed_at DESC')

        columns = [col[0] for col in cursor.description]
        checks = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            "success": True,
            "data": checks,
            "count": len(checks)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        conn = sqlite3.connect('checks_api.db')
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM api_processed_checks')
        total_checks = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(amount) FROM api_processed_checks')
        total_amount = cursor.fetchone()[0] or 0

        cursor.execute('SELECT AVG(confidence_score) FROM api_processed_checks')
        avg_conf = cursor.fetchone()[0] or 0

        cursor.execute('SELECT AVG(fraud_risk_score) FROM api_processed_checks')
        avg_fraud = cursor.fetchone()[0] or 0

        conn.close()

        return jsonify({
            "success": True,
            "analytics": {
                "total_checks": total_checks,
                "total_amount": round(total_amount, 2),
                "average_confidence": round(avg_conf, 2),
                "average_fraud_risk": round(avg_fraud, 2)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

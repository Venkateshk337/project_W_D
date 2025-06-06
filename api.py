from flask import Flask, request, jsonify
import google.generativeai as genai
from PIL import Image
import json
import base64
from io import BytesIO
import os

app = Flask(__name__)

# Configure Gemini AI
GEMINI_API_KEY = "AIzaSyCQuWWutRYb9UYpDKxgtBMekmPmi8KjCWs"
genai.configure(api_key=GEMINI_API_KEY)


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "Bank Check Processor"})


@app.route('/api/process', methods=['POST'])
def process_check():
    try:
        data = request.json
        image_data = data.get('image')

        if not image_data:
            return jsonify({"error": "No image data provided"}), 400

        # Decode base64 image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        image = Image.open(BytesIO(image_bytes))

        # Process with Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = """
        Extract check information in JSON format:
        {
            "check_number": "number",
            "amount": "numeric amount",
            "payee": "pay to",
            "date": "YYYY-MM-DD",
            "bank_name": "bank"
        }
        """

        response = model.generate_content([prompt, image])

        # Parse response
        response_text = response.text
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start != -1 and json_end != -1:
            result = json.loads(response_text[json_start:json_end])
            return jsonify({"success": True, "data": result})
        else:
            return jsonify({"error": "Failed to parse response"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

import cv2
import numpy as np
from PIL import Image
import google.generativeai as genai
import json
import base64
import io

class FraudDetectionEngine:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def detect_image_tampering(self, image):
        """Detect potential image tampering using OpenCV."""
        try:
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size

            suspicious_score = 0
            if edge_density > 0.15:
                suspicious_score += 30

            hsv = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1, 2], None, [50, 60, 60], [0, 180, 0, 256, 0, 256])
            hist_variance = np.var(hist)
            if hist_variance > 1000:
                suspicious_score += 20

            return {
                "tampering_score": min(suspicious_score, 100),
                "edge_density": edge_density,
                "color_variance": float(hist_variance)
            }

        except Exception as e:
            return {"error": str(e)}

    def analyze_signature_authenticity(self, image):
        """Use Gemini AI to analyze signature authenticity."""
        try:
            # Convert image to Gemini-compatible format
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='PNG')
            image_bytes.seek(0)

            gemini_image = {
                "mime_type": "image/png",
                "data": image_bytes.read()
            }

            prompt = """
            Analyze the signature on this check image and provide a detailed assessment:

            1. Signature quality and consistency
            2. Pen pressure variations
            3. Natural flow vs. traced appearance
            4. Any signs of forgery or alteration
            5. Overall authenticity score (0-100)

            Provide response in JSON format:
            {
                "signature_quality": "description",
                "authenticity_score": numeric_score,
                "fraud_indicators": ["list of concerns"],
                "recommendation": "accept/review/reject"
            }
            """

            response = self.model.generate_content([prompt, genai.types.Blob(gemini_image)])
            response_text = response.text

            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                return {"error": "Could not parse AI response"}

        except Exception as e:
            return {"error": str(e)}

    def comprehensive_fraud_analysis(self, image, extracted_data):
        """Combine visual and data checks for overall fraud risk score."""
        results = {
            "overall_risk_score": 0,
            "risk_factors": [],
            "recommendation": "accept"
        }

        tampering_result = self.detect_image_tampering(image)
        if "tampering_score" in tampering_result:
            results["overall_risk_score"] += tampering_result["tampering_score"] * 0.3
            if tampering_result["tampering_score"] > 50:
                results["risk_factors"].append("Potential image tampering detected")

        signature_result = self.analyze_signature_authenticity(image)
        if "authenticity_score" in signature_result:
            risk_from_signature = (100 - signature_result["authenticity_score"]) * 0.4
            results["overall_risk_score"] += risk_from_signature
            if signature_result["authenticity_score"] < 70:
                results["risk_factors"].append("Questionable signature authenticity")

        amount = extracted_data.get("amount", 0)
        if amount > 50000:
            results["overall_risk_score"] += 20
            results["risk_factors"].append("Unusually high check amount")

        critical_fields = ["check_number", "amount", "payee", "date"]
        missing_count = sum(1 for field in critical_fields if extracted_data.get(field) in ["N/A", "", None])
        if missing_count > 1:
            results["overall_risk_score"] += missing_count * 15
            results["risk_factors"].append(f"Missing {missing_count} critical fields")

        final_score = min(results["overall_risk_score"], 100)
        results["overall_risk_score"] = final_score

        if final_score >= 70:
            results["recommendation"] = "reject"
        elif final_score >= 40:
            results["recommendation"] = "manual_review"

        return results


# 🔬 Example usage with sample image and dummy data
def test_fraud_detection():
    api_key = "AIzaSyCQuWWutRYb9UYpDKxgtBMekmPmi8KjCWs"  # WARNING: Never expose real keys in prod
    fraud_detector = FraudDetectionEngine(api_key)

    image_path = "sample_check.png"  # Replace with actual image file path
    image = Image.open(image_path)

    extracted_data = {
        "check_number": "123456",
        "amount": 60000,
        "payee": "John Doe",
        "date": "2024-01-15"
    }

    print("Running fraud detection...")
    result = fraud_detector.comprehensive_fraud_analysis(image, extracted_data)
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    test_fraud_detection()

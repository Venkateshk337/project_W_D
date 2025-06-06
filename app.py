import streamlit as st

# This must be the first Streamlit command
st.set_page_config(
    page_title="Automated Bank Check Processing",
    page_icon="🏦",
    layout="wide"
)

import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
from io import BytesIO
import base64

# ✅ Directly set Gemini API key here
GEMINI_API_KEY = "AIzaSyCQuWWutRYb9UYpDKxgtBMekmPmi8KjCWs"

if not GEMINI_API_KEY:
    st.error("Gemini API key not set.")
else:
    genai.configure(api_key=GEMINI_API_KEY)


class CheckProcessor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect('checks.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_checks (
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
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                image_data BLOB
            )
        ''')
        conn.commit()
        conn.close()

    def extract_check_data(self, image):
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
            "signature_present": "true/false"
        }

        If any field is not clearly visible or missing, use "N/A" as the value.
        """

        try:
            response = self.model.generate_content([prompt, image])
            response_text = response.text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                return self.validate_extracted_data(data)
            else:
                return None
        except Exception as e:
            st.error(f"Extraction error: {str(e)}")
            return None

    def validate_extracted_data(self, data):
        if 'amount' in data and data['amount'] != "N/A":
            try:
                data['amount'] = float(str(data['amount']).replace('$', '').replace(',', ''))
            except:
                data['amount'] = 0.0
        if 'date' in data:
            try:
                datetime.strptime(data['date'], '%Y-%m-%d')
            except:
                data['date'] = "N/A"

        filled = sum(1 for v in data.values() if v not in ("", "N/A"))
        data['confidence_score'] = round((filled / len(data)) * 100, 2)
        return data

    def save_to_database(self, data, image):
        try:
            conn = sqlite3.connect('checks.db')
            cursor = conn.cursor()
            img_bytes = BytesIO()
            image.save(img_bytes, format='PNG')
            cursor.execute('''
                INSERT INTO processed_checks 
                (check_number, amount, payee, date, bank_name, account_number,
                 routing_number, memo, confidence_score, image_data)
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
                data.get('confidence_score', 0.0),
                img_bytes.getvalue()
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Database save error: {str(e)}")
            return False

    def get_processed_checks(self):
        try:
            conn = sqlite3.connect('checks.db')
            df = pd.read_sql_query('''
                SELECT id, check_number, amount, payee, date, bank_name,
                       confidence_score, processed_at
                FROM processed_checks
                ORDER BY processed_at DESC
            ''', conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Database read error: {str(e)}")
            return pd.DataFrame()


def main():
    st.title("🏦 Automated Bank Check Processing")
    processor = CheckProcessor()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Process Check", "View Results", "Analytics"])

    if page == "Process Check":
        uploaded_files = st.file_uploader("Upload check image(s)", type=["png", "jpg", "jpeg"],
                                          accept_multiple_files=True)
        if uploaded_files:
            for file in uploaded_files:
                st.subheader(f"File: {file.name}")
                image = Image.open(file)
                st.image(image, caption="Uploaded Check", use_column_width=True)

                if st.button(f"Process {file.name}"):
                    with st.spinner("Extracting..."):
                        data = processor.extract_check_data(image)
                        if data:
                            st.json(data)
                            st.progress(data['confidence_score']/100)
                            if st.button(f"Save to Database - {file.name}"):
                                if processor.save_to_database(data, image):
                                    st.success("Saved successfully.")
                        else:
                            st.error("Failed to extract data.")

    elif page == "View Results":
        st.header("📑 Processed Checks")
        df = processor.get_processed_checks()
        if not df.empty:
            st.dataframe(df)
            st.download_button("Download CSV", df.to_csv(index=False), "checks.csv", "text/csv")
        else:
            st.info("No data yet. Please process a check.")

    elif page == "Analytics":
        st.header("📈 Analytics Dashboard")
        df = processor.get_processed_checks()
        if not df.empty:
            st.metric("Total Checks", len(df))
            st.metric("Total Amount", f"${df['amount'].sum():,.2f}")
            st.metric("Avg Confidence", f"{df['confidence_score'].mean():.2f}%")

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.histogram(df, x='amount', title='Amount Distribution'), use_container_width=True)
            with col2:
                st.plotly_chart(px.histogram(df, x='confidence_score', title='Confidence Score'),
                                use_container_width=True)

            df['date_only'] = pd.to_datetime(df['processed_at']).dt.date
            timeline = df.groupby('date_only').size().reset_index(name='count')
            st.plotly_chart(px.line(timeline, x='date_only', y='count', title="Daily Check Volume"))
        else:
            st.info("Analytics will appear after processing checks.")


if __name__ == "__main__":
    main()

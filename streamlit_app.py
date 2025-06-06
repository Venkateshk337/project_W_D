import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64
import os
import tempfile

# ✅ Set Streamlit page config FIRST before any Streamlit command
st.set_page_config(
    page_title="Bank Check Processing",
    page_icon="🏦",
    layout="wide"
)

# Configure Gemini AI
GEMINI_API_KEY = "AIzaSyCQuWWutRYb9UYpDKxgtBMekmPmi8KjCWs"
genai.configure(api_key=GEMINI_API_KEY)


class CheckProcessor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.db_path = self.get_db_path()
        self.init_database()

    def get_db_path(self):
        if os.environ.get('VERCEL'):
            return '/tmp/checks.db'
        else:
            return 'checks.db'

    def init_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
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
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Database initialization error: {str(e)}")

    def extract_check_data(self, image):
        try:
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
            Be very careful with the amount extraction - it should be a numeric value.
            """

            response = self.model.generate_content([prompt, image])
            response_text = response.text

            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                extracted_data = json.loads(json_str)
                extracted_data = self.validate_extracted_data(extracted_data)
                return extracted_data
            else:
                return None
        except Exception as e:
            st.error(f"Error extracting data: {str(e)}")
            return None

    def validate_extracted_data(self, data):
        if 'amount' in data and data['amount'] != "N/A":
            amount_str = str(data['amount']).replace('$', '').replace(',', '')
            try:
                data['amount'] = float(amount_str)
            except:
                data['amount'] = 0.0

        total_fields = len(data)
        filled_fields = sum(1 for v in data.values() if v != "N/A" and v != "")
        data['confidence_score'] = (filled_fields / total_fields) * 100

        return data

    def save_to_database(self, data):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO processed_checks 
                (check_number, amount, payee, date, bank_name, account_number, 
                 routing_number, memo, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('check_number', 'N/A'),
                data.get('amount', 0.0),
                data.get('payee', 'N/A'),
                data.get('date', 'N/A'),
                data.get('bank_name', 'N/A'),
                data.get('account_number', 'N/A'),
                data.get('routing_number', 'N/A'),
                data.get('memo', 'N/A'),
                data.get('confidence_score', 0.0)
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error saving to database: {str(e)}")
            return False

    def get_processed_checks(self):
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('''
                SELECT id, check_number, amount, payee, date, bank_name, 
                       confidence_score, processed_at
                FROM processed_checks
                ORDER BY processed_at DESC
            ''', conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error retrieving data: {str(e)}")
            return pd.DataFrame()


def main():
    st.title("🏦 Automated Bank Check Processing System")
    st.markdown("Upload bank check images for automated data extraction and processing")

    processor = CheckProcessor()

    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Process Checks", "View Results", "Analytics"])

    if page == "Process Checks":
        st.header("📄 Upload and Process Checks")

        uploaded_file = st.file_uploader("Choose a check image", type=['png', 'jpg', 'jpeg'])

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            col1, col2 = st.columns(2)

            with col1:
                st.image(image, caption="Uploaded Check", use_column_width=True)

            with col2:
                if st.button("Process Check"):
                    with st.spinner("Extracting data from check..."):
                        extracted_data = processor.extract_check_data(image)

                        if extracted_data:
                            st.success("✅ Data extracted successfully!")
                            st.json(extracted_data)

                            confidence = extracted_data.get('confidence_score', 0)
                            if confidence >= 80:
                                st.success(f"High confidence: {confidence:.1f}%")
                            elif confidence >= 60:
                                st.warning(f"Medium confidence: {confidence:.1f}%")
                            else:
                                st.error(f"Low confidence: {confidence:.1f}%")

                            if st.button("Save to Database"):
                                if processor.save_to_database(extracted_data):
                                    st.success("✅ Data saved to database!")
                                else:
                                    st.error("❌ Failed to save data")
                        else:
                            st.error("❌ Failed to extract data from check")

    elif page == "View Results":
        st.header("📊 Processed Checks")

        df = processor.get_processed_checks()

        if not df.empty:
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"processed_checks_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No processed checks found. Upload and process some checks first!")

    elif page == "Analytics":
        st.header("📈 Analytics Dashboard")

        df = processor.get_processed_checks()

        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Checks", len(df))
            with col2:
                st.metric("Total Amount", f"${df['amount'].sum():,.2f}")
            with col3:
                st.metric("Avg Confidence", f"{df['confidence_score'].mean():.1f}%")
            with col4:
                high_confidence = len(df[df['confidence_score'] >= 80])
                st.metric("High Confidence", f"{high_confidence}/{len(df)}")

            col1, col2 = st.columns(2)
            if len(df) > 1:
                with col1:
                    fig_amount = px.histogram(df, x='amount', title="Check Amount Distribution", nbins=min(20, len(df)))
                    st.plotly_chart(fig_amount, use_container_width=True)
                with col2:
                    fig_confidence = px.histogram(df, x='confidence_score', title="Confidence Score Distribution",
                                                  nbins=min(10, len(df)))
                    st.plotly_chart(fig_confidence, use_container_width=True)
        else:
            st.info("No data available for analytics. Process some checks first!")


if __name__ == "__main__":
    main()

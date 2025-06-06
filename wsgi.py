from app import main
import streamlit.web.cli as stcli
import sys
import os

def run_streamlit():
    """Run Streamlit app for WSGI deployment"""
    sys.argv = [
        "streamlit",
        "run",
        "app.py",
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true"
    ]
    stcli.main()

if __name__ == "__main__":
    run_streamlit()

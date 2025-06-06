from app import main
import streamlit as st
import os

# Configure for Vercel deployment
if __name__ == "__main__":
    # Set environment variables for Vercel
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    
    main()

import subprocess
import sys
import os


def install_requirements():
    """Install required packages"""
    requirements = [
        "streamlit==1.28.1",
        "google-generativeai==0.3.2",
        "Pillow==10.0.1",
        "pandas==2.1.1",
        "plotly==5.17.0",
        "opencv-python==4.8.1.78",
        "flask==2.3.3"
    ]

    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")


def run_streamlit_app():
    """Run the Streamlit application"""
    try:
        print("🚀 Starting Automated Bank Check Processing System...")
        print("📱 Open your browser and go to: http://localhost:8501")

        # Run streamlit app
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port=8501"])

    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {str(e)}")


if __name__ == "__main__":
    print("🏦 Automated Bank Check Processing System")
    print("=" * 50)

    # Install requirements
    print("📦 Installing required packages...")
    install_requirements()

    print("\n" + "=" * 50)

    # Run the app
    run_streamlit_app()

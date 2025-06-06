# 🏦 Automated Bank Check Processing System

An AI-powered system for automated bank check processing using OCR and entity recognition.

## Features

- **OCR Processing**: Extract text from check images using Gemini AI
- **Entity Recognition**: Automatically identify check details (amount, payee, date, etc.)
- **Fraud Detection**: AI-powered fraud risk assessment
- **Analytics Dashboard**: Comprehensive processing metrics and charts
- **Data Storage**: Structured storage in SQLite database

## Quick Start

### Local Development

1. **Clone the repository**
\`\`\`bash
git clone <repository-url>
cd bank-check-processor
\`\`\`

2. **Install dependencies**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

3. **Run the application**
\`\`\`bash
streamlit run app.py
\`\`\`

4. **Access the application**
Open your browser and go to `http://localhost:8501`

### Docker Deployment

\`\`\`bash
docker build -t bank-check-processor .
docker run -p 8501:8501 bank-check-processor
\`\`\`

### Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini AI API key
- `PORT`: Port number for the application (default: 8501)

## Usage

1. **Upload Check Images**: Drag and drop check images in the "Process Checks" section
2. **Extract Data**: Click "Process" to extract check information using AI
3. **Review Results**: Check confidence scores and extracted data
4. **Save to Database**: Store processed checks for future reference
5. **View Analytics**: Monitor processing metrics and trends

## API Endpoints

- `POST /api/process-check`: Process a check image
- `GET /api/checks`: Retrieve all processed checks
- `GET /api/analytics`: Get processing analytics

## Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python, Flask
- **AI/ML**: Google Gemini AI
- **Database**: SQLite
- **Visualization**: Plotly
- **Image Processing**: OpenCV, Pillow

## Security Features

- Image tampering detection
- Signature authenticity analysis
- Fraud risk scoring
- Data validation and sanitization

## License

MIT License - see LICENSE file for details.

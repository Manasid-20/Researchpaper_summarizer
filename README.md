# Researchpaper_summarizer
An AI-powered Streamlit app that turns a research paper PDF into a structured
summary — objective, methodology, key findings, conclusion, and keywords —
using Google's Gemini API.

## Features

- Drag-and-drop PDF upload with page/word/read-time stats
- Text extraction via PyMuPDF
- AI-generated structured summary (Gemini 1.5 Flash or Pro)
- Download the summary as `.txt` or `.md`
- API key loaded securely from a `.env` file (no hardcoded secrets)

## Project structure

```
ai-research-summarizer/
├── app.py              # Streamlit application
├── requirements.txt    # Python dependencies
├── .env.example        # Template for your API key
├── .gitignore
└── README.md
```

## 1. Get a Gemini API key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in and click **Create API key**.
3. Copy the key — you'll need it in step 3 below.

## 2. Clone and set up the project locally

```bash
git clone https://github.com/<your-username>/ai-research-summarizer.git
cd ai-research-summarizer

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## 3. Configure your API key

Copy the example env file and add your key:

```bash
cp .env.example .env
```

Open `.env` and set:

```
GEMINI_API_KEY=your_actual_key_here
```

The app reads this automatically at startup. If no `.env` key is found, the
sidebar will let you paste a key manually for that session instead.

## 4. Run the app

```bash
streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

## 5. Push this project to GitHub

```bash
git init
git add .
git commit -m "Initial commit: AI Research Paper Summarizer"
git branch -M main
git remote add origin https://github.com/<your-username>/ai-research-summarizer.git
git push -u origin main
```

`.env` is already listed in `.gitignore`, so your API key will never be
committed. Only `.env.example` (with a placeholder) is tracked.

## 6. Deploy (optional)

To deploy on **Streamlit Community Cloud**:

1. Push the repo to GitHub (step 5).
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. Set the main file path to `app.py`.
4. Under **Advanced settings → Secrets**, add:
   ```
   GEMINI_API_KEY = "your_actual_key_here"
   ```
5. Deploy.

## Tech stack

- Python
- Streamlit
- PyMuPDF
- Google Gemini API
- python-dotenv

## License

MIT — feel free to use and modify.

---
Developed by **Manasi Dewalkar**

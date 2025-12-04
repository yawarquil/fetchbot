# MovieFetchBot 🎬

A modern web application for fetching movie and TV series data from TMDB API with multiple export format support.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- 🔍 **Smart Search** - Find movies and TV shows with autocomplete
- 📺 **Full Details** - Cast, ratings, episodes, and more
- 📥 **Multi-Format Export** - JSON, CSV, SQL, TXT, XML
- 📤 **Batch Processing** - Upload a list and export all at once
- 🔐 **User Authentication** - JWT-based with JSON storage
- 🎨 **Modern UI** - Dark theme with glassmorphism design

## 🚀 Quick Start

### Local Development

1. **Clone and install dependencies:**
```bash
cd telegrambot
pip install -r requirements.txt
```

2. **Run the application:**
```bash
streamlit run app.py
```

3. **Open in browser:**
Navigate to `http://localhost:8501`

### Docker

```bash
docker build -t moviefetchbot .
docker run -p 8501:8501 moviefetchbot
```

## 📁 Project Structure

```
telegrambot/
├── app.py              # Streamlit main UI
├── api/
│   └── main.py         # FastAPI backend
├── sources/
│   └── tmdb.py         # TMDB API client
├── exporters/
│   ├── json_exporter.py
│   ├── txt_exporter.py
│   ├── sql_exporter.py
│   ├── csv_exporter.py
│   └── xml_exporter.py
├── models/
│   └── schemas.py      # Pydantic models
├── utils/
│   ├── auth.py         # JWT authentication
│   └── validators.py   # Input validation
├── data/               # User data storage
├── requirements.txt
├── Dockerfile
└── README.md
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TMDB_API_KEY` | Your TMDB API key | Built-in |
| `JWT_SECRET_KEY` | Secret for JWT tokens | Auto-generated |

## 📤 Export Formats

| Format | Best For |
|--------|----------|
| **JSON** | APIs, web integration |
| **CSV** | Spreadsheets, analysis |
| **SQL** | Database imports |
| **TXT** | Quick reading, logs |
| **XML** | Legacy systems |

## 🚀 Deploy to Render

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect repository
4. Use Docker environment
5. Deploy!

## 📝 License

MIT License - feel free to use for personal and commercial projects.

---

Built with ❤️ using Streamlit and TMDB API

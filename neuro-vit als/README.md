# Neuro-Vitals: Predictive Health Intelligence System

An AI-powered hackathon project featuring adversarial diagnosis, health trajectory forecasting, and community health intelligence.

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Run the server
python -m app.main
```

Server will run at: http://localhost:8000
API Docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
# Open index.html in your browser
# Or use a simple HTTP server:
python -m http.server 3000
```

Frontend will be at: http://localhost:3000

## 🎯 Features

### 1. Smart Symptom Analysis
- AI-powered diagnosis with explainable reasoning
- Confidence scoring
- Personalized recommendations

### 2. Adversarial Diagnosis Engine ⚔️
- Two AI models debate the diagnosis
- Prosecutor AI argues for primary diagnosis
- Defense AI finds contradictions
- Judge AI synthesizes final verdict

### 3. Temporal Health Trajectory 📈
- 6-month health risk forecasting
- Baseline vs intervention scenarios
- Interactive visualization

### 4. Community Health Intelligence 🌐
- Real-time outbreak detection
- Heat map visualization
- Transmission velocity tracking

## 🔧 Environment Variables

Create a `.env` file in the `backend` directory:

```env
OPENAI_API_KEY=your_key_here
MODEL_PROVIDER=mock  # Use 'openai' with real API key
ENABLE_ADVERSARIAL=True
ENABLE_TRAJECTORY=True
ENABLE_COMMUNITY=True
```

## 📁 Project Structure

```
neuro-vitals/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── config.py        # Configuration
│   │   ├── schemas.py       # Pydantic models
│   │   ├── routers/         # API endpoints
│   │   └── services/        # Business logic
│   └── requirements.txt
└── frontend/
    └── index.html           # Single-page application
```

## 🎬 Demo Usage

1. Start the backend server
2. Open frontend in browser
3. Fill in patient information
4. Try each feature:
   - **Symptom Analysis**: Get AI diagnosis
   - **Adversarial**: Watch AI debate
   - **Trajectory**: See 6-month forecast
   - **Community**: View outbreak map

## 🏆 Hackathon Features

- **Technical Excellence**: Adversarial AI system
- **Clinical Value**: Temporal forecasting
- **Public Health Impact**: Outbreak detection
- **Premium UI**: Modern, responsive design
- **Full-Stack**: FastAPI + Vanilla JS

## 📝 License

MIT License - Built for International Hackathon 2026

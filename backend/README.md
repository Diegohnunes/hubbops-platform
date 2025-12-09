# Hubbops Backend

FastAPI backend for the Hubbops Internal Developer Platform.

## Features

- **RESTful API** for templates and services management
- **WebSocket** support for real-time logs
- **CORS** enabled for frontend integration
- **Pydantic** schemas for request/response validation
- **ops-cli** integration for service provisioning

## Setup

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### Running

```bash
# Use the start script (recommended)
./start.sh

# Or manually with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Templates

- `GET /api/templates` - List all templates
- `GET /api/templates/{id}` - Get template details

### Services

- `POST /api/services/` - Create a new service
- `GET /api/services/` - List all services
- `GET /api/services/{id}` - Get service details
- `DELETE /api/services/{id}` - Delete a service
- `WS /api/services/ws/{id}/logs` - Real-time logs (WebSocket)

### Health

- `GET /` - API info
- `GET /health` - Health check

## Project Structure

```
backend/
├── app/
│   ├── api/           # API route handlers
│   ├── core/          # Core configurations
│   ├── models/        # Database models (future)
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   └── main.py        # FastAPI app
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
└── start.sh          # Startup script
```

## Development

The backend is configured to auto-reload on code changes when using `--reload` flag.

## Next Steps

- [ ] Implement actual ops-cli integration
- [ ] Add database for service persistence
- [ ] Implement authentication
- [ ] Add Kubernetes API integration
- [ ] Implement template validation

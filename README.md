# Vue + MapLibre GL JS Monorepo

This project is a monorepo containing both frontend (Vue 3) and backend (FastAPI) applications.

## Project Structure
```
├── src/                # Frontend Vue application
├── backend/           # Backend FastAPI application
├── dist/             # Built frontend files
├── vite.config.js    # Vite configuration
└── package.json      # Node dependencies and scripts
```

## Development

### Prerequisites
- Node.js
- Python 3.x
- npm or yarn

### Running Development Servers

You can start both frontend and backend servers with a single command:

```bash
npm run dev:all
```

Or run them separately:

1. Frontend Development Server (Hot-reload enabled)
```bash
npm run dev
```

2. Backend Development Server
```bash
npm run dev:backend
```

The frontend will be available at `http://localhost:5173` and will proxy API requests to the backend at `http://localhost:8000`.

## Production

To deploy the application in production:

```bash
npm run start
```

This will:
1. Build the frontend assets (`npm run build`)
2. Start the backend server using gunicorn

### Production URLs
- Frontend: Served through the backend at `http://localhost:8000`
- API: `http://localhost:8000/api`

## Configuration

### Frontend (Vite)
- Development proxy is configured to forward `/api` requests to the backend
- Static files are built to `./dist` directory
- Aliases configured: `@` points to `./src`

### Backend
- Development: Uses uvicorn with hot-reload
- Production: Uses gunicorn for better performance and process management



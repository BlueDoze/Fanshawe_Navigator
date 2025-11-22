# React Frontend Setup Guide

## Prerequisites

You need to install Node.js to run the React frontend.

### Install Node.js

1. Download Node.js from: https://nodejs.org/
2. Install the LTS (Long Term Support) version
3. Verify installation by opening a new PowerShell and running:
   ```powershell
   node --version
   npm --version
   ```

## Setup Instructions

### 1. Install Dependencies

Open PowerShell in the `frontend` directory and run:

```powershell
npm install
```

This will install all required packages:
- React and React DOM
- Leaflet and React-Leaflet (for maps)
- Tailwind CSS (for styling)
- Vite (for development server)
- Lucide React (for icons)

### 2. Start the Development Server

```powershell
npm run dev
```

The React app will start on `http://localhost:5173` (Vite default port)

### 3. Start the Backend

In a separate terminal, navigate to the backend directory:

```powershell
cd ..\backend
uvicorn api:app --reload --port 8000
```

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx              # Main application component
│   ├── main.jsx             # React entry point
│   ├── index.css            # Global styles with Tailwind
│   └── components/          # Reusable components
├── index.html               # HTML entry point
├── package.json             # Dependencies and scripts
├── tailwind.config.js       # Tailwind configuration
├── vite.config.js           # Vite configuration
└── postcss.config.js        # PostCSS configuration
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## Features

### Chat Interface
- Send messages to the Fanshawe Navigator chatbot
- Get navigation directions between buildings
- Request information about specific buildings
- View conversation history

### Interactive Map
- Click "Show Map" to view the campus map
- Click on buildings to see detailed information
- Visual route highlighting (green = origin, red = destination)
- Integrated with OpenStreetMap tiles

### Color Scheme
The app uses Fanshawe College branding colors:
- `#161917` - Dark background
- `#b9030f` - Fanshawe red (primary)
- `#9e0004` - Dark red
- `#70160e` - Darker red
- `#e1e3db` - Cream (text)

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`

### Endpoints Used:
- `POST /api/chat` - Send chat messages
- `GET /api/geojson` - Load campus building data
- `GET /api/predios/{ref}/info` - Get building information
- `POST /api/calcular-rota` - Calculate routes between buildings

## Troubleshooting

### Port Already in Use
If port 5173 is busy, Vite will automatically use the next available port.

### CORS Issues
Make sure the backend API has CORS enabled for `http://localhost:5173`

### Map Not Loading
- Check internet connection (OpenStreetMap tiles require internet)
- Verify backend is running and `/api/geojson` endpoint works

### Styling Issues
If Tailwind styles aren't applying:
```powershell
npm run build
```

## Old Vanilla JS Version

The previous vanilla JavaScript version has been backed up as:
- `index_vanilla.html.bak`

You can switch back by renaming files if needed.

## Production Build

To build for production:

```powershell
npm run build
```

This creates a `dist/` folder with optimized static files that can be:
- Served by any web server (nginx, Apache, etc.)
- Deployed to Vercel, Netlify, GitHub Pages, etc.
- Served by the Python backend using static file serving

To preview the production build:
```powershell
npm run preview
```

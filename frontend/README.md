# Spotter AI - Frontend

Production-grade fuel routing optimization frontend built with Next.js 14, React 18, TypeScript, and Leaflet.

## Features

- **Interactive Route Visualization** - Beautiful map showing routes and fuel stops
- **Smart Route Planning** - Form with popular routes and advanced vehicle options
- **Real-time Fuel Stop Details** - Comprehensive information about each fuel stop
- **Polyline Decoding** - Decode and visualize encoded route geometry
- **Beautiful UI** - Modern design with Tailwind CSS
- **Type-Safe** - Full TypeScript support
- **Production-Ready** - Optimized for performance and reliability

## Tech Stack

- **Next.js 14** - React framework with App Router
- **React 18** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Leaflet** - Interactive maps
- **Axios** - HTTP client
- **Lucide React** - Beautiful icons

## Quick Start

### Prerequisites

- Node.js 18+ installed
- Backend server running at `http://127.0.0.1:8000/`

### Installation

1. **Navigate to frontend directory:**
   ```bash
   cd "r:\Spotter AI\frontend"
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   ```
   http://localhost:3000
   ```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Main application page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── RouteMap.tsx      # Interactive map component
│   ├── RoutePlannerForm.tsx  # Route planning form
│   └── FuelStopsList.tsx # Fuel stops display
├── lib/                   # Utilities and services
│   ├── api.ts            # API service with type-safe endpoints
│   └── polyline.ts       # Polyline encoding/decoding utilities
├── public/               # Static assets
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── tailwind.config.js    # Tailwind config
└── next.config.js        # Next.js config
```

## Available Scripts

- `npm run dev` - Start development server (http://localhost:3000)
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Features Guide

### Route Planning

1. Enter start and end locations (e.g., "Los Angeles, CA")
2. Optionally adjust vehicle MPG and range in advanced options
3. Click "Plan Route" or select a popular route
4. View route on map with fuel stops marked

### Interactive Map

- **Green marker (A)** - Start location
- **Red marker (B)** - End location
- **Orange markers** - Fuel stops
- **Blue line** - Optimized route
- Click markers for details

### Fuel Stops Information

Each fuel stop displays:
- Station name and location
- Fuel price per gallon
- Gallons needed
- Total cost
- Distance from start

## API Integration

The frontend communicates with the backend API at:
```
http://127.0.0.1:8000/api/v1
```

### Endpoints Used:

- `POST /plan/` - Plan route with fuel stops
- `GET /health/` - Check API health
- `GET /stations/` - List fuel stations
- `GET /stations/cheapest/` - Get cheapest stations

### Configuring API URL

Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
```

## Polyline Decoding

The app uses Google's polyline encoding format for efficient route transmission:

```typescript
import { decodePolyline } from '@/lib/polyline';

const coordinates = decodePolyline(encodedPolyline);
// Returns: [{lat: 34.0522, lng: -118.2437}, ...]
```

## Styling

### Tailwind CSS

The app uses Tailwind CSS with a custom color palette:

```javascript
colors: {
  primary: {
    500: '#0ea5e9',  // Main brand color
    600: '#0284c7',  // Hover states
    700: '#0369a1',  // Active states
  }
}
```

### Custom Animations

- Fade-in animations for route results
- Smooth hover transitions
- Loading spinners

## Production Build

1. **Build the application:**
   ```bash
   npm run build
   ```

2. **Start production server:**
   ```bash
   npm start
   ```

3. **Deploy to hosting:**
   - Vercel (recommended)
   - Netlify
   - Any Node.js hosting

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- **First Load** - 2-5 seconds (external API calls)
- **Cached Routes** - < 100ms
- **Map Rendering** - < 500ms
- **Page Load** - < 1 second

## Troubleshooting

### Issue: "Unable to connect to the server"

**Solution:** Ensure backend is running:
```bash
cd "r:\Spotter AI"
python manage.py runserver
```

### Issue: Map not displaying

**Solution:** Check browser console for errors. Ensure Leaflet CSS is loaded.

### Issue: "Module not found"

**Solution:** Reinstall dependencies:
```bash
rm -rf node_modules package-lock.json
npm install
```

## Environment Variables

Create `.env.local` file:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
```

## Development Tips

1. **Hot Reload** - Changes auto-refresh in dev mode
2. **TypeScript** - Use VS Code for best TypeScript experience
3. **Component Dev** - Test components in isolation
4. **API Testing** - Use browser DevTools Network tab

## License

Part of the Spotter AI Fuel Routing Optimization System.

## Support

For issues or questions:
1. Check backend server is running
2. Verify API URL in `.env.local`
3. Check browser console for errors
4. Review backend logs at `logs/spotter_ai.log`

---

**Built with Next.js, React, TypeScript, and Leaflet** | Production-Grade Fuel Routing Optimization

# Surveillance AI Frontend

A modern React + Vite frontend application for the Surveillance AI platform, providing an intuitive interface for video analysis, real-time monitoring, and detection management.

## 🚀 Quick Start

### Prerequisites
- **Node.js 18+**
- **npm** or **yarn**

### Installation
```bash
# Install dependencies
npm ci

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

## 🌐 Development URLs
- **Local Development**: http://localhost:8080
- **Backend API**: http://127.0.0.1:8000 (configured in .env)

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Route-based page components
│   ├── context/       # React context providers
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utility functions and API client
│   └── main.tsx       # Application entry point
├── public/            # Static assets
├── .env.example       # Environment variables template
└── package.json       # Dependencies and scripts
```

## 🎨 Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Shadcn/ui** - Component library
- **React Router** - Client-side routing
- **Zustand** - State management

## 📱 Features

- **Video Upload & Analysis** - Drag-and-drop video upload with real-time progress
- **Detection Results** - Interactive results viewer with preview clips
- **Live Monitoring** - Real-time detection alerts and filtering
- **Configuration** - Adjustable detection parameters and thresholds
- **Responsive Design** - Mobile-friendly interface

## 🔧 Environment Variables

Create a `.env` file based on `.env.example`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 📦 Available Scripts

```bash
# Development
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build

# Code Quality
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking
```

## 🔗 Integration

The frontend integrates with the Surveillance AI backend via:
- **REST API** for video analysis and configuration
- **WebSocket** for real-time detection alerts
- **Static file serving** for preview clips and results

## 🎯 Key Components

- **LazyVideo** - Optimized video player with lazy loading
- **DevPanel** - Development tools and debugging
- **LiveStore** - Real-time state management
- **UploadContext** - File upload handling

## 🚀 Deployment

```bash
# Build for production
npm run build

# The dist/ folder contains the production build
# Serve with any static file server
```

---

*Part of the Surveillance AI Platform - Intelligent Video Analysis System*
# Surveillance AI Resume Docs - Chunk 3/6

## Question:
Document the complete frontend user experience and architecture.

Include:
- Screens and flows: Home, M1–M4 (Manual Upload), L1–L4 (Live Feed Analytics)
- Frontend–backend communication (API routes, progress tracking, JSON parsing)
- Libraries used (React, TypeScript, Tailwind, Framer Motion, etc.)
- Timeline visualization and video preview implementation (5–10s clips)

## Answer:

### Frontend Architecture Overview

The Surveillance AI frontend is a modern, responsive React application built with TypeScript, featuring an intuitive user interface for video analysis, real-time monitoring, and detection management. The application follows a component-based architecture with sophisticated state management and seamless backend integration.

### Complete User Experience Flow

#### 1. Landing Experience
**Landing3D Page (`/`)**
- **Purpose**: 3D animated introduction with WebGL/Three.js integration
- **Features**: 
  - Interactive 3D hero section with fallback to static content
  - Accessibility support (reduced motion, high contrast mode)
  - Auto-navigation to upload after 3.5s or user interaction
  - Skip functionality with 1.5s delay
- **Technology**: React Three Fiber, Three.js, WebGL detection
- **UX**: Smooth onboarding with visual appeal

#### 2. Manual Upload Flow (M1-M4)

**M1: Upload Page (`/upload`)**
- **Purpose**: Video file selection and upload interface
- **Features**:
  - Drag-and-drop file upload with validation
  - YouTube URL integration with format selection
  - Analysis time window selection (VideoRangeSelector)
  - Prompt input with chip-based interface
  - Real-time upload progress tracking
- **Components**: `UrlIngestForm`, `PromptChipsInput`, `VideoRangeSelector`

**M2: Configure Page (`/configure`)**
- **Purpose**: Analysis mode and parameter configuration
- **Features**:
  - 5 Analysis modes: FullScan, FrameSkip, MotionFilter, TrackThenMatch, ActivityDetect
  - Model selection (CLIP ViT-B/32)
  - Advanced parameter tuning
  - Real-time configuration preview
- **Modes**:
  - **FullScan**: Deep frame-by-frame analysis
  - **FrameSkip**: Optimized performance with frame sampling
  - **MotionFilter**: Motion-based detection
  - **TrackThenMatch**: Object tracking + semantic matching
  - **ActivityDetect**: Suspicious behavior detection

**M3: Progress Page (`/progress`)**
- **Purpose**: Real-time analysis progress monitoring
- **Features**:
  - Live progress updates with percentage and ETA
  - Status polling with error handling
  - Automatic navigation to results on completion
  - Timeout handling and retry mechanisms
- **API Integration**: `/status` endpoint with job ID tracking

**M4: Results Page (`/results`)**
- **Purpose**: Interactive results visualization and management
- **Features**:
  - Timeline visualization with zoom controls
  - Video preview clips (5-10 seconds)
  - Detection filtering and categorization
  - Re-analysis capabilities with new prompts
  - Export functionality for clips and data
  - Runs history panel for analysis comparison

#### 3. Live Feed Analytics Flow (L1-L4)

**L1: Live Dashboard (`/live`)**
- **Purpose**: Real-time monitoring dashboard
- **Features**:
  - Live camera feeds integration
  - Real-time detection alerts
  - WebSocket connection management
  - Connection status indicators
- **Technology**: WebSocket client with heartbeat and reconnection

**L2: Live Alerts (`/live/alerts`)**
- **Purpose**: Alert management and filtering
- **Features**:
  - Virtualized alert list for performance
  - Advanced filtering (category, confidence, time range)
  - Search functionality across alert content
  - Bulk operations (acknowledge, pin, export)
- **Performance**: Virtual scrolling for large datasets

**L3: Live Filters (`/live/filters`)**
- **Purpose**: Advanced filtering configuration
- **Features**:
  - Category-based filtering
  - Confidence threshold adjustment
  - Time-based filtering
  - Camera-specific settings
- **Persistence**: Filter settings saved to localStorage

**L4: Live Review (`/live/review/:id`)**
- **Purpose**: Individual alert review and analysis
- **Features**:
  - Full-screen video player with controls
  - Alert metadata display
  - Export functionality
  - Note-taking capabilities
- **Components**: `VideoWithVisibility`, export progress tracking

### Frontend-Backend Communication

#### 1. API Architecture (`lib/api.ts`)
**Centralized API Client:**
- **Base URL Management**: Environment-based configuration
- **Request Wrapper**: Robust error handling and timeout management
- **Type Safety**: TypeScript interfaces for all API responses
- **Cache Busting**: Timestamp-based URL parameters

**Key API Endpoints:**
```typescript
// Analysis endpoints
getStatus: (jobId: string) => JobStatus
getResults: (jobId: string) => AnalysisResponse
postExportClips: (jobId: string) => ExportStart

// Live monitoring endpoints
getLiveAlerts: (cameraId: string, since?: number) => Alert[]
postLiveAck: (alertId: string, acknowledged: boolean) => boolean
postLivePin: (alertId: string, pinned: boolean) => boolean
postLiveNote: (alertId: string, note: string) => boolean
postLiveExport: (alertId: string) => ExportResponse
```

#### 2. Progress Tracking System
**Real-time Status Updates:**
- **Polling Mechanism**: 1.2-second intervals during analysis
- **Status Types**: `queued`, `processing`, `complete`, `error`
- **Progress Metrics**: Percentage completion, ETA calculation
- **Error Handling**: Timeout detection, retry logic, graceful degradation

**WebSocket Integration:**
- **Live Monitoring**: Real-time alert streaming
- **Connection Management**: Heartbeat, reconnection, fallback to REST
- **State Synchronization**: Optimistic updates with server confirmation

#### 3. JSON Response Processing
**Structured Data Handling:**
```typescript
type AnalysisResponse = {
  status: string;
  video_id: string;
  results: ResultEntry[];
  alert_summary?: Record<string, number>;
  analysis_timestamp?: string;
  json_path?: string;
  prompts?: string[];
  analysisWindow?: {
    start: string;
    end: string;
    offsetSeconds: number;
  };
  previewSets?: {
    merged?: Array<{
      label: string;
      start: string;
      end: string;
      duration: number;
      confidence_peak: number;
      url: string;
    }>;
  };
};
```

### Technology Stack & Libraries

#### 1. Core Framework
- **React 18**: Modern functional components with hooks
- **TypeScript 5.8**: Full type safety and enhanced developer experience
- **Vite 5.4**: Fast build tool and development server
- **React Router 6**: Client-side routing with nested routes

#### 2. UI & Styling
- **Tailwind CSS 3.4**: Utility-first CSS framework
- **Shadcn/ui**: Modern component library with Radix UI primitives
- **Radix UI**: Accessible, unstyled UI primitives
- **Lucide React**: Comprehensive icon library
- **Framer Motion**: Animation library (planned integration)

#### 3. State Management
- **React Context**: Global state management (`UploadContext`, `LiveProvider`)
- **Zustand**: Lightweight state management for complex interactions
- **React Query**: Server state management and caching
- **localStorage**: Client-side persistence for user preferences

#### 4. Advanced Features
- **React Three Fiber**: 3D graphics and WebGL integration
- **Three.js**: 3D library for landing page animations
- **React Virtual**: Virtual scrolling for performance optimization
- **React Hook Form**: Form handling with validation
- **Zod**: Schema validation for type safety

#### 5. Development Tools
- **ESLint**: Code linting and quality assurance
- **TypeScript ESLint**: TypeScript-specific linting rules
- **Vite Plugins**: React SWC for fast compilation
- **PostCSS**: CSS processing with Autoprefixer

### Timeline Visualization & Video Preview

#### 1. Timeline Implementation
**Interactive Timeline Component:**
- **Zoom Controls**: Multiple zoom levels for detailed analysis
- **Time Navigation**: Click-to-seek functionality
- **Visual Indicators**: Color-coded detection markers
- **Responsive Design**: Adaptive layout for different screen sizes

**Timeline Features:**
```typescript
// Timeline item rendering with virtual scrolling
{timelineItems.map((item, idx) => {
  if (item.type === 'detection') {
    return (
      <Tooltip>
        <TooltipTrigger>
          <LazyVideo
            src={item.preview_clip}
            previewClipMp4={item.preview_clip_mp4}
            previewClipWebm={item.preview_clip_webm}
            muted
            playsInline
            preload="none"
            autoPlay
            loop
            className="w-full h-28 object-cover"
          />
        </TooltipTrigger>
        <TooltipContent>
          {/* Detection metadata and labels */}
        </TooltipContent>
      </Tooltip>
    );
  }
})}
```

#### 2. Video Preview System
**LazyVideo Component:**
- **Lazy Loading**: Intersection Observer for performance
- **Format Support**: MP4/WebM with automatic fallback
- **Cache Busting**: Timestamp-based URL parameters
- **Performance Optimization**: Pause when offscreen, preload management

**Preview Features:**
- **5-10 Second Clips**: Optimized duration for analysis
- **Multiple Formats**: MP4 primary, WebM fallback
- **Thumbnail Generation**: Automatic poster frames
- **Hover Previews**: Instant preview on timeline hover
- **Export Functionality**: Download individual clips

#### 3. Virtual Scrolling Implementation
**Performance Optimization:**
- **Virtualized Lists**: Handle thousands of detections efficiently
- **Dynamic Height**: Adaptive row heights for different content
- **Memory Management**: Automatic cleanup of offscreen elements
- **Smooth Scrolling**: Native browser scrolling with virtual positioning

### Advanced UX Features

#### 1. Accessibility
- **Keyboard Navigation**: Full keyboard support for all interactions
- **Screen Reader Support**: ARIA labels and semantic HTML
- **High Contrast Mode**: Toggle with Alt+H shortcut
- **Reduced Motion**: Respects user motion preferences

#### 2. Performance Optimizations
- **Code Splitting**: Route-based lazy loading
- **Image Optimization**: Lazy loading with intersection observer
- **Bundle Optimization**: Tree shaking and dead code elimination
- **Caching Strategy**: Intelligent cache management for API responses

#### 3. Error Handling
- **Error Boundaries**: Graceful error recovery
- **Network Resilience**: Automatic retry with exponential backoff
- **Fallback UI**: Graceful degradation for failed components
- **User Feedback**: Clear error messages and recovery options

#### 4. Developer Experience
- **Hot Reload**: Instant development feedback
- **Type Safety**: Comprehensive TypeScript coverage
- **Debug Tools**: Development panel with connection status
- **Code Quality**: ESLint integration with React-specific rules

### Integration Architecture

#### 1. Backend Communication
- **REST API**: Comprehensive endpoint coverage
- **WebSocket**: Real-time live monitoring
- **File Upload**: Multipart form data with progress tracking
- **Static Assets**: Optimized media serving with CORS

#### 2. State Management Flow
```
User Action → Context Update → API Call → Response Processing → UI Update
```

#### 3. Data Flow Architecture
- **Upload Flow**: File → Validation → Upload → Analysis → Results
- **Live Flow**: WebSocket → Alert Processing → UI Update → User Action
- **Re-analysis**: Existing Media → New Prompts → Analysis → Updated Results

This frontend architecture demonstrates advanced React development skills, modern web technologies, and sophisticated user experience design, making it an excellent showcase for technical resumes and portfolio presentations.

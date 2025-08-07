
export interface UploadedVideo {
  file: File;
  url: string;
  duration: number;
  size: number;
}

export interface AnalysisPrompt {
  text: string;
  model: 'chatgpt' | 'vertex';
  mode: 'basic' | 'advanced';
  confidence?: number;
}

export interface DetectionMatch {
  id: string;
  timestamp: number;
  thumbnailUrl: string;
  clipUrl: string;
  confidence: number;
  description: string;
}

export interface AnalysisSession {
  id: string;
  prompt: string;
  timestamp: Date;
  matchCount: number;
  model: string;
  mode: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  matches: DetectionMatch[];
}

export interface ProcessingStatus {
  stage: 'analyzing' | 'matching' | 'generating' | 'completed';
  progress: number;
  message: string;
  timeline: TimelineSegment[];
}

export interface TimelineSegment {
  start: number;
  end: number;
  hasMatch: boolean;
  confidence?: number;
}

export interface ExportSettings {
  includeMetadata: boolean;
  format: 'zip' | 'csv' | 'pdf';
  videoFormat: 'mp4' | 'avi' | 'mov';
}

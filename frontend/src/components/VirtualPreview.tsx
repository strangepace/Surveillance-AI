import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { parseHMS, formatHMS } from '@/lib/time';

interface VirtualPreviewProps {
  src: string;
  start: number; // start time in seconds
  end: number;   // end time in seconds
  label?: string;
  className?: string;
}

export const VirtualPreview: React.FC<VirtualPreviewProps> = ({
  src,
  start,
  end,
  label,
  className = ""
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [poster, setPoster] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [duration, setDuration] = useState<number>(0);

  // Calculate clip duration
  const clipDuration = end - start;

  // Generate poster image at start time
  const generatePoster = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx) return;

    try {
      // Set video to start time
      video.currentTime = start;
      
      // Wait for seek to complete
      await new Promise((resolve) => {
        const onSeeked = () => {
          video.removeEventListener('seeked', onSeeked);
          resolve(void 0);
        };
        video.addEventListener('seeked', onSeeked);
      });

      // Draw frame to canvas
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      // Convert to data URL
      const posterUrl = canvas.toDataURL('image/jpeg', 0.8);
      setPoster(posterUrl);
    } catch (err) {
      console.warn('Failed to generate poster:', err);
    }
  }, [start]);

  // Handle video loaded metadata
  const handleLoadedMetadata = useCallback(() => {
    if (!videoRef.current) return;
    
    const video = videoRef.current;
    setDuration(video.duration);
    
    // Generate poster after metadata is loaded
    generatePoster();
  }, [generatePoster]);

  // Handle time updates to auto-pause at end
  const handleTimeUpdate = useCallback(() => {
    if (!videoRef.current) return;
    
    const video = videoRef.current;
    const currentTime = video.currentTime;
    
    // Check if we've reached the end (with small buffer)
    if (currentTime >= end - 0.05) {
      video.pause();
      setIsPlaying(false);
      setIsPaused(true);
    }
  }, [end]);

  // Handle play/pause
  const handlePlayPause = useCallback(() => {
    if (!videoRef.current) return;
    
    const video = videoRef.current;
    
    if (video.paused) {
      // If paused at end, restart from beginning
      if (isPaused) {
        video.currentTime = start;
        setIsPaused(false);
      }
      video.play();
      setIsPlaying(true);
    } else {
      video.pause();
      setIsPlaying(false);
    }
  }, [start, isPaused]);

  // Handle replay
  const handleReplay = useCallback(() => {
    if (!videoRef.current) return;
    
    const video = videoRef.current;
    video.currentTime = start;
    video.play();
    setIsPlaying(true);
    setIsPaused(false);
  }, [start]);

  // Handle video errors
  const handleError = useCallback(() => {
    setError('Failed to load video');
  }, []);

  // Set up video element
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Add event listeners
    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('error', handleError);

    return () => {
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('error', handleError);
    };
  }, [handleLoadedMetadata, handleTimeUpdate, handleError]);

  // Build video source with time fragment (if supported)
  const videoSrc = `${src}#t=${start},${end}`;

  return (
    <Card className={`relative transition-all duration-300 hover:-translate-y-1 hover:shadow-lg ${className}`}>
      <CardContent className="p-0">
        <div className="relative">
          {/* Video element */}
          <video
            ref={videoRef}
            src={videoSrc}
            poster={poster || undefined}
            className="w-full h-48 object-cover rounded-t-lg"
            preload="metadata"
            playsInline
            muted
          />
          
          {/* Hidden canvas for poster generation */}
          <canvas ref={canvasRef} className="hidden" />
          
          {/* Overlay controls */}
          <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center">
            <div className="opacity-0 hover:opacity-100 transition-opacity duration-200">
              {isPaused ? (
                <Button
                  onClick={handleReplay}
                  size="lg"
                  className="rounded-full w-16 h-16"
                  variant="secondary"
                >
                  <RotateCcw className="w-6 h-6" />
                </Button>
              ) : (
                <Button
                  onClick={handlePlayPause}
                  size="lg"
                  className="rounded-full w-16 h-16"
                  variant="secondary"
                >
                  {isPlaying ? (
                    <Pause className="w-6 h-6" />
                  ) : (
                    <Play className="w-6 h-6" />
                  )}
                </Button>
              )}
            </div>
          </div>
          
          {/* Error overlay */}
          {error && (
            <div className="absolute inset-0 bg-red-500 bg-opacity-80 flex items-center justify-center rounded-t-lg">
              <p className="text-white text-sm font-medium">{error}</p>
            </div>
          )}
        </div>
        
        {/* Clip info */}
        <div className="p-3 space-y-2">
          {label && (
            <Badge variant="secondary" className="text-xs">
              {label}
            </Badge>
          )}
          <div className="text-xs text-muted-foreground space-y-1">
            <div>Start: {formatHMS(start)}</div>
            <div>End: {formatHMS(end)}</div>
            <div>Duration: {clipDuration.toFixed(1)}s</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default VirtualPreview;

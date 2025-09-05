import React from "react";

type LazyVideoProps = React.VideoHTMLAttributes<HTMLVideoElement> & {
  placeholderHeight?: number;
  pauseOffscreen?: boolean; // when true, pauses when out of view
  jobId?: string; // for cache busting
  frameIndex?: number; // for cache busting
  previewClipMp4?: string; // MP4 preview URL
  previewClipWebm?: string; // WebM preview URL (fallback)
};

const LazyVideo: React.FC<LazyVideoProps> = ({ 
  placeholderHeight = 160, 
  src, 
  pauseOffscreen = true, 
  autoPlay, 
  muted, 
  jobId,
  frameIndex,
  previewClipMp4,
  previewClipWebm,
  ...props 
}) => {
  const wrapperRef = React.useRef<HTMLDivElement | null>(null);
  const videoRef = React.useRef<HTMLVideoElement | null>(null);
  const [visible, setVisible] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(true);
  const [hasError, setHasError] = React.useState(false);
  const [isPlaying, setIsPlaying] = React.useState(false);

  // Generate cache-busting URLs for both formats
  const bust = Date.now();
  const mp4 = previewClipMp4 ? `${previewClipMp4}${previewClipMp4.includes("?") ? "&" : "?"}_v=${bust}` : "";
  const webm = previewClipWebm ? `${previewClipWebm}${previewClipWebm.includes("?") ? "&" : "?"}_v=${bust}` : "";
  
  // Use the best available source
  const videoSrc = mp4 || webm || src;
  const hasMultipleSources = mp4 && webm;

  // Intersection Observer for lazy loading
  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );

    if (wrapperRef.current) {
      observer.observe(wrapperRef.current);
    }

    return () => observer.disconnect();
  }, []);

  // Pause when out of view
  React.useEffect(() => {
    if (!pauseOffscreen || !videoRef.current) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting && isPlaying) {
          videoRef.current?.pause();
          setIsPlaying(false);
        }
      },
      { threshold: 0.1 }
    );

    if (wrapperRef.current) {
      observer.observe(wrapperRef.current);
    }

    return () => observer.disconnect();
  }, [pauseOffscreen, isPlaying]);

  // Handle video events
  const handleLoadedMetadata = () => {
    setIsLoading(false);
    setHasError(false);
    console.log("Video loaded successfully:", videoSrc);
  };

  const handleError = (e: React.SyntheticEvent<HTMLVideoElement, Event>) => {
    setIsLoading(false);
    setHasError(true);
    console.error("Video error:", videoSrc, e);
  };

  const handlePlay = () => setIsPlaying(true);
  const handlePause = () => setIsPlaying(false);

  if (!visible) {
    return (
      <div 
        ref={wrapperRef}
        className="bg-gray-200 animate-pulse rounded"
        style={{ height: placeholderHeight }}
      />
    );
  }

  return (
    <div ref={wrapperRef} className="relative">
      {isLoading && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse rounded flex items-center justify-center">
          <div className="text-gray-500 text-sm">Loading...</div>
        </div>
      )}
      
      {hasError && (
        <div className="absolute inset-0 bg-red-100 border border-red-300 rounded flex items-center justify-center">
          <div className="text-red-500 text-sm">Video failed to load</div>
        </div>
      )}
      
      <video
        ref={videoRef}
        key={`${jobId || "unknown"}-${frameIndex || 0}-${bust}`}
        className="w-full h-auto rounded"
        controls
        preload="metadata"
        playsInline
        muted={muted}
        autoPlay={autoPlay}
        onLoadedMetadata={handleLoadedMetadata}
        onError={handleError}
        onPlay={handlePlay}
        onPause={handlePause}
        {...props}
      >
        {/* Dual source support with MP4 priority */}
        {mp4 && <source src={mp4} type="video/mp4" />}
        {webm && <source src={webm} type="video/webm" />}
        {!mp4 && !webm && src && <source src={src} type="video/mp4" />}
        
        {/* Fallback text */}
        Your browser does not support the video tag.
      </video>
      
      {/* Debug info in development */}
      {process.env.NODE_ENV === 'development' && (
        <div className="text-xs text-gray-500 mt-1">
          {hasMultipleSources ? `MP4 + WebM (${mp4 ? '✅' : '❌'}/${webm ? '✅' : '❌'})` : 'Single source'}
        </div>
      )}
    </div>
  );
};

export default LazyVideo;

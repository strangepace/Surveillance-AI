import React from "react";

type LazyVideoProps = React.VideoHTMLAttributes<HTMLVideoElement> & {
  placeholderHeight?: number;
  pauseOffscreen?: boolean; // when true, pauses when out of view
};

const LazyVideo: React.FC<LazyVideoProps> = ({ placeholderHeight = 160, src, pauseOffscreen = true, autoPlay, muted, ...props }) => {
  const wrapperRef = React.useRef<HTMLDivElement | null>(null);
  const videoRef = React.useRef<HTMLVideoElement | null>(null);
  const [visible, setVisible] = React.useState(false);

  React.useEffect(() => {
    const el = wrapperRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          const inView = e.isIntersecting || e.intersectionRatio > 0;
          if (inView) setVisible(true);
          if (pauseOffscreen && videoRef.current) {
            if (!inView) {
              try { videoRef.current.pause(); } catch {}
            } else if (autoPlay) {
              try { videoRef.current.play(); } catch {}
            }
          }
        });
      },
      { rootMargin: "200px", threshold: [0, 0.01, 0.5, 1] }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [pauseOffscreen, autoPlay]);

  return (
    <div ref={wrapperRef} className="w-full">
      {visible ? (
        <video ref={videoRef} src={src} autoPlay={autoPlay} muted={muted} {...props} />
      ) : (
        <div
          className="w-full bg-muted animate-pulse"
          style={{ height: placeholderHeight }}
          aria-hidden
        />
      )}
    </div>
  );
};

export default LazyVideo;

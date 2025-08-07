
import React from 'react';
import { Eye, Camera, Signal } from 'lucide-react';

interface LiveVideoFeedProps {
  isMuted: boolean;
}

const LiveVideoFeed: React.FC<LiveVideoFeedProps> = ({ isMuted }) => {
  return (
    <div className="h-full bg-black/50 border border-cyan-500/30 rounded-lg overflow-hidden backdrop-blur-lg">
      {/* HUD Header */}
      <div className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border-b border-cyan-500/30 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Camera className="w-6 h-6 text-cyan-400" />
            <div>
              <h3 className="text-white font-mono text-lg">CAM-01</h3>
              <p className="text-cyan-400 text-sm">Main Entrance - Sector 7</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Signal className="w-4 h-4 text-green-400" />
              <span className="text-green-400 text-sm font-mono">STRONG</span>
            </div>
            <div className="text-cyan-400 font-mono text-sm">
              {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* Video Feed */}
      <div className="relative h-[calc(100%-80px)] bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
        {/* Simulated Video Feed */}
        <div className="w-full h-full bg-black/30 flex items-center justify-center relative overflow-hidden">
          {/* Grid Overlay */}
          <div className="absolute inset-0 opacity-20">
            <div className="grid grid-cols-8 grid-rows-6 h-full w-full">
              {Array.from({ length: 48 }).map((_, i) => (
                <div key={i} className="border border-cyan-500/20" />
              ))}
            </div>
          </div>

          {/* Center Crosshair */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="relative">
              <div className="w-8 h-8 border-2 border-cyan-400 rounded-full opacity-50" />
              <div className="absolute inset-2 w-4 h-4 border border-cyan-400 rounded-full animate-pulse" />
            </div>
          </div>

          {/* Video Placeholder */}
          <div className="text-center text-cyan-400">
            <Eye className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-mono">LIVE FEED ACTIVE</p>
            <p className="text-sm opacity-70">1920x1080 • 30 FPS</p>
          </div>

          {/* Audio Status */}
          {isMuted && (
            <div className="absolute top-4 left-4 bg-red-500/20 border border-red-500/50 rounded px-3 py-1">
              <span className="text-red-400 text-sm font-mono">AUDIO MUTED</span>
            </div>
          )}

          {/* Recording Status */}
          <div className="absolute top-4 right-4 flex items-center gap-2 bg-red-500/20 border border-red-500/50 rounded px-3 py-1">
            <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse" />
            <span className="text-red-400 text-sm font-mono">REC</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveVideoFeed;

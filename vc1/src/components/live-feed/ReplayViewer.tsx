
import React, { useState } from 'react';
import { ArrowLeft, Play, Pause, SkipBack, SkipForward, Tag, AlertTriangle, CheckCircle, Flag } from 'lucide-react';
import { Alert } from '@/types/live-feed';

interface ReplayViewerProps {
  alert: Alert | null;
  onBack: () => void;
}

const ReplayViewer: React.FC<ReplayViewerProps> = ({ alert, onBack }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration] = useState(15); // 15-second clips
  const [tag, setTag] = useState<string>('');

  if (!alert) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <p className="font-mono">No alert selected</p>
      </div>
    );
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStatusUpdate = (status: 'reviewed' | 'escalated' | 'false-alarm') => {
    console.log(`Alert ${alert.id} marked as: ${status}`);
  };

  const handleExportCase = () => {
    console.log(`Exporting case file for alert ${alert.id}`);
  };

  return (
    <div className="h-full grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Mini Live Feed */}
      <div className="lg:col-span-1 bg-black/50 border border-cyan-500/30 rounded-lg backdrop-blur-lg overflow-hidden">
        <div className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border-b border-cyan-500/30 p-3">
          <h3 className="text-white font-mono text-sm">LIVE FEED</h3>
        </div>
        <div className="h-[calc(100%-50px)] bg-gray-900 flex items-center justify-center relative">
          <div className="text-center text-cyan-400">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse mx-auto mb-2" />
            <p className="text-xs font-mono">LIVE</p>
          </div>
          <div className="absolute inset-2 border border-cyan-500/20 rounded" />
        </div>
      </div>

      {/* Replay Player */}
      <div className="lg:col-span-3 bg-black/50 border border-orange-500/30 rounded-lg backdrop-blur-lg overflow-hidden">
        {/* Player Header */}
        <div className="bg-gradient-to-r from-orange-500/10 to-red-500/10 border-b border-orange-500/30 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={onBack}
                className="p-2 text-orange-400 hover:text-orange-300 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h3 className="text-white font-mono text-lg">EVENT REPLAY</h3>
                <p className="text-orange-400 text-sm">{alert.id} - {alert.type}</p>
              </div>
            </div>
            
            <div className={`px-3 py-1 rounded text-sm font-mono border ${
              alert.severity === 'critical'
                ? 'bg-red-500/20 text-red-400 border-red-500/30'
                : 'bg-green-500/20 text-green-400 border-green-500/30'
            }`}>
              {alert.severity.toUpperCase()}
            </div>
          </div>
        </div>

        {/* Video Player */}
        <div className="h-80 bg-gray-900 relative flex items-center justify-center">
          {/* Video placeholder */}
          <div className="text-center text-orange-400">
            <AlertTriangle className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-mono">ALERT CLIP</p>
            <p className="text-sm opacity-70">{alert.timestamp.toLocaleString()}</p>
          </div>

          {/* Play/Pause Overlay */}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="absolute inset-0 flex items-center justify-center bg-black/20 hover:bg-black/40 transition-colors"
          >
            {isPlaying ? (
              <Pause className="w-16 h-16 text-white opacity-70" />
            ) : (
              <Play className="w-16 h-16 text-white opacity-70" />
            )}
          </button>

          {/* Timeline */}
          <div className="absolute bottom-4 left-4 right-4">
            <div className="flex items-center gap-3">
              <span className="text-white font-mono text-sm">{formatTime(currentTime)}</span>
              <div className="flex-1 bg-gray-700 h-1 rounded-full">
                <div 
                  className="bg-orange-400 h-full rounded-full transition-all"
                  style={{ width: `${(currentTime / duration) * 100}%` }}
                />
              </div>
              <span className="text-white font-mono text-sm">{formatTime(duration)}</span>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="border-t border-orange-500/30 p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <button className="p-2 text-orange-400 hover:text-orange-300 transition-colors">
                <SkipBack className="w-5 h-5" />
              </button>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-3 bg-orange-500/20 border border-orange-500/30 rounded-lg text-orange-400 hover:bg-orange-500/30 transition-colors"
              >
                {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
              </button>
              <button className="p-2 text-orange-400 hover:text-orange-300 transition-colors">
                <SkipForward className="w-5 h-5" />
              </button>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="text"
                value={tag}
                onChange={(e) => setTag(e.target.value)}
                placeholder="Add tag..."
                className="px-3 py-1 bg-gray-800/50 border border-orange-500/30 rounded text-white placeholder-gray-400 text-sm focus:border-orange-400 focus:outline-none"
              />
              <button className="p-1 text-orange-400 hover:text-orange-300 transition-colors">
                <Tag className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Status Actions */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <button
              onClick={() => handleStatusUpdate('reviewed')}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-500/20 border border-blue-500/30 rounded text-blue-400 hover:bg-blue-500/30 transition-colors"
            >
              <CheckCircle className="w-4 h-4" />
              Reviewed
            </button>
            
            <button
              onClick={() => handleStatusUpdate('escalated')}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-red-500/20 border border-red-500/30 rounded text-red-400 hover:bg-red-500/30 transition-colors"
            >
              <AlertTriangle className="w-4 h-4" />
              Escalate
            </button>
            
            <button
              onClick={() => handleStatusUpdate('false-alarm')}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-500/20 border border-gray-500/30 rounded text-gray-400 hover:bg-gray-500/30 transition-colors"
            >
              <Flag className="w-4 h-4" />
              False Alarm
            </button>
            
            <button
              onClick={handleExportCase}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-purple-500/20 border border-purple-500/30 rounded text-purple-400 hover:bg-purple-500/30 transition-colors"
            >
              <Tag className="w-4 h-4" />
              Export Case
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReplayViewer;

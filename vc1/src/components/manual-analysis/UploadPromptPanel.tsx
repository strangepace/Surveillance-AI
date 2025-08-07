
import React, { useState, useRef } from 'react';
import { Upload, Video, ArrowRight, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { UploadedVideo, AnalysisPrompt } from '@/types/manual-analysis';

interface UploadPromptPanelProps {
  onAnalyze: (video: UploadedVideo, prompt: AnalysisPrompt) => void;
}

const UploadPromptPanel: React.FC<UploadPromptPanelProps> = ({ onAnalyze }) => {
  const [video, setVideo] = useState<UploadedVideo | null>(null);
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState<'chatgpt' | 'vertex'>('chatgpt');
  const [mode, setMode] = useState<'basic' | 'advanced'>('basic');
  const [confidence, setConfidence] = useState(75);
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith('video/')) {
      const videoElement = document.createElement('video');
      videoElement.src = URL.createObjectURL(file);
      videoElement.onloadedmetadata = () => {
        setVideo({
          file,
          url: videoElement.src,
          duration: videoElement.duration,
          size: file.size
        });
      };
    }
  };

  const handleAnalyze = () => {
    if (video && prompt.trim()) {
      onAnalyze(video, {
        text: prompt,
        model,
        mode,
        confidence: mode === 'advanced' ? confidence : undefined
      });
    }
  };

  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      {/* Video Upload Section */}
      <div className="bg-black/30 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-lg">
        <h3 className="text-cyan-400 font-mono text-lg mb-4">Upload Video</h3>
        
        {!video ? (
          <div 
            className="border-2 border-dashed border-cyan-500/50 rounded-lg p-8 text-center cursor-pointer hover:border-cyan-400 transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="w-12 h-12 text-cyan-400 mx-auto mb-4" />
            <p className="text-white font-mono">Click to upload video file</p>
            <p className="text-gray-400 text-sm mt-2">MP4, AVI, MOV supported</p>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>
        ) : (
          <div className="bg-black/50 rounded-lg p-4 flex items-center gap-4">
            <Video className="w-8 h-8 text-cyan-400" />
            <div className="flex-1">
              <p className="text-white font-mono">{video.file.name}</p>
              <p className="text-gray-400 text-sm">
                {formatFileSize(video.size)} • {formatDuration(video.duration)}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              className="border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10"
            >
              Change
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>
        )}
      </div>

      {/* Prompt Input Section */}
      <div className="bg-black/30 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-lg">
        <h3 className="text-cyan-400 font-mono text-lg mb-4">Analysis Prompt</h3>
        <div className="space-y-4">
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe what you're looking for... (e.g., 'person in red jacket', 'suspicious activity near entrance')"
            className="min-h-[120px] bg-black/50 border-cyan-500/30 text-white font-mono resize-none focus:border-cyan-400"
          />
          
          {/* Character count */}
          <div className="text-right">
            <span className="text-gray-400 text-sm font-mono">{prompt.length}/500</span>
          </div>
        </div>
      </div>

      {/* Model & Mode Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Model Selection */}
        <div className="bg-black/30 border border-cyan-500/30 rounded-lg p-4 backdrop-blur-lg">
          <h4 className="text-cyan-400 font-mono text-sm mb-3">AI Model</h4>
          <div className="relative">
            <button
              onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
              className="w-full bg-black/50 border border-cyan-500/30 rounded px-3 py-2 text-white font-mono flex items-center justify-between hover:border-cyan-400 transition-colors"
            >
              <span>{model === 'chatgpt' ? 'ChatGPT-4' : 'Google Vertex AI'}</span>
              <ChevronDown className="w-4 h-4" />
            </button>
            
            {isModelDropdownOpen && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-black/90 border border-cyan-500/30 rounded z-10">
                <button
                  onClick={() => { setModel('chatgpt'); setIsModelDropdownOpen(false); }}
                  className="w-full px-3 py-2 text-left text-white font-mono hover:bg-cyan-500/10 transition-colors"
                >
                  ChatGPT-4
                </button>
                <button
                  onClick={() => { setModel('vertex'); setIsModelDropdownOpen(false); }}
                  className="w-full px-3 py-2 text-left text-white font-mono hover:bg-cyan-500/10 transition-colors"
                >
                  Google Vertex AI
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Mode Selection */}
        <div className="bg-black/30 border border-cyan-500/30 rounded-lg p-4 backdrop-blur-lg">
          <h4 className="text-cyan-400 font-mono text-sm mb-3">Analysis Mode</h4>
          <div className="flex gap-2">
            <button
              onClick={() => setMode('basic')}
              className={`flex-1 px-3 py-2 rounded font-mono text-sm transition-all ${
                mode === 'basic'
                  ? 'bg-cyan-500/20 border border-cyan-400 text-cyan-300'
                  : 'bg-black/50 border border-gray-600 text-gray-300 hover:border-cyan-500/50'
              }`}
            >
              Basic
            </button>
            <button
              onClick={() => setMode('advanced')}
              className={`flex-1 px-3 py-2 rounded font-mono text-sm transition-all ${
                mode === 'advanced'
                  ? 'bg-cyan-500/20 border border-cyan-400 text-cyan-300'
                  : 'bg-black/50 border border-gray-600 text-gray-300 hover:border-cyan-500/50'
              }`}
            >
              Advanced
            </button>
          </div>
        </div>
      </div>

      {/* Advanced Settings */}
      {mode === 'advanced' && (
        <div className="bg-black/30 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-lg">
          <h4 className="text-cyan-400 font-mono text-sm mb-4">Detection Confidence</h4>
          <div className="space-y-2">
            <input
              type="range"
              min="50"
              max="95"
              value={confidence}
              onChange={(e) => setConfidence(Number(e.target.value))}
              className="w-full accent-cyan-400"
            />
            <div className="flex justify-between text-sm font-mono">
              <span className="text-gray-400">50%</span>
              <span className="text-cyan-400">{confidence}%</span>
              <span className="text-gray-400">95%</span>
            </div>
          </div>
        </div>
      )}

      {/* Analyze Button */}
      <div className="flex justify-center">
        <Button
          onClick={handleAnalyze}
          disabled={!video || !prompt.trim()}
          className="bg-gradient-to-r from-cyan-500/20 to-blue-600/20 border border-cyan-400/50 text-cyan-300 hover:text-white hover:border-cyan-300 hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] px-8 py-3 font-mono text-lg tracking-wider disabled:opacity-50 disabled:cursor-not-allowed group"
        >
          <ArrowRight className="w-5 h-5 mr-2 group-hover:translate-x-1 transition-transform" />
          Analyze Video
        </Button>
      </div>
    </div>
  );
};

export default UploadPromptPanel;

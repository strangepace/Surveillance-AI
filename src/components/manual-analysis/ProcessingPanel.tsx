
import React from 'react';
import { Loader2, X, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ProcessingStatus } from '@/types/manual-analysis';

interface ProcessingPanelProps {
  status: ProcessingStatus;
  onCancel: () => void;
  onViewResults: () => void;
}

const ProcessingPanel: React.FC<ProcessingPanelProps> = ({ 
  status, 
  onCancel, 
  onViewResults 
}) => {
  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'analyzing': return 'text-yellow-400';
      case 'matching': return 'text-blue-400';
      case 'generating': return 'text-purple-400';
      case 'completed': return 'text-green-400';
      default: return 'text-cyan-400';
    }
  };

  const getStageDescription = (stage: string) => {
    switch (stage) {
      case 'analyzing': return 'Analyzing video frames...';
      case 'matching': return 'Finding pattern matches...';
      case 'generating': return 'Generating results...';
      case 'completed': return 'Analysis complete!';
      default: return 'Processing...';
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-mono font-bold text-white mb-2">
          Video Analysis in Progress
        </h2>
        <p className="text-gray-400">AI is analyzing your video for matches</p>
      </div>

      {/* Main Processing Panel */}
      <div className="bg-black/30 border border-cyan-500/30 rounded-lg p-8 backdrop-blur-lg">
        {/* Status Display */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
            <span className={`text-xl font-mono ${getStageColor(status.stage)}`}>
              {status.stage.toUpperCase()}
            </span>
          </div>
          <p className="text-white font-mono text-lg">{getStageDescription(status.stage)}</p>
          <p className="text-gray-400 mt-2">{status.message}</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm font-mono mb-2">
            <span className="text-gray-400">Progress</span>
            <span className="text-cyan-400">{Math.round(status.progress)}%</span>
          </div>
          <Progress 
            value={status.progress} 
            className="h-3 bg-black/50"
          />
        </div>

        {/* Timeline Visualization */}
        <div className="mb-8">
          <h4 className="text-cyan-400 font-mono text-sm mb-4">Detection Timeline</h4>
          <div className="bg-black/50 rounded-lg p-4">
            <div className="flex h-8 gap-1 overflow-hidden rounded">
              {status.timeline.map((segment, index) => (
                <div
                  key={index}
                  className={`flex-1 transition-all duration-500 ${
                    segment.hasMatch
                      ? 'bg-gradient-to-t from-cyan-500 to-cyan-300 animate-pulse'
                      : 'bg-gray-700'
                  }`}
                  style={{
                    opacity: segment.hasMatch ? (segment.confidence || 100) / 100 : 0.3
                  }}
                />
              ))}
            </div>
            <div className="flex justify-between text-xs text-gray-400 mt-2 font-mono">
              <span>0:00</span>
              <span>Matches lighting up in real-time</span>
              <span>End</span>
            </div>
          </div>
        </div>

        {/* Live Detection Feed */}
        <div className="mb-8">
          <h4 className="text-cyan-400 font-mono text-sm mb-4">Live Detection Feed</h4>
          <div className="bg-black/50 rounded-lg p-4 h-32 overflow-y-auto">
            <div className="space-y-2 font-mono text-sm">
              {[
                { time: '00:15', message: 'Object detection initialized', type: 'info' },
                { time: '00:23', message: 'Pattern match found at 00:45', type: 'success' },
                { time: '00:31', message: 'Analyzing frame sequence 120-180', type: 'info' },
                { time: '00:38', message: 'High confidence match at 01:23', type: 'success' },
                { time: '00:42', message: 'Processing final segments...', type: 'info' }
              ].map((log, index) => (
                <div key={index} className="flex gap-3">
                  <span className="text-gray-500">[{log.time}]</span>
                  <span className={
                    log.type === 'success' ? 'text-green-400' : 
                    log.type === 'warning' ? 'text-yellow-400' : 'text-gray-300'
                  }>
                    {log.message}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center gap-4">
          <Button
            onClick={onCancel}
            variant="outline"
            className="border-red-500/50 text-red-400 hover:bg-red-500/10 hover:border-red-400"
          >
            <X className="w-4 h-4 mr-2" />
            Cancel Analysis
          </Button>
          
          {status.stage === 'completed' && (
            <Button
              onClick={onViewResults}
              className="bg-gradient-to-r from-cyan-500/20 to-blue-600/20 border border-cyan-400/50 text-cyan-300 hover:text-white hover:border-cyan-300 hover:shadow-[0_0_30px_rgba(6,182,212,0.5)]"
            >
              <Eye className="w-4 h-4 mr-2" />
              View Results
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProcessingPanel;

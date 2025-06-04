
import React, { useState } from 'react';
import { Download, Share2, Eye, FileText, Archive, Play } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DetectionMatch, ExportSettings } from '@/types/manual-analysis';

interface ResultsPanelProps {
  matches: DetectionMatch[];
  onExport: (settings: ExportSettings) => void;
  prompt: string;
  model: string;
}

const ResultsPanel: React.FC<ResultsPanelProps> = ({ 
  matches, 
  onExport, 
  prompt,
  model 
}) => {
  const [selectedMatch, setSelectedMatch] = useState<DetectionMatch | null>(null);
  const [exportSettings, setExportSettings] = useState<ExportSettings>({
    includeMetadata: true,
    format: 'zip',
    videoFormat: 'mp4'
  });

  const formatTimestamp = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-400 border-green-400/30 bg-green-400/10';
    if (confidence >= 60) return 'text-yellow-400 border-yellow-400/30 bg-yellow-400/10';
    return 'text-red-400 border-red-400/30 bg-red-400/10';
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
      {/* Results List */}
      <div className="lg:col-span-3 space-y-4">
        <div className="bg-black/30 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-lg">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-mono font-bold text-white">Analysis Results</h2>
              <p className="text-gray-400 mt-1">Found {matches.length} matches</p>
            </div>
            <Badge variant="outline" className="border-cyan-400/50 text-cyan-400">
              {model.toUpperCase()}
            </Badge>
          </div>

          {/* Prompt Display */}
          <div className="bg-black/50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-400 mb-1 font-mono">SEARCH PROMPT:</p>
            <p className="text-white font-mono">"{prompt}"</p>
          </div>

          {/* Results Grid */}
          <div className="space-y-3 max-h-[600px] overflow-y-auto">
            {matches.map((match) => (
              <div
                key={match.id}
                className="bg-black/50 border border-gray-600/30 rounded-lg p-4 hover:border-cyan-500/50 transition-colors cursor-pointer"
                onClick={() => setSelectedMatch(match)}
              >
                <div className="flex items-center gap-4">
                  {/* Thumbnail */}
                  <div className="relative w-24 h-16 bg-gray-800 rounded overflow-hidden flex-shrink-0">
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Play className="w-6 h-6 text-cyan-400" />
                    </div>
                    <div className="absolute bottom-1 right-1 bg-black/70 text-white text-xs px-1 rounded font-mono">
                      {formatTimestamp(match.timestamp)}
                    </div>
                  </div>

                  {/* Match Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-white font-mono">Match {match.id}</h3>
                      <Badge 
                        variant="outline" 
                        className={getConfidenceColor(match.confidence)}
                      >
                        {match.confidence}% confidence
                      </Badge>
                    </div>
                    <p className="text-gray-300 text-sm">{match.description}</p>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedMatch(match);
                      }}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-gray-500/50 text-gray-400 hover:bg-gray-500/10"
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-gray-500/50 text-gray-400 hover:bg-gray-500/10"
                    >
                      <Share2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Export Side Panel */}
      <div className="space-y-4">
        {/* Export Tools */}
        <div className="bg-black/30 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-lg">
          <h3 className="text-cyan-400 font-mono text-lg mb-4">Export Tools</h3>
          
          <div className="space-y-4">
            {/* Quick Export Buttons */}
            <Button
              onClick={() => onExport({ ...exportSettings, format: 'zip' })}
              className="w-full bg-gradient-to-r from-cyan-500/20 to-blue-600/20 border border-cyan-400/50 text-cyan-300 hover:text-white hover:border-cyan-300 hover:shadow-[0_0_20px_rgba(6,182,212,0.3)] justify-start"
            >
              <Archive className="w-4 h-4 mr-2" />
              Export All (ZIP)
            </Button>
            
            <Button
              onClick={() => onExport({ ...exportSettings, format: 'csv' })}
              variant="outline"
              className="w-full border-gray-500/50 text-gray-300 hover:bg-gray-500/10 justify-start"
            >
              <FileText className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
            
            <Button
              onClick={() => onExport({ ...exportSettings, format: 'pdf' })}
              variant="outline"
              className="w-full border-gray-500/50 text-gray-300 hover:bg-gray-500/10 justify-start"
            >
              <FileText className="w-4 h-4 mr-2" />
              Generate PDF Report
            </Button>
          </div>
        </div>

        {/* Metadata Overview */}
        <div className="bg-black/30 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-lg">
          <h3 className="text-cyan-400 font-mono text-lg mb-4">Analysis Info</h3>
          
          <div className="space-y-3 text-sm font-mono">
            <div className="flex justify-between">
              <span className="text-gray-400">Model:</span>
              <span className="text-white">{model.toUpperCase()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Matches:</span>
              <span className="text-white">{matches.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Avg Confidence:</span>
              <span className="text-white">
                {matches.length > 0 
                  ? Math.round(matches.reduce((sum, match) => sum + match.confidence, 0) / matches.length)
                  : 0}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Analysis Time:</span>
              <span className="text-white">2m 34s</span>
            </div>
          </div>
        </div>

        {/* Export Settings */}
        <div className="bg-black/30 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-lg">
          <h3 className="text-cyan-400 font-mono text-lg mb-4">Export Settings</h3>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm text-gray-400 font-mono mb-2 block">Video Format</label>
              <select
                value={exportSettings.videoFormat}
                onChange={(e) => setExportSettings(prev => ({ 
                  ...prev, 
                  videoFormat: e.target.value as 'mp4' | 'avi' | 'mov' 
                }))}
                className="w-full bg-black/50 border border-gray-600/30 rounded px-3 py-2 text-white font-mono text-sm focus:border-cyan-400"
              >
                <option value="mp4">MP4</option>
                <option value="avi">AVI</option>
                <option value="mov">MOV</option>
              </select>
            </div>
            
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="include-metadata"
                checked={exportSettings.includeMetadata}
                onChange={(e) => setExportSettings(prev => ({ 
                  ...prev, 
                  includeMetadata: e.target.checked 
                }))}
                className="w-4 h-4 accent-cyan-400"
              />
              <label htmlFor="include-metadata" className="text-sm text-gray-300 font-mono">
                Include metadata
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Preview Modal */}
      {selectedMatch && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-black/90 border border-cyan-500/30 rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto backdrop-blur-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-mono text-white">Match {selectedMatch.id} Preview</h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedMatch(null)}
                className="border-gray-500/50 text-gray-400"
              >
                ✕
              </Button>
            </div>
            
            {/* Video Preview Placeholder */}
            <div className="bg-black rounded-lg aspect-video flex items-center justify-center mb-4">
              <div className="text-center">
                <Play className="w-16 h-16 text-cyan-400 mx-auto mb-2" />
                <p className="text-white font-mono">Preview at {formatTimestamp(selectedMatch.timestamp)}</p>
                <p className="text-gray-400 text-sm">{selectedMatch.confidence}% confidence</p>
              </div>
            </div>
            
            <p className="text-gray-300 mb-4">{selectedMatch.description}</p>
            
            <div className="flex gap-2">
              <Button className="bg-cyan-500/20 border border-cyan-400/50 text-cyan-300">
                <Download className="w-4 h-4 mr-2" />
                Download Clip
              </Button>
              <Button variant="outline" className="border-gray-500/50 text-gray-400">
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsPanel;

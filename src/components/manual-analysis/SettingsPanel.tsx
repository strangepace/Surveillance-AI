
import React, { useState } from 'react';
import { Settings, History, MessageSquare, ExternalLink, Trash2, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { AnalysisSession } from '@/types/manual-analysis';

interface SettingsPanelProps {
  sessions: AnalysisSession[];
  onReanalyze: (session: AnalysisSession) => void;
  onDeleteSession: (sessionId: string) => void;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ 
  sessions, 
  onReanalyze, 
  onDeleteSession 
}) => {
  const [activeTab, setActiveTab] = useState<'settings' | 'history' | 'feedback' | 'legal'>('settings');
  const [defaultModel, setDefaultModel] = useState<'chatgpt' | 'vertex'>('chatgpt');
  const [defaultMode, setDefaultMode] = useState<'basic' | 'advanced'>('basic');
  const [defaultConfidence, setDefaultConfidence] = useState(75);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackType, setFeedbackType] = useState<'issue' | 'feature'>('issue');

  const formatDate = (date: Date) => {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400';
      case 'processing': return 'text-yellow-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const tabs = [
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'history', label: 'History', icon: History },
    { id: 'feedback', label: 'Feedback', icon: MessageSquare },
    { id: 'legal', label: 'Legal & Docs', icon: ExternalLink }
  ];

  return (
    <div className="max-w-6xl mx-auto">
      {/* Tab Navigation */}
      <div className="bg-black/30 border border-cyan-500/30 rounded-lg mb-6 backdrop-blur-lg">
        <div className="flex overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-6 py-4 font-mono text-sm whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? 'text-cyan-400 border-b-2 border-cyan-400 bg-cyan-500/10'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-black/30 border border-cyan-500/30 rounded-lg p-6 backdrop-blur-lg">
        {activeTab === 'settings' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-mono font-bold text-white mb-6">Analysis Settings</h2>
            
            {/* Default Model & Mode */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-cyan-400 font-mono text-lg mb-4">Default AI Model</h3>
                <div className="space-y-2">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="model"
                      value="chatgpt"
                      checked={defaultModel === 'chatgpt'}
                      onChange={(e) => setDefaultModel(e.target.value as 'chatgpt')}
                      className="w-4 h-4 accent-cyan-400"
                    />
                    <span className="text-white font-mono">ChatGPT-4</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="model"
                      value="vertex"
                      checked={defaultModel === 'vertex'}
                      onChange={(e) => setDefaultModel(e.target.value as 'vertex')}
                      className="w-4 h-4 accent-cyan-400"
                    />
                    <span className="text-white font-mono">Google Vertex AI</span>
                  </label>
                </div>
              </div>

              <div>
                <h3 className="text-cyan-400 font-mono text-lg mb-4">Default Analysis Mode</h3>
                <div className="space-y-2">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="mode"
                      value="basic"
                      checked={defaultMode === 'basic'}
                      onChange={(e) => setDefaultMode(e.target.value as 'basic')}
                      className="w-4 h-4 accent-cyan-400"
                    />
                    <span className="text-white font-mono">Basic</span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="radio"
                      name="mode"
                      value="advanced"
                      checked={defaultMode === 'advanced'}
                      onChange={(e) => setDefaultMode(e.target.value as 'advanced')}
                      className="w-4 h-4 accent-cyan-400"
                    />
                    <span className="text-white font-mono">Advanced</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Advanced Settings */}
            {defaultMode === 'advanced' && (
              <div>
                <h3 className="text-cyan-400 font-mono text-lg mb-4">Detection Confidence Threshold</h3>
                <div className="space-y-2">
                  <input
                    type="range"
                    min="50"
                    max="95"
                    value={defaultConfidence}
                    onChange={(e) => setDefaultConfidence(Number(e.target.value))}
                    className="w-full accent-cyan-400"
                  />
                  <div className="flex justify-between text-sm font-mono">
                    <span className="text-gray-400">50%</span>
                    <span className="text-cyan-400">{defaultConfidence}%</span>
                    <span className="text-gray-400">95%</span>
                  </div>
                  <p className="text-gray-400 text-sm">Higher values reduce false positives but may miss some matches</p>
                </div>
              </div>
            )}

            {/* User Preferences */}
            <div>
              <h3 className="text-cyan-400 font-mono text-lg mb-4">User Preferences</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-400 font-mono mb-2 block">User Role</label>
                  <select className="w-full bg-black/50 border border-gray-600/30 rounded px-3 py-2 text-white font-mono text-sm focus:border-cyan-400">
                    <option value="viewer">Viewer</option>
                    <option value="responder">Responder</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
                
                <div className="flex items-center gap-3">
                  <input type="checkbox" id="auto-export" className="w-4 h-4 accent-cyan-400" />
                  <label htmlFor="auto-export" className="text-sm text-gray-300 font-mono">
                    Auto-export results after analysis
                  </label>
                </div>
                
                <div className="flex items-center gap-3">
                  <input type="checkbox" id="notifications" className="w-4 h-4 accent-cyan-400" />
                  <label htmlFor="notifications" className="text-sm text-gray-300 font-mono">
                    Enable desktop notifications
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-mono font-bold text-white mb-6">Session History</h2>
            
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {sessions.map((session) => (
                <div key={session.id} className="bg-black/50 border border-gray-600/30 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-white font-mono">Session {session.id}</h3>
                        <span className={`text-sm font-mono ${getStatusColor(session.status)}`}>
                          {session.status.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-gray-300 text-sm mb-2">"{session.prompt}"</p>
                      <div className="flex gap-4 text-xs text-gray-400 font-mono">
                        <span>{formatDate(session.timestamp)}</span>
                        <span>{session.matchCount} matches</span>
                        <span>{session.model}</span>
                        <span>{session.mode}</span>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onReanalyze(session)}
                        className="border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10"
                      >
                        <RotateCcw className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onDeleteSession(session.id)}
                        className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
              
              {sessions.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-gray-400 font-mono">No analysis sessions yet</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'feedback' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-mono font-bold text-white mb-6">Feedback & Support</h2>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-400 font-mono mb-2 block">Feedback Type</label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="feedbackType"
                      value="issue"
                      checked={feedbackType === 'issue'}
                      onChange={(e) => setFeedbackType(e.target.value as 'issue')}
                      className="w-4 h-4 accent-cyan-400"
                    />
                    <span className="text-white font-mono">Report Issue</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="feedbackType"
                      value="feature"
                      checked={feedbackType === 'feature'}
                      onChange={(e) => setFeedbackType(e.target.value as 'feature')}
                      className="w-4 h-4 accent-cyan-400"
                    />
                    <span className="text-white font-mono">Suggest Feature</span>
                  </label>
                </div>
              </div>
              
              <div>
                <label className="text-sm text-gray-400 font-mono mb-2 block">
                  {feedbackType === 'issue' ? 'Describe the issue' : 'Describe your feature request'}
                </label>
                <Textarea
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  placeholder={feedbackType === 'issue' 
                    ? "Please describe the issue you encountered..."
                    : "Please describe the feature you'd like to see..."
                  }
                  className="min-h-[120px] bg-black/50 border-cyan-500/30 text-white font-mono"
                />
              </div>
              
              <Button className="bg-gradient-to-r from-cyan-500/20 to-blue-600/20 border border-cyan-400/50 text-cyan-300 hover:text-white hover:border-cyan-300">
                <MessageSquare className="w-4 h-4 mr-2" />
                Submit Feedback
              </Button>
            </div>
          </div>
        )}

        {activeTab === 'legal' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-mono font-bold text-white mb-6">Legal & Documentation</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-cyan-400 font-mono text-lg">Legal</h3>
                <div className="space-y-2">
                  <a href="#" className="flex items-center gap-2 text-gray-300 hover:text-cyan-400 transition-colors">
                    <ExternalLink className="w-4 h-4" />
                    <span className="font-mono">Privacy Policy</span>
                  </a>
                  <a href="#" className="flex items-center gap-2 text-gray-300 hover:text-cyan-400 transition-colors">
                    <ExternalLink className="w-4 h-4" />
                    <span className="font-mono">Terms of Service</span>
                  </a>
                  <a href="#" className="flex items-center gap-2 text-gray-300 hover:text-cyan-400 transition-colors">
                    <ExternalLink className="w-4 h-4" />
                    <span className="font-mono">Data Processing Agreement</span>
                  </a>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="text-cyan-400 font-mono text-lg">Documentation</h3>
                <div className="space-y-2">
                  <a href="#" className="flex items-center gap-2 text-gray-300 hover:text-cyan-400 transition-colors">
                    <ExternalLink className="w-4 h-4" />
                    <span className="font-mono">API Documentation</span>
                  </a>
                  <a href="#" className="flex items-center gap-2 text-gray-300 hover:text-cyan-400 transition-colors">
                    <ExternalLink className="w-4 h-4" />
                    <span className="font-mono">User Guide</span>
                  </a>
                  <a href="#" className="flex items-center gap-2 text-gray-300 hover:text-cyan-400 transition-colors">
                    <ExternalLink className="w-4 h-4" />
                    <span className="font-mono">Integration Examples</span>
                  </a>
                </div>
              </div>
            </div>
            
            <div className="bg-black/50 rounded-lg p-4 mt-6">
              <h4 className="text-white font-mono mb-2">System Information</h4>
              <div className="grid grid-cols-2 gap-4 text-sm font-mono">
                <div className="flex justify-between">
                  <span className="text-gray-400">Version:</span>
                  <span className="text-white">v2.1.0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Build:</span>
                  <span className="text-white">2024.03.15</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Environment:</span>
                  <span className="text-white">Production</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Region:</span>
                  <span className="text-white">US-East</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SettingsPanel;


import React, { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import UploadPromptPanel from '@/components/manual-analysis/UploadPromptPanel';
import ProcessingPanel from '@/components/manual-analysis/ProcessingPanel';
import ResultsPanel from '@/components/manual-analysis/ResultsPanel';
import SettingsPanel from '@/components/manual-analysis/SettingsPanel';
import { 
  UploadedVideo, 
  AnalysisPrompt, 
  ProcessingStatus, 
  DetectionMatch, 
  AnalysisSession,
  ExportSettings 
} from '@/types/manual-analysis';

type AnalysisStep = 'upload' | 'processing' | 'results' | 'settings';

const ManualAnalysis = () => {
  const [currentStep, setCurrentStep] = useState<AnalysisStep>('upload');
  const [currentVideo, setCurrentVideo] = useState<UploadedVideo | null>(null);
  const [currentPrompt, setCurrentPrompt] = useState<AnalysisPrompt | null>(null);
  
  // Mock data for demonstration
  const [processingStatus] = useState<ProcessingStatus>({
    stage: 'matching',
    progress: 65,
    message: 'Analyzing frame sequences for pattern matches...',
    timeline: Array.from({ length: 20 }, (_, i) => ({
      start: i * 5,
      end: (i + 1) * 5,
      hasMatch: Math.random() > 0.7,
      confidence: Math.random() * 40 + 60
    }))
  });

  const [mockMatches] = useState<DetectionMatch[]>([
    {
      id: '001',
      timestamp: 45,
      thumbnailUrl: '',
      clipUrl: '',
      confidence: 89,
      description: 'Person in red jacket detected near entrance'
    },
    {
      id: '002',
      timestamp: 127,
      thumbnailUrl: '',
      clipUrl: '',
      confidence: 76,
      description: 'Similar clothing pattern identified in corridor'
    },
    {
      id: '003',
      timestamp: 203,
      thumbnailUrl: '',
      clipUrl: '',
      confidence: 82,
      description: 'Red jacket match in parking area'
    }
  ]);

  const [mockSessions] = useState<AnalysisSession[]>([
    {
      id: '001',
      prompt: 'person in red jacket',
      timestamp: new Date(Date.now() - 86400000),
      matchCount: 3,
      model: 'ChatGPT-4',
      mode: 'advanced',
      status: 'completed',
      matches: mockMatches
    },
    {
      id: '002',
      prompt: 'suspicious activity near door',
      timestamp: new Date(Date.now() - 172800000),
      matchCount: 7,
      model: 'Vertex AI',
      mode: 'basic',
      status: 'completed',
      matches: []
    }
  ]);

  const handleAnalyze = (video: UploadedVideo, prompt: AnalysisPrompt) => {
    setCurrentVideo(video);
    setCurrentPrompt(prompt);
    setCurrentStep('processing');
    
    // Simulate processing completion
    setTimeout(() => {
      setCurrentStep('results');
    }, 5000);
  };

  const handleCancelProcessing = () => {
    setCurrentStep('upload');
  };

  const handleViewResults = () => {
    setCurrentStep('results');
  };

  const handleExport = (settings: ExportSettings) => {
    console.log('Exporting with settings:', settings);
    // Implement export logic
  };

  const handleReanalyze = (session: AnalysisSession) => {
    console.log('Re-analyzing session:', session.id);
    // Implement re-analysis logic
  };

  const handleDeleteSession = (sessionId: string) => {
    console.log('Deleting session:', sessionId);
    // Implement session deletion logic
  };

  const getStepName = (step: AnalysisStep) => {
    switch (step) {
      case 'upload': return 'M1 - Upload & Prompt';
      case 'processing': return 'M2 - Processing';
      case 'results': return 'M3 - Results';
      case 'settings': return 'M4 - Settings';
      default: return 'Manual Analysis';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black">
      {/* Navigation Header */}
      <nav className="relative z-50 p-6 border-b border-cyan-500/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link 
              to="/" 
              className="inline-flex items-center gap-2 text-gray-300 hover:text-cyan-400 transition-colors font-mono"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Home
            </Link>
            
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-mono font-bold text-white">
                {getStepName(currentStep)}
              </h1>
              
              {/* Step Navigation */}
              <div className="hidden md:flex items-center gap-2">
                {['upload', 'processing', 'results', 'settings'].map((step, index) => (
                  <button
                    key={step}
                    onClick={() => {
                      if (step === 'settings' || 
                          (step === 'results' && currentStep !== 'upload') ||
                          (step === 'upload')) {
                        setCurrentStep(step as AnalysisStep);
                      }
                    }}
                    className={`px-3 py-1 rounded font-mono text-sm transition-colors ${
                      currentStep === step
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/50'
                        : 'text-gray-400 hover:text-gray-200 border border-transparent'
                    }`}
                    disabled={step === 'processing' || (step === 'results' && currentStep === 'upload')}
                  >
                    M{index + 1}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="p-6">
        {currentStep === 'upload' && (
          <div className="max-w-4xl mx-auto">
            <UploadPromptPanel onAnalyze={handleAnalyze} />
          </div>
        )}

        {currentStep === 'processing' && (
          <ProcessingPanel
            status={processingStatus}
            onCancel={handleCancelProcessing}
            onViewResults={handleViewResults}
          />
        )}

        {currentStep === 'results' && currentPrompt && (
          <ResultsPanel
            matches={mockMatches}
            onExport={handleExport}
            prompt={currentPrompt.text}
            model={currentPrompt.model}
          />
        )}

        {currentStep === 'settings' && (
          <SettingsPanel
            sessions={mockSessions}
            onReanalyze={handleReanalyze}
            onDeleteSession={handleDeleteSession}
          />
        )}
      </div>

      {/* Background Effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 opacity-20">
          <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="manual-grid" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(0, 255, 255, 0.2)" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#manual-grid)" />
          </svg>
        </div>
        
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/10 via-transparent to-purple-900/10" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent" />
      </div>
    </div>
  );
};

export default ManualAnalysis;

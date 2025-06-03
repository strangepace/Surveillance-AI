
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Video, Eye, Zap, Target } from 'lucide-react';
import TechGrid from '@/components/TechGrid';
import Navigation from '@/components/Navigation';
import GlitchButton from '@/components/GlitchButton';

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black relative overflow-hidden">
      <TechGrid />
      <Navigation />
      
      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex flex-col items-center justify-center px-6">
        {/* Hero Section */}
        <div className="text-center space-y-8 max-w-4xl mx-auto">
          {/* Main Logo/Icon */}
          <div className="flex justify-center mb-8">
            <div className="relative">
              <div className="w-24 h-24 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-full flex items-center justify-center shadow-[0_0_50px_rgba(6,182,212,0.5)]">
                <Eye className="w-12 h-12 text-white" />
              </div>
              <div className="absolute inset-0 w-24 h-24 border-2 border-cyan-400 rounded-full animate-ping" />
            </div>
          </div>
          
          {/* Title */}
          <h1 className="text-6xl md:text-7xl font-mono font-bold text-white tracking-wider mb-6">
            SURVEILLANCE
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
              .AI
            </span>
          </h1>
          
          {/* Tagline */}
          <p className="text-2xl md:text-3xl text-gray-300 font-mono tracking-wide mb-12">
            AI-Powered Video Intelligence
          </p>
          
          {/* Subtitle */}
          <p className="text-lg text-gray-400 max-w-2xl mx-auto leading-relaxed mb-16">
            Advanced surveillance analytics platform for law enforcement, private security, 
            and monitoring operations. Real-time threat detection and forensic video analysis.
          </p>
          
          {/* CTA Buttons */}
          <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
            {/* Manual Analysis CTA */}
            <div className="space-y-4">
              <div className="bg-black/30 backdrop-blur-lg border border-purple-500/30 rounded-lg p-8 hover:border-purple-400/50 transition-all duration-300 group">
                <div className="flex justify-center mb-4">
                  <Video className="w-12 h-12 text-purple-400 group-hover:text-purple-300 transition-colors" />
                </div>
                <h3 className="text-xl font-mono font-bold text-white mb-3">
                  Forensic Analysis
                </h3>
                <p className="text-gray-400 mb-6 text-sm leading-relaxed">
                  Upload videos for AI-powered investigation. Extract insights, identify suspects, analyze patterns.
                </p>
                <GlitchButton 
                  variant="secondary" 
                  onClick={() => navigate('/manual-analysis')}
                  className="w-full"
                >
                  <Target className="w-5 h-5" />
                  Start Manual Video Analysis
                </GlitchButton>
              </div>
            </div>
            
            {/* Live Feed CTA */}
            <div className="space-y-4">
              <div className="bg-black/30 backdrop-blur-lg border border-cyan-500/30 rounded-lg p-8 hover:border-cyan-400/50 transition-all duration-300 group">
                <div className="flex justify-center mb-4">
                  <Zap className="w-12 h-12 text-cyan-400 group-hover:text-cyan-300 transition-colors" />
                </div>
                <h3 className="text-xl font-mono font-bold text-white mb-3">
                  Live Monitoring
                </h3>
                <p className="text-gray-400 mb-6 text-sm leading-relaxed">
                  Real-time CCTV analytics. Instant threat alerts, crowd monitoring, anomaly detection.
                </p>
                <GlitchButton 
                  variant="primary" 
                  onClick={() => navigate('/live-feed')}
                  className="w-full"
                >
                  <Eye className="w-5 h-5" />
                  Open Live Feed Dashboard
                </GlitchButton>
              </div>
            </div>
          </div>
          
          {/* Status Indicators */}
          <div className="flex justify-center gap-8 mt-16 text-sm font-mono">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
              <span className="text-gray-300">Systems Online</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-cyan-400 rounded-full animate-pulse" />
              <span className="text-gray-300">AI Models Active</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse" />
              <span className="text-gray-300">Secure Connection</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Bottom Grid Pattern */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black/50 to-transparent" />
    </div>
  );
};

export default Index;

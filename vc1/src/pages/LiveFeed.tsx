
import React, { useState, useEffect } from 'react';
import { ArrowLeft, Volume2, VolumeX, Settings, Search, Filter, Eye } from 'lucide-react';
import { Link } from 'react-router-dom';
import LiveVideoFeed from '@/components/live-feed/LiveVideoFeed';
import AlertPanel from '@/components/live-feed/AlertPanel';
import FilterPanel from '@/components/live-feed/FilterPanel';
import ReplayViewer from '@/components/live-feed/ReplayViewer';
import SettingsPanel from '@/components/live-feed/SettingsPanel';
import { Alert } from '@/types/live-feed';

const LiveFeed = () => {
  const [currentView, setCurrentView] = useState<'dashboard' | 'filter' | 'replay' | 'settings'>('dashboard');
  const [isMuted, setIsMuted] = useState(false);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  // Simulate real-time alerts
  useEffect(() => {
    const alertTypes = ['Fire Detection', 'Weapon Detected', 'Intrusion Alert', 'Crowd Anomaly', 'Vehicle Violation'];
    const severities: ('normal' | 'critical')[] = ['normal', 'critical'];
    
    const generateAlert = () => {
      const newAlert: Alert = {
        id: `ALERT-${Date.now()}`,
        timestamp: new Date(),
        type: alertTypes[Math.floor(Math.random() * alertTypes.length)],
        severity: severities[Math.floor(Math.random() * severities.length)],
        location: `Sector ${Math.floor(Math.random() * 10) + 1}`,
        description: 'Automated detection triggered',
        acknowledged: false,
        clipUrl: '/placeholder-clip.mp4'
      };
      
      setAlerts(prev => [newAlert, ...prev.slice(0, 49)]); // Keep last 50 alerts
    };

    const interval = setInterval(generateAlert, Math.random() * 8000 + 2000); // 2-10 seconds
    return () => clearInterval(interval);
  }, []);

  const acknowledgeAlert = (alertId: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, acknowledged: true } : alert
    ));
  };

  const viewReplay = (alert: Alert) => {
    setSelectedAlert(alert);
    setCurrentView('replay');
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'filter':
        return <FilterPanel alerts={alerts} onAlertSelect={viewReplay} onBack={() => setCurrentView('dashboard')} />;
      case 'replay':
        return <ReplayViewer alert={selectedAlert} onBack={() => setCurrentView('dashboard')} />;
      case 'settings':
        return <SettingsPanel onBack={() => setCurrentView('dashboard')} />;
      default:
        return (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
            {/* Live Video Feed */}
            <div className="lg:col-span-2">
              <LiveVideoFeed isMuted={isMuted} />
            </div>
            
            {/* Alert Panel */}
            <div className="lg:col-span-1">
              <AlertPanel 
                alerts={alerts} 
                onAcknowledge={acknowledgeAlert}
                onViewReplay={viewReplay}
              />
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black">
      {/* Header */}
      <div className="border-b border-cyan-500/20 bg-black/30 backdrop-blur-lg">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-4">
            <Link 
              to="/" 
              className="inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              Exit Live Feed
            </Link>
            
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
              <span className="text-white font-mono text-lg">LIVE MONITORING</span>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsMuted(!isMuted)}
              className={`p-2 rounded-lg border transition-all ${
                isMuted 
                  ? 'border-red-500/50 bg-red-500/10 text-red-400' 
                  : 'border-cyan-500/50 bg-cyan-500/10 text-cyan-400'
              }`}
            >
              {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
            </button>
            
            <button
              onClick={() => setCurrentView('filter')}
              className={`p-2 rounded-lg border transition-all ${
                currentView === 'filter'
                  ? 'border-purple-500/50 bg-purple-500/10 text-purple-400'
                  : 'border-gray-500/50 bg-gray-500/10 text-gray-400 hover:border-purple-500/50'
              }`}
            >
              <Filter className="w-5 h-5" />
            </button>
            
            <button
              onClick={() => setCurrentView('settings')}
              className={`p-2 rounded-lg border transition-all ${
                currentView === 'settings'
                  ? 'border-orange-500/50 bg-orange-500/10 text-orange-400'
                  : 'border-gray-500/50 bg-gray-500/10 text-gray-400 hover:border-orange-500/50'
              }`}
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6 h-[calc(100vh-80px)]">
        {renderCurrentView()}
      </div>
    </div>
  );
};

export default LiveFeed;

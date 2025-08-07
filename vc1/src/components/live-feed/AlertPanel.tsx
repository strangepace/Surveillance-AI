
import React from 'react';
import { Download, Share, MessageSquare, CheckCircle, AlertTriangle, Clock } from 'lucide-react';
import { Alert } from '@/types/live-feed';

interface AlertPanelProps {
  alerts: Alert[];
  onAcknowledge: (alertId: string) => void;
  onViewReplay: (alert: Alert) => void;
}

const AlertPanel: React.FC<AlertPanelProps> = ({ alerts, onAcknowledge, onViewReplay }) => {
  const handleAcknowledge = (alertId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    onAcknowledge(alertId);
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="h-full bg-black/50 border border-purple-500/30 rounded-lg backdrop-blur-lg overflow-hidden">
      {/* Panel Header */}
      <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-b border-purple-500/30 p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-white font-mono text-lg">ALERT FEED</h3>
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            <span className="text-yellow-400 font-mono text-sm">
              {alerts.filter(a => !a.acknowledged).length} ACTIVE
            </span>
          </div>
        </div>
      </div>

      {/* Alert List */}
      <div className="h-[calc(100%-80px)] overflow-y-auto p-4 space-y-3">
        {alerts.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p className="font-mono">Monitoring for alerts...</p>
          </div>
        ) : (
          alerts.map((alert, index) => (
            <div
              key={alert.id}
              className={`border rounded-lg p-4 cursor-pointer transition-all hover:scale-[1.02] ${
                alert.severity === 'critical'
                  ? alert.acknowledged
                    ? 'border-red-500/30 bg-red-500/5'
                    : 'border-red-500/50 bg-red-500/10 shadow-[0_0_20px_rgba(239,68,68,0.3)]'
                  : alert.acknowledged
                    ? 'border-green-500/30 bg-green-500/5'
                    : 'border-green-500/50 bg-green-500/10 shadow-[0_0_20px_rgba(34,197,94,0.3)]'
              }`}
              onClick={() => onViewReplay(alert)}
            >
              {/* Alert Header */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 text-xs font-mono rounded ${
                    alert.severity === 'critical'
                      ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                      : 'bg-green-500/20 text-green-400 border border-green-500/30'
                  }`}>
                    Alert {index + 1}
                  </span>
                  {alert.acknowledged && (
                    <CheckCircle className="w-4 h-4 text-cyan-400" />
                  )}
                </div>
                <span className="text-gray-400 text-xs font-mono">
                  {formatTime(alert.timestamp)}
                </span>
              </div>

              {/* Alert Content */}
              <div className="mb-3">
                <h4 className="text-white font-semibold mb-1">{alert.type}</h4>
                {alert.location && (
                  <p className="text-cyan-400 text-sm mb-1">{alert.location}</p>
                )}
                <p className="text-gray-300 text-sm">{alert.description}</p>
              </div>

              {/* Alert Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => handleAcknowledge(alert.id, e)}
                  disabled={alert.acknowledged}
                  className={`px-3 py-1 text-xs font-mono rounded transition-all ${
                    alert.acknowledged
                      ? 'bg-gray-500/20 text-gray-500 cursor-not-allowed'
                      : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/30'
                  }`}
                >
                  {alert.acknowledged ? 'Acknowledged' : 'Acknowledge'}
                </button>
                
                <button className="p-1 text-gray-400 hover:text-white transition-colors">
                  <Download className="w-4 h-4" />
                </button>
                
                <button className="p-1 text-gray-400 hover:text-white transition-colors">
                  <Share className="w-4 h-4" />
                </button>
                
                <button className="p-1 text-gray-400 hover:text-white transition-colors">
                  <MessageSquare className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AlertPanel;

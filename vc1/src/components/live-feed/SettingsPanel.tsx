
import React, { useState } from 'react';
import { ArrowLeft, Shield, Zap, Download, User, Save } from 'lucide-react';
import { DetectionSettings, ExportSettings } from '@/types/live-feed';

interface SettingsPanelProps {
  onBack: () => void;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ onBack }) => {
  const [detectionSettings, setDetectionSettings] = useState<DetectionSettings>({
    fire: true,
    weapon: true,
    intrusion: true,
    crowd: false,
    vehicle: true,
  });

  const [sensitivity, setSensitivity] = useState({
    fire: 75,
    weapon: 90,
    intrusion: 80,
    crowd: 60,
    vehicle: 70,
  });

  const [exportSettings, setExportSettings] = useState<ExportSettings>({
    autoExportZip: false,
    autoExportCsv: true,
    autoExportPdf: false,
    defaultFormat: 'mp4',
  });

  const [userMode, setUserMode] = useState<'viewer' | 'responder' | 'admin'>('responder');

  const toggleDetection = (key: keyof DetectionSettings) => {
    setDetectionSettings(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSensitivityChange = (key: string, value: number) => {
    setSensitivity(prev => ({ ...prev, [key]: value }));
  };

  const handleSaveSettings = () => {
    console.log('Settings saved:', { detectionSettings, sensitivity, exportSettings, userMode });
  };

  return (
    <div className="h-full bg-black/50 border border-orange-500/30 rounded-lg backdrop-blur-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-500/10 to-yellow-500/10 border-b border-orange-500/30 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="p-2 text-orange-400 hover:text-orange-300 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h3 className="text-white font-mono text-lg">SYSTEM CONFIGURATION</h3>
          </div>
          
          <button
            onClick={handleSaveSettings}
            className="flex items-center gap-2 px-4 py-2 bg-orange-500/20 border border-orange-500/30 rounded text-orange-400 hover:bg-orange-500/30 transition-colors"
          >
            <Save className="w-4 h-4" />
            Save Config
          </button>
        </div>
      </div>

      {/* Settings Content */}
      <div className="p-6 h-[calc(100%-80px)] overflow-y-auto space-y-8">
        {/* Detection Settings */}
        <div className="bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/30 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-6">
            <Shield className="w-6 h-6 text-red-400" />
            <h4 className="text-white font-mono text-lg">DETECTION MODULES</h4>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {Object.entries(detectionSettings).map(([key, enabled]) => (
              <div key={key} className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-white font-semibold capitalize">{key} Detection</label>
                  <button
                    onClick={() => toggleDetection(key as keyof DetectionSettings)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      enabled ? 'bg-red-500' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        enabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
                
                {enabled && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400 text-sm">Sensitivity</span>
                      <span className="text-orange-400 font-mono text-sm">{sensitivity[key as keyof typeof sensitivity]}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={sensitivity[key as keyof typeof sensitivity]}
                      onChange={(e) => handleSensitivityChange(key, Number(e.target.value))}
                      className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Alert Actions */}
        <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/30 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-6">
            <Zap className="w-6 h-6 text-yellow-400" />
            <h4 className="text-white font-mono text-lg">ALERT ACTIONS</h4>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4 text-yellow-500 bg-gray-800 border-yellow-500/30 rounded" />
              <span className="text-gray-300">Notify on Alert</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4 text-yellow-500 bg-gray-800 border-yellow-500/30 rounded" />
              <span className="text-gray-300">Audio Ping</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" className="w-4 h-4 text-yellow-500 bg-gray-800 border-yellow-500/30 rounded" />
              <span className="text-gray-300">Auto Escalate</span>
            </label>
          </div>
        </div>

        {/* Export Settings */}
        <div className="bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/30 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-6">
            <Download className="w-6 h-6 text-green-400" />
            <h4 className="text-white font-mono text-lg">EXPORT CONFIGURATION</h4>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h5 className="text-gray-300 font-semibold">Auto Export Options</h5>
              <div className="space-y-3">
                <label className="flex items-center justify-between">
                  <span className="text-gray-300">Auto Export ZIP</span>
                  <button
                    onClick={() => setExportSettings(prev => ({ ...prev, autoExportZip: !prev.autoExportZip }))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      exportSettings.autoExportZip ? 'bg-green-500' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        exportSettings.autoExportZip ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </label>
                
                <label className="flex items-center justify-between">
                  <span className="text-gray-300">Auto Export CSV</span>
                  <button
                    onClick={() => setExportSettings(prev => ({ ...prev, autoExportCsv: !prev.autoExportCsv }))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      exportSettings.autoExportCsv ? 'bg-green-500' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        exportSettings.autoExportCsv ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </label>
                
                <label className="flex items-center justify-between">
                  <span className="text-gray-300">Daily PDF Report</span>
                  <button
                    onClick={() => setExportSettings(prev => ({ ...prev, autoExportPdf: !prev.autoExportPdf }))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      exportSettings.autoExportPdf ? 'bg-green-500' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        exportSettings.autoExportPdf ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </label>
              </div>
            </div>

            <div className="space-y-4">
              <h5 className="text-gray-300 font-semibold">Default Format</h5>
              <select
                value={exportSettings.defaultFormat}
                onChange={(e) => setExportSettings(prev => ({ ...prev, defaultFormat: e.target.value as any }))}
                className="w-full p-3 bg-gray-800/50 border border-green-500/30 rounded text-white focus:border-green-400 focus:outline-none"
              >
                <option value="mp4">MP4</option>
                <option value="avi">AVI</option>
                <option value="mov">MOV</option>
              </select>
            </div>
          </div>
        </div>

        {/* User Preferences */}
        <div className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/30 rounded-lg p-6">
          <div className="flex items-center gap-3 mb-6">
            <User className="w-6 h-6 text-purple-400" />
            <h4 className="text-white font-mono text-lg">USER PREFERENCES</h4>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-gray-300 font-semibold mb-2">Operating Mode</label>
              <select
                value={userMode}
                onChange={(e) => setUserMode(e.target.value as any)}
                className="w-full p-3 bg-gray-800/50 border border-purple-500/30 rounded text-white focus:border-purple-400 focus:outline-none"
              >
                <option value="viewer">Viewer Mode</option>
                <option value="responder">Responder Mode</option>
                <option value="admin">Administrator Mode</option>
              </select>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" defaultChecked className="w-4 h-4 text-purple-500 bg-gray-800 border-purple-500/30 rounded" />
                <span className="text-gray-300">Show Grid Overlay</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="w-4 h-4 text-purple-500 bg-gray-800 border-purple-500/30 rounded" />
                <span className="text-gray-300">Auto-acknowledge Normal</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;

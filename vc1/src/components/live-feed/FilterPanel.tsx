
import React, { useState } from 'react';
import { ArrowLeft, Search, Download, FileText, Filter } from 'lucide-react';
import { Alert, FilterOptions } from '@/types/live-feed';

interface FilterPanelProps {
  alerts: Alert[];
  onAlertSelect: (alert: Alert) => void;
  onBack: () => void;
}

const FilterPanel: React.FC<FilterPanelProps> = ({ alerts, onAlertSelect, onBack }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<FilterOptions>({
    type: [],
    severity: [],
    timeRange: {
      start: new Date(Date.now() - 24 * 60 * 60 * 1000), // 24 hours ago
      end: new Date()
    },
    acknowledgementStatus: 'all'
  });

  const alertTypes = ['Fire Detection', 'Weapon Detected', 'Intrusion Alert', 'Crowd Anomaly', 'Vehicle Violation'];
  const severityOptions: ('normal' | 'critical')[] = ['normal', 'critical'];

  const filteredAlerts = alerts.filter(alert => {
    // Search filter
    if (searchQuery && !alert.type.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !alert.description.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }

    // Type filter
    if (filters.type.length > 0 && !filters.type.includes(alert.type)) {
      return false;
    }

    // Severity filter
    if (filters.severity.length > 0 && !filters.severity.includes(alert.severity)) {
      return false;
    }

    // Acknowledgement filter
    if (filters.acknowledgementStatus === 'acknowledged' && !alert.acknowledged) {
      return false;
    }
    if (filters.acknowledgementStatus === 'unacknowledged' && alert.acknowledged) {
      return false;
    }

    return true;
  });

  const toggleTypeFilter = (type: string) => {
    setFilters(prev => ({
      ...prev,
      type: prev.type.includes(type)
        ? prev.type.filter(t => t !== type)
        : [...prev.type, type]
    }));
  };

  const toggleSeverityFilter = (severity: 'normal' | 'critical') => {
    setFilters(prev => ({
      ...prev,
      severity: prev.severity.includes(severity)
        ? prev.severity.filter(s => s !== severity)
        : [...prev.severity, severity]
    }));
  };

  const exportAsCSV = () => {
    const csvContent = [
      ['Alert ID', 'Timestamp', 'Type', 'Severity', 'Location', 'Description', 'Acknowledged'],
      ...filteredAlerts.map(alert => [
        alert.id,
        alert.timestamp.toISOString(),
        alert.type,
        alert.severity,
        alert.location || '',
        alert.description,
        alert.acknowledged ? 'Yes' : 'No'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `alerts_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Filter Sidebar */}
      <div className="lg:col-span-1 bg-black/50 border border-purple-500/30 rounded-lg backdrop-blur-lg p-6">
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={onBack}
            className="p-2 text-purple-400 hover:text-purple-300 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h3 className="text-white font-mono text-lg">FILTERS</h3>
        </div>

        {/* Search */}
        <div className="mb-6">
          <label className="block text-purple-400 text-sm font-mono mb-2">Search</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search alerts..."
              className="w-full pl-10 pr-3 py-2 bg-gray-800/50 border border-purple-500/30 rounded text-white placeholder-gray-400 focus:border-purple-400 focus:outline-none"
            />
          </div>
        </div>

        {/* Alert Types */}
        <div className="mb-6">
          <label className="block text-purple-400 text-sm font-mono mb-3">Alert Types</label>
          <div className="space-y-2">
            {alertTypes.map(type => (
              <label key={type} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.type.includes(type)}
                  onChange={() => toggleTypeFilter(type)}
                  className="w-4 h-4 text-purple-500 bg-gray-800 border-purple-500/30 rounded focus:ring-purple-500 focus:ring-2"
                />
                <span className="text-gray-300 text-sm">{type}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Severity */}
        <div className="mb-6">
          <label className="block text-purple-400 text-sm font-mono mb-3">Severity</label>
          <div className="space-y-2">
            {severityOptions.map(severity => (
              <label key={severity} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={filters.severity.includes(severity)}
                  onChange={() => toggleSeverityFilter(severity)}
                  className="w-4 h-4 text-purple-500 bg-gray-800 border-purple-500/30 rounded focus:ring-purple-500 focus:ring-2"
                />
                <span className={`text-sm capitalize ${
                  severity === 'critical' ? 'text-red-400' : 'text-green-400'
                }`}>
                  {severity}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Acknowledgement Status */}
        <div className="mb-6">
          <label className="block text-purple-400 text-sm font-mono mb-3">Status</label>
          <select
            value={filters.acknowledgementStatus}
            onChange={(e) => setFilters(prev => ({ ...prev, acknowledgementStatus: e.target.value as any }))}
            className="w-full p-2 bg-gray-800/50 border border-purple-500/30 rounded text-white focus:border-purple-400 focus:outline-none"
          >
            <option value="all">All Alerts</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="unacknowledged">Unacknowledged</option>
          </select>
        </div>

        {/* Export Buttons */}
        <div className="space-y-3">
          <button
            onClick={exportAsCSV}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-500/20 border border-green-500/30 rounded text-green-400 hover:bg-green-500/30 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
          <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-orange-500/20 border border-orange-500/30 rounded text-orange-400 hover:bg-orange-500/30 transition-colors">
            <FileText className="w-4 h-4" />
            Export PDF
          </button>
        </div>
      </div>

      {/* Results List */}
      <div className="lg:col-span-3 bg-black/50 border border-purple-500/30 rounded-lg backdrop-blur-lg">
        {/* Results Header */}
        <div className="border-b border-purple-500/30 p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-white font-mono text-lg">SEARCH RESULTS</h3>
            <span className="text-purple-400 font-mono text-sm">
              {filteredAlerts.length} alerts found
            </span>
          </div>
        </div>

        {/* Results Grid */}
        <div className="p-4 h-[calc(100%-80px)] overflow-y-auto">
          <div className="grid gap-4">
            {filteredAlerts.map((alert, index) => (
              <div
                key={alert.id}
                onClick={() => onAlertSelect(alert)}
                className={`border rounded-lg p-4 cursor-pointer transition-all hover:scale-[1.01] ${
                  alert.severity === 'critical'
                    ? 'border-red-500/30 bg-red-500/5 hover:border-red-500/50'
                    : 'border-green-500/30 bg-green-500/5 hover:border-green-500/50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-2 py-1 text-xs font-mono rounded ${
                        alert.severity === 'critical'
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                          : 'bg-green-500/20 text-green-400 border border-green-500/30'
                      }`}>
                        {alert.id}
                      </span>
                      <span className="text-gray-400 text-sm">
                        {alert.timestamp.toLocaleString()}
                      </span>
                    </div>
                    <h4 className="text-white font-semibold mb-1">{alert.type}</h4>
                    {alert.location && (
                      <p className="text-cyan-400 text-sm mb-1">{alert.location}</p>
                    )}
                    <p className="text-gray-300 text-sm">{alert.description}</p>
                  </div>
                  
                  <div className="ml-4 bg-gray-800/50 w-16 h-12 rounded border border-gray-600/30 flex items-center justify-center">
                    <span className="text-gray-400 text-xs">CLIP</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterPanel;

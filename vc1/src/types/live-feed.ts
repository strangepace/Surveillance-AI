
export interface Alert {
  id: string;
  timestamp: Date;
  type: string;
  severity: 'normal' | 'critical';
  location?: string;
  description: string;
  acknowledged: boolean;
  clipUrl?: string;
}

export interface FilterOptions {
  type: string[];
  severity: ('normal' | 'critical')[];
  timeRange: {
    start: Date;
    end: Date;
  };
  acknowledgementStatus: 'all' | 'acknowledged' | 'unacknowledged';
}

export interface DetectionSettings {
  fire: boolean;
  weapon: boolean;
  intrusion: boolean;
  crowd: boolean;
  vehicle: boolean;
}

export interface ExportSettings {
  autoExportZip: boolean;
  autoExportCsv: boolean;
  autoExportPdf: boolean;
  defaultFormat: 'mp4' | 'avi' | 'mov';
}

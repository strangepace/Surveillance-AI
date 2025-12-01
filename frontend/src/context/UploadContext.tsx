import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

export type VideoMetadata = {
  duration: number; // seconds
  width: number;
  height: number;
  fps?: number | null;
  sizeBytes: number;
  resolution: string; // e.g., 1920×1080
};

export type AnalyzeModel = "clip" | "google";
export type AnalyzeMode =
  | "FullScan"
  | "FrameSkip"
  | "MotionFilter"
  | "TrackThenMatch"
  | "ActivityDetect";

interface UploadContextValue {
  file: File | null;
  metadata: VideoMetadata | null;
  setFileWithMetadata: (file: File, metadata: VideoMetadata) => void;

  // Analysis range
  analysisRange: [number, number]; // [startS, endS]
  setAnalysisRange: (range: [number, number]) => void;

  // M2 config state
  prompts: string[];
  model: AnalyzeModel;
  mode: AnalyzeMode | null;
  setPrompts: (prompts: string[]) => void;
  setModel: (model: AnalyzeModel) => void;
  setMode: (mode: AnalyzeMode | null) => void;

  // Job tracking
  jobId: string | null;
  setJobId: (id: string | null) => void;

  clear: () => void;
}

const UploadContext = createContext<UploadContextValue | undefined>(undefined);

const CONFIG_KEY = "surv-ai:m2-config";

export const UploadProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [file, setFile] = useState<File | null>(null);
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);
  const [analysisRange, setAnalysisRange] = useState<[number, number]>([0, 30]);

// Config state with session persistence
const [prompts, setPrompts] = useState<string[]>([]);
const [model, setModel] = useState<AnalyzeModel>("clip");
const [mode, setMode] = useState<AnalyzeMode | null>(null);
const [jobId, setJobId] = useState<string | null>(null);

  // Hydrate from sessionStorage once
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(CONFIG_KEY);
      if (raw) {
const parsed = JSON.parse(raw) as { prompts?: string[]; model?: AnalyzeModel; mode?: AnalyzeMode | null; jobId?: string | null };
if (Array.isArray(parsed.prompts)) setPrompts(parsed.prompts);
if (parsed.model === "clip" || parsed.model === "google") setModel(parsed.model);
if (
  parsed.mode === "FullScan" ||
  parsed.mode === "FrameSkip" ||
  parsed.mode === "MotionFilter" ||
  parsed.mode === "TrackThenMatch" ||
  parsed.mode === "ActivityDetect"
)
  setMode(parsed.mode);
if (typeof parsed.jobId === "string") setJobId(parsed.jobId);
      }
    } catch {}
  }, []);

  // Persist to sessionStorage when config changes
  useEffect(() => {
    try {
const payload = JSON.stringify({ prompts, model, mode, jobId });
sessionStorage.setItem(CONFIG_KEY, payload);
    } catch {}
  }, [prompts, model, mode, jobId]);

  const setFileWithMetadata = (f: File, m: VideoMetadata) => {
    setFile(f);
    setMetadata(m);
  };

const clear = () => {
  setFile(null);
  setMetadata(null);
  setPrompts([]);
  setModel("clip");
  setMode(null);
  setJobId(null);
  try { sessionStorage.removeItem(CONFIG_KEY); } catch {}
};

const value = useMemo(
  () => ({
    file,
    metadata,
    setFileWithMetadata,
    analysisRange,
    setAnalysisRange,
    prompts,
    model,
    mode,
    setPrompts,
    setModel,
    setMode,
    jobId,
    setJobId,
    clear,
  }),
  [file, metadata, analysisRange, prompts, model, mode, jobId]
);

  return <UploadContext.Provider value={value}>{children}</UploadContext.Provider>;
};

export const useUpload = () => {
  const ctx = useContext(UploadContext);
  if (!ctx) throw new Error("useUpload must be used within UploadProvider");
  return ctx;
};

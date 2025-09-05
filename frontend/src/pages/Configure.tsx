import React, { useMemo, useState } from "react";
import { SEOHead } from "@/components/SEO";
import flags from "@/lib/config";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useUpload, AnalyzeMode, AnalyzeModel } from "@/context/UploadContext";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Brain, Zap, Move, Link as LinkIcon, PersonStanding, X, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import PromptChipsInput from "@/components/PromptChipsInput";

const MODES: { key: AnalyzeMode; name: string; desc: string; Icon: React.ComponentType<any> }[] = [
  { key: "FullScan", name: "FullScan", desc: "Deep scan of every frame", Icon: Brain },
  { key: "FrameSkip", name: "FrameSkip", desc: "Faster, skips frames", Icon: Zap },
  { key: "MotionFilter", name: "MotionFilter", desc: "Scan only motion", Icon: Move },
  { key: "TrackThenMatch", name: "TrackThenMatch", desc: "Track → match", Icon: LinkIcon },
  { key: "ActivityDetect", name: "ActivityDetect", desc: "Detect suspicious behavior", Icon: PersonStanding },
];

const Configure: React.FC = () => {
  const navigate = useNavigate();
  const { file, prompts, setPrompts, mode, setMode, model, setModel, setJobId } = useUpload();

  const [submitting, setSubmitting] = useState(false);

  const gradientStyle = useMemo(
    () => ({
      background:
        "linear-gradient(135deg, hsl(var(--gradient-upload-from)) 0%, hsl(var(--gradient-upload-to)) 100%)",
    }),
    []
  );

  const validate = () => {
    if (!file) {
      toast.error("No file selected", { description: "Please upload a video in M1 before configuring." });
      return false;
    }
    if (!prompts || prompts.length === 0) {
      toast.error("Add at least one prompt", { description: "Enter keywords separated by commas." });
      return false;
    }
    if (!mode) {
      toast.error("Select a detection mode", { description: "Choose one mode to continue." });
      return false;
    }
    return true;
  };

  const onSubmit = async () => {
    if (!validate()) return;
    try {
      setSubmitting(true);
      const fd = new FormData();
      fd.append("file", file as File);
      fd.append("prompts", (prompts || []).join(", "));
      fd.append("model", (model || "clip") as AnalyzeModel);
      fd.append("mode", mode as AnalyzeMode);

      const resp = await api.apiFetch<any>("/analyze", { method: "POST", body: fd, timeoutMs: 30000 });
      if (resp?.error_type) {
        throw new Error(`${resp.error_type}: ${resp?.message || "Unknown error"}`);
      }
      const id = typeof resp?.jobId === "string" ? resp.jobId : (typeof resp?.video_id === "string" ? resp.video_id : null);
      toast.success("Analysis started", { description: "Redirecting to progress…" });
      if (id) {
        setJobId(id);
        navigate(`/progress?jobId=${encodeURIComponent(id)}`);
      } else {
        // If backend didn't return a jobId, stay on configure with error
        throw new Error("No jobId returned from backend");
      }
    } catch (e: any) {
      toast.error("Failed to start analysis", { description: e?.message ?? "Please try again." });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen" style={gradientStyle}>
      <SEOHead
        title="Configure Detection – Surveillance AI"
        description="Enter prompts and select detection mode for AI analysis."
        canonical={typeof window !== "undefined" ? window.location.origin + "/configure" : "/configure"}
      />

      <header className="container pt-8 pb-4">
        <div className="flex items-center justify-between">
          <div className="text-xl font-semibold tracking-tight">Surveillance AI</div>
          <div className="text-sm text-muted-foreground">M2 • Configure</div>
        </div>
      </header>

      <main className="container pb-12">
        <h1 className="sr-only">Configure Detection – Surveillance AI</h1>
        <Card className={cn("mx-auto max-w-4xl rounded-2xl shadow-lg border bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/70")}> 
          <CardHeader>
            <CardTitle className="text-2xl">Prompts, Mode & Model</CardTitle>
            <CardDescription>Define what to look for and how to analyze.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              {/* Left column: Prompts + Model */}
              <section className="lg:col-span-3">
                <PromptChipsInput
                  label="Prompts"
                  placeholder="e.g., red car, person with backpack"
                  helper="Use commas to create multiple prompts. Double-click a chip to edit."
                />

                <div className="mt-6">
                  <div className="flex items-center gap-2 mb-2">
                    <label className="block text-sm font-medium">Model</label>
                    {flags.enableExperimentalGoogleModel && model === "google" && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="text-xs inline-flex items-center gap-1 text-muted-foreground">
                            🧪 Experimental
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>
                          Google AI is experimental — accuracy and speed may vary.
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </div>
                  <Select value={model} onValueChange={(v) => setModel(v as AnalyzeModel)}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Choose a model" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectLabel>Available Models</SelectLabel>
                        <SelectItem value="clip">CLIP (Default)</SelectItem>
                        {flags.enableExperimentalGoogleModel && (
                          <SelectItem value="google">Google AI 🧪</SelectItem>
                        )}
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </div>
              </section>

              {/* Right column: Modes */}
              <section className="lg:col-span-2">
                <label className="block text-sm font-medium mb-2">Detection Mode</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {MODES.map(({ key, name, desc, Icon }) => {
                    const selected = mode === key;
                    return (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setMode(key)}
                        className={cn(
                          "text-left rounded-lg border p-3 bg-background transition-colors",
                          selected ? "border-primary bg-primary/5" : "hover:bg-muted"
                        )}
                        aria-pressed={selected}
                      >
                        <div className="flex items-center gap-2">
                          <Icon className="h-4 w-4" />
                          <div className="font-medium text-sm">{name}</div>
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">{desc}</div>
                      </button>
                    );
                  })}
                </div>
                {!mode && (
                  <div className="mt-2 text-xs text-muted-foreground flex items-center gap-1">
                    <Info className="h-3.5 w-3.5" /> Choose one mode to continue
                  </div>
                )}
              </section>
            </div>

            <div className="mt-8 flex justify-between">
              <div className="text-xs text-muted-foreground">
                Ensure your prompts are precise for best results.
              </div>
              <Button size="lg" onClick={onSubmit} disabled={submitting || !(file && (prompts?.length ?? 0) > 0 && mode)}>
                {submitting ? "Starting…" : "Start analysis"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default Configure;

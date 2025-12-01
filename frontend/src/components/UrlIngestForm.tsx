import React, { useState, useCallback, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Loader2, ExternalLink, AlertTriangle, X, RefreshCw } from "lucide-react";
import { VideoRangeSelector } from "@/components/VideoRangeSelector";
import { formatHMS, parseHMS } from "@/lib/time";
import { FormatOption } from "@/lib/formatUtils";

interface UrlIngestFormProps {
  onIngestComplete: (data: {
    media_id: string;
    title: string;
    duration: number;
    original_url: string;
    window: {
      start: string;
      end: string;
      offsetSeconds: number;
    };
  }) => void;
  onError: (error: string) => void;
  onRangeChange?: (range: [number, number]) => void;
}

interface UrlIngestRequest {
  url: string;
  start?: string;
  end?: string;
  rights_confirmed: boolean;
  format_id?: string;
}

interface UrlIngestResponse {
  media_id: string;
  title: string;
  duration: number;
  original_url: string;
  window: {
    start: string;
    end: string;
    offsetSeconds: number;
  };
}

const UrlIngestForm: React.FC<UrlIngestFormProps> = ({ onIngestComplete, onError, onRangeChange }) => {
  const [formData, setFormData] = useState<UrlIngestRequest>({
    url: "",
    start: "",
    end: "",
    rights_confirmed: false,
    format_id: "auto"
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingFormats, setIsLoadingFormats] = useState(false);
  const [videoMetadata, setVideoMetadata] = useState<{ duration: number; title?: string; thumbnailUrl?: string; channel?: string } | null>(null);
  const [analysisRange, setAnalysisRange] = useState<[number, number]>([0, 30]);
  const [formatOptions, setFormatOptions] = useState<FormatOption[]>([]);
  const [formatsError, setFormatsError] = useState<string | null>(null);
  const [fetchedMedia, setFetchedMedia] = useState<{ media_id: string; title: string; duration_s: number; format_id?: string } | null>(null);

  const handleInputChange = useCallback((field: keyof UrlIngestRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const clearUrl = useCallback(() => {
    setFormData(prev => ({ ...prev, url: "" }));
    setFormatOptions([]);
    setFormatsError(null);
  }, []);

  // Probe via /media/fetch to get title/thumbs/duration/formats
  const probeUrl = useCallback(async (url: string) => {
    if (!url.trim()) {
      setFormatOptions([]);
      setFormatsError(null);
      setVideoMetadata(null);
      return;
    }

    setIsLoadingFormats(true);
    setFormatsError(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/media/fetch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: "youtube", url, action: "probe" })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = err?.detail || `HTTP ${res.status}`;
        throw new Error(detail);
      }
      const data = await res.json();
      // thumbnail: pick highest area
      let thumb = undefined as string | undefined;
      if (Array.isArray(data.thumbs) && data.thumbs.length > 0) {
        const best = [...data.thumbs].sort((a: any, b: any) => ((b.w||0)*(b.h||0)) - ((a.w||0)*(a.h||0)))[0];
        thumb = best?.url;
      }
      setVideoMetadata({ duration: data.duration_s || 0, title: data.title, thumbnailUrl: thumb, channel: data.channel });
      // formats to options
      const options: FormatOption[] = [
        {
          value: "auto",
          label: "Auto (Recommended)",
          description: "Best quality under size limits • H.264/AAC"
        },
        ...(data.formats || []).map((f: any) => ({
          value: f.format_id,
          label: f.label,
          description: `${f.vcodec}/${f.acodec} • ${typeof f.filesize_mb === 'number' ? `${f.filesize_mb} MB` : 'size unknown'}`
        }))
      ];
      setFormatOptions(options);
      // Set default to auto if not already set
      if (!formData.format_id) {
        setFormData(prev => ({ ...prev, format_id: "auto" }));
      }
    } catch (error) {
      console.error("Failed to fetch formats:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to fetch video formats";
      setFormatsError(errorMessage);
      setFormatOptions([]);
      // Specific toasts
      const msg = (error instanceof Error) ? error.message.toLowerCase() : "";
      if (msg.includes("age") || msg.includes("restricted")) toast.error("This video is age-restricted.");
      else if (msg.includes("private")) toast.error("This video is private.");
      else if (msg.includes("drm")) toast.error("DRM-protected video is not supported.");
      else toast.error(errorMessage);
    } finally {
      setIsLoadingFormats(false);
    }
  }, []);

  // Auto-probe when URL is pasted and rights are confirmed
  useEffect(() => {
    if (formData.url.trim() && formData.rights_confirmed) {
      const timeoutId = setTimeout(() => {
        probeUrl(formData.url);
      }, 500); // Debounce for 500ms

      return () => clearTimeout(timeoutId);
    }
  }, [formData.url, formData.rights_confirmed, probeUrl]);

  // Trigger probe on blur/enter
  const onUrlBlur = useCallback(() => {
    if (formData.url.trim() && formData.rights_confirmed) probeUrl(formData.url);
  }, [formData.url, formData.rights_confirmed, probeUrl]);
  const onUrlKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (formData.url.trim() && formData.rights_confirmed) probeUrl(formData.url);
    }
  }, [formData.url, formData.rights_confirmed, probeUrl]);

  const handleUrlSubmit = useCallback(async () => {
    if (!formData.url.trim()) {
      toast.error("Please enter a YouTube URL");
      return;
    }

    if (!formData.rights_confirmed) {
      toast.error("Please confirm you have rights to download this content");
      return;
    }

    setIsLoading(true);
    
    try {
      // Fetch video (download or reuse cached)
      const res = await fetch("http://127.0.0.1:8000/media/fetch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source: "youtube",
          url: formData.url,
          action: "fetch",
          format_id: formData.format_id === "auto" ? undefined : formData.format_id
        })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();

      // Store media_id etc for next step
      setFetchedMedia({ media_id: data.media_id, title: data.title || videoMetadata?.title || "", duration_s: data.duration_s || (videoMetadata?.duration ?? 0), format_id: data.format_id });

      // Notify parent (preserve legacy shape expected by Upload.tsx)
      const durationNum = data.duration_s || (videoMetadata?.duration ?? 0);
      onIngestComplete({
        media_id: data.media_id,
        title: data.title || "YouTube Video",
        duration: durationNum,
        original_url: data.file_url || "",
        window: {
          start: "00:00:00",
          end: formatHMS(durationNum || 0),
          offsetSeconds: 0
        }
      });

      // If not probed earlier, ensure we have duration/title displayed
      if (!videoMetadata) {
        setVideoMetadata({ duration: data.duration_s || 0, title: data.title, thumbnailUrl: undefined });
      }

      // Default analysis range to full duration if known
      const dur = videoMetadata?.duration || data.duration_s || 0;
      const nextRange: [number, number] = [0, dur > 0 ? dur : analysisRange[1]];
      setAnalysisRange(nextRange);
      onRangeChange?.(nextRange);

      toast.success(`${data.already_cached ? "Reused cached" : "Fetched"}: ${data.title || "video"}`);
      
    } catch (error) {
      console.error("URL ingestion error:", error);
      
      let errorMessage = "Failed to fetch video from YouTube";
      
      if (error instanceof Error) {
        if (error.message.includes("private") || error.message.includes("Private")) {
          errorMessage = "This video is private. Please use a public video.";
        } else if (error.message.includes("DRM") || error.message.includes("drm")) {
          errorMessage = "This video has DRM protection and cannot be downloaded.";
        } else if (error.message.includes("geo") || error.message.includes("region")) {
          errorMessage = "This video is not available in your region.";
        } else if (error.message.includes("age") || error.message.includes("restricted")) {
          errorMessage = "This video is age-restricted and cannot be downloaded.";
        } else if (error.message.includes("disabled")) {
          errorMessage = "URL ingestion is disabled. Please contact your administrator.";
        } else if (error.message.includes("size") || error.message.includes("duration")) {
          errorMessage = error.message;
        } else {
          errorMessage = error.message;
        }
      }
      
      onError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [formData, onIngestComplete, onError]);

  const canSubmit = formData.url.trim() && formData.rights_confirmed && !isLoading && 
    (formatOptions.length > 0 || formData.format_id === "auto");

  return (
    <div className="space-y-6">
      {/* URL Input */}
      <div className="space-y-2">
        <Label htmlFor="youtube-url">YouTube URL</Label>
        <div className="relative">
          <Input
            id="youtube-url"
            type="url"
            placeholder="https://www.youtube.com/watch?v=..."
            value={formData.url}
            onChange={(e) => handleInputChange("url", e.target.value)}
            onBlur={onUrlBlur}
            onKeyDown={onUrlKeyDown}
            disabled={isLoading}
            className="pr-10"
          />
          {formData.url && (
            <button
              type="button"
              onClick={clearUrl}
              disabled={isLoading}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Clear URL"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          Enter a public YouTube video URL. Private, age-restricted, or DRM-protected videos cannot be processed.
        </p>
      </div>

      {/* Rights Confirmation */}
      <div className="flex items-start gap-3">
        <Checkbox 
          id="rights-confirm" 
          checked={formData.rights_confirmed} 
          onCheckedChange={(checked) => handleInputChange("rights_confirmed", checked)}
          disabled={isLoading}
        />
        <div className="grid gap-1.5 text-sm">
          <Label htmlFor="rights-confirm" className="font-medium">
            I have rights to download and analyze this content
          </Label>
          <p className="text-xs text-muted-foreground">
            You must own the content or have explicit permission to download and analyze it.
          </p>
        </div>
      </div>

      {/* Format Selection */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="format">Video Format</Label>
          {formData.url.trim() && formData.rights_confirmed && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => probeUrl(formData.url)}
              disabled={isLoadingFormats}
              className="h-6 px-2 text-xs"
            >
              {isLoadingFormats ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <RefreshCw className="h-3 w-3" />
              )}
              Refresh
            </Button>
          )}
        </div>
        
        {isLoadingFormats ? (
          <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
            <span className="text-sm text-blue-700 dark:text-blue-300">
              Fetching available formats...
            </span>
          </div>
        ) : formatsError ? (
          <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <div className="flex-1">
              <p className="text-sm text-red-700 dark:text-red-300">
                Failed to fetch formats: {formatsError}
              </p>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => probeUrl(formData.url)}
                className="h-6 px-2 text-xs mt-1"
              >
                Retry
              </Button>
            </div>
          </div>
        ) : formatOptions.length > 0 ? (
          <Select 
            value={formData.format_id} 
            onValueChange={(value) => handleInputChange("format_id", value)}
            disabled={isLoading}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select format" />
            </SelectTrigger>
            <SelectContent>
              {formatOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  <div className="flex flex-col">
                    <span className="font-medium">{option.label}</span>
                    <span className="text-xs text-muted-foreground">{option.description}</span>
                    {option.warning && (
                      <span className="text-xs text-orange-600">{option.warning}</span>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : formData.url.trim() && formData.rights_confirmed ? (
          <div className="flex items-center gap-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <span className="text-sm text-yellow-700 dark:text-yellow-300">
              No formats available. You can still proceed with Auto selection.
            </span>
          </div>
        ) : (
          <div className="p-3 bg-gray-50 dark:bg-gray-900/20 border border-gray-200 dark:border-gray-800 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Enter a YouTube URL and confirm rights to see available formats.
            </p>
          </div>
        )}
      </div>

      {/* Video details (after probe) */}
      {videoMetadata && (
        <div className="space-y-4">
          <div className="flex gap-4 items-start">
            {videoMetadata.thumbnailUrl && (
              <img src={videoMetadata.thumbnailUrl} alt={videoMetadata.title || "thumbnail"} className="w-40 h-24 object-cover rounded" />
            )}
            <div className="space-y-1">
              <div className="text-sm font-medium">{videoMetadata.title || "Video"}</div>
              {videoMetadata.channel && <div className="text-xs text-muted-foreground">{videoMetadata.channel}</div>}
              <div className="text-xs text-green-600">Duration: {formatHMS(videoMetadata.duration)}</div>
            </div>
          </div>

          {/* Analysis Time Window (only after fetch) */}
          {fetchedMedia && (
            <div className="space-y-2">
              <Label>Analysis Time Window</Label>
              <VideoRangeSelector
                duration={videoMetadata.duration}
                value={analysisRange}
                onChange={(r) => { setAnalysisRange(r); onRangeChange?.(r); }}
                step={0.01}
              />
              <p className="text-xs text-muted-foreground">
                Select the portion of the video you want to analyze. This will be used for the analysis step.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Submit Button */
      }
      <div className="flex justify-end">
        {!fetchedMedia ? (
          <Button 
            onClick={handleUrlSubmit}
            disabled={!canSubmit}
            size="lg"
            className="min-w-[140px]"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Fetching...
              </>
            ) : (
              <>
                <ExternalLink className="mr-2 h-4 w-4" />
                Fetch Video
              </>
            )}
          </Button>
        ) : (
          <div className="text-sm text-muted-foreground">Ready to analyze (media_id: {fetchedMedia.media_id}). Use the main "Analyze Video" button.</div>
        )}
      </div>

      {/* Error Display */}
      {isLoading && (
        <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
          <span className="text-sm text-blue-700 dark:text-blue-300">
            Fetching video from YouTube...
          </span>
        </div>
      )}
    </div>
  );
};

export default UrlIngestForm;

import React, { useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Upload from "./pages/Upload";
import NotFound from "./pages/NotFound";
import Configure from "./pages/Configure";
import ProgressPage from "./pages/Progress";
import ResultsPage from "./pages/Results";
import LivePage from "./pages/Live";
import LiveAlertsPage from "./pages/LiveAlerts";
import LiveFiltersPage from "./pages/LiveFilters";
import LiveReviewPage from "./pages/LiveReview";
import Landing3D from "./pages/Landing3D";
import VerifyPage from "./pages/Verify";
import { UploadProvider } from "./context/UploadContext";
import { LiveProvider } from "./context/LiveStore";
import DevPanel from "@/components/DevPanel";
import ErrorBoundary from "@/components/ErrorBoundary";

const queryClient = new QueryClient();

const App = () => {
  useEffect(() => {
    const stored = localStorage.getItem("ui.highContrast");
    if (stored === "1") document.documentElement.classList.add("high-contrast");
    const onKey = (e: KeyboardEvent) => {
      if (e.altKey && (e.key === "h" || e.key === "H")) {
        document.documentElement.classList.toggle("high-contrast");
        const on = document.documentElement.classList.contains("high-contrast");
        localStorage.setItem("ui.highContrast", on ? "1" : "0");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <LiveProvider>
            <UploadProvider>
              <ErrorBoundary>
                <>
                  <Routes>
                    <Route path="/" element={<Landing3D />} />
                    <Route path="/upload" element={<Upload />} />
                    <Route path="/configure" element={<Configure />} />
                    <Route path="/progress" element={<ProgressPage />} />
                    <Route path="/results" element={<ResultsPage />} />
                    <Route path="/live" element={<LivePage />} />
                    <Route path="/live/alerts" element={<LiveAlertsPage />} />
                    <Route path="/live/filters" element={<LiveFiltersPage />} />
                    <Route path="/live/review/:id" element={<LiveReviewPage />} />
                    {import.meta.env.DEV && <Route path="/verify" element={<VerifyPage />} />}
                    {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                  {import.meta.env.DEV && <DevPanel />}
                </>
              </ErrorBoundary>
            </UploadProvider>
          </LiveProvider>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;

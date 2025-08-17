import React from "react";

type Props = { children: React.ReactNode };

type State = { hasError: boolean; error?: any };

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error: any) {
    return { hasError: true, error };
  }
  componentDidCatch(error: any, errorInfo: any) {
    console.error("App error boundary caught:", error, errorInfo);
  }
  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
    try { window.location.reload(); } catch {}
  };
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6">
          <div className="max-w-md w-full rounded-lg border bg-card p-6 text-center space-y-3 shadow">
            <h1 className="text-xl font-semibold">Something went wrong</h1>
            <p className="text-sm text-muted-foreground">An unexpected error occurred. You can try again or go back to the start.</p>
            <div className="flex items-center justify-center gap-2 pt-2">
              <button className="inline-flex items-center rounded-md border px-3 py-1.5 text-sm" onClick={this.handleRetry}>Retry</button>
              <a className="inline-flex items-center rounded-md border px-3 py-1.5 text-sm" href="/upload">Go to Upload</a>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children as any;
  }
}

export default ErrorBoundary;

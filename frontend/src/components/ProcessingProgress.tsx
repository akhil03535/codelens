import { useEffect, useState } from "react";

interface ProgressStep {
  name: string;
  status: "pending" | "active" | "complete" | "error";
  timestamp?: number;
}

interface ProcessingProgressProps {
  steps: ProgressStep[];
  currentProgress: number; // 0-100
  stage?: string;
  error?: string;
  onCancel?: () => void;
  onRetry?: () => void;
  startTime?: number;
}

export function ProcessingProgress({
  steps,
  currentProgress,
  stage,
  error,
  onCancel,
  onRetry,
  startTime,
}: ProcessingProgressProps) {
  const [eta, setEta] = useState<string>("");

  useEffect(() => {
    if (!startTime || currentProgress <= 0 || currentProgress >= 100) {
      setEta("");
      return;
    }
    
    const elapsed = (Date.now() - startTime) / 1000;
    const rate = currentProgress / elapsed;
    const remaining = (100 - currentProgress) / rate;
    
    if (remaining < 60) {
      setEta(`${Math.ceil(remaining)}s remaining`);
    } else {
      setEta(`${Math.ceil(remaining / 60)}m remaining`);
    }
  }, [currentProgress, startTime]);

  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">{stage || "Processing..."}</p>
            <p className="text-xs text-text-dim mt-1">Progress: {currentProgress}%</p>
          </div>
          {eta && <p className="text-xs text-text-dim">{eta}</p>}
        </div>
        <div className="h-2 bg-bg-3 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-accent to-accent/80 rounded-full transition-all duration-300"
            style={{ width: `${currentProgress}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {steps.map((step, idx) => (
          <div key={idx} className="flex items-center gap-3">
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold transition-colors ${
                step.status === "complete"
                  ? "bg-success/20 text-success"
                  : step.status === "active"
                  ? "bg-accent/20 text-accent animate-pulse"
                  : step.status === "error"
                  ? "bg-danger/20 text-danger"
                  : "bg-bg-3 text-text-dim"
              }`}
            >
              {step.status === "complete" ? "✓" : step.status === "error" ? "!" : idx + 1}
            </div>
            <span className={`text-sm ${step.status === "active" ? "font-medium" : ""}`}>
              {step.name}
            </span>
          </div>
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-danger/10 border border-danger/20 rounded-lg p-3">
          <p className="text-sm text-danger">{error}</p>
        </div>
      )}

      {/* Action Buttons */}
      {error && (
        <div className="flex gap-2">
          {onRetry && (
            <button onClick={onRetry} className="btn-primary flex-1 text-sm py-2">
              Retry Upload
            </button>
          )}
          {onCancel && (
            <button onClick={onCancel} className="btn-ghost flex-1 text-sm py-2">
              Cancel
            </button>
          )}
        </div>
      )}
      {!error && onCancel && (
        <button onClick={onCancel} className="btn-ghost w-full text-sm py-2">
          Cancel Upload
        </button>
      )}
    </div>
  );
}

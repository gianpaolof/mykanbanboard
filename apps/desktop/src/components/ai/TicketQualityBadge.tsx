// components/ai/TicketQualityBadge.tsx
import { useState, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Award, Loader2, AlertCircle, X, CheckCircle, Target, FileText } from 'lucide-react';
import { cn } from '../../lib/utils';

// ===========================================
// TYPES
// ===========================================

interface QualityScores {
  clarity_score: number;
  completeness_score: number;
  actionability_score: number;
  feedback: string;
  overall_score: number;
}

interface TicketQualityBadgeProps {
  ticketTitle: string;
  ticketDescription: string;
  priority: string;
  effort: string;
  labels: string[];
  className?: string;
}

// ===========================================
// CONSTANTS
// ===========================================

const AGENT_API_BASE = 'http://localhost:8765/api';

const getScoreColor = (score: number): string => {
  if (score >= 7) return 'text-green-400';
  if (score >= 5) return 'text-yellow-400';
  return 'text-red-400';
};

const getScoreBgColor = (score: number): string => {
  if (score >= 7) return 'bg-green-500/20 border-green-500/30';
  if (score >= 5) return 'bg-yellow-500/20 border-yellow-500/30';
  return 'bg-red-500/20 border-red-500/30';
};

const getOverallLabel = (score: number): string => {
  if (score >= 8) return 'Excellent';
  if (score >= 6) return 'Good';
  if (score >= 4) return 'Fair';
  return 'Needs Improvement';
};

// ===========================================
// SCORE ITEM COMPONENT
// ===========================================

interface ScoreItemProps {
  icon: typeof CheckCircle;
  label: string;
  score: number;
}

const ScoreItem = memo(function ScoreItem({ icon: Icon, label, score }: ScoreItemProps) {
  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-zinc-400" />
        <span className="text-sm text-zinc-300">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-24 h-2 bg-zinc-800 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${score * 10}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className={cn(
              'h-full rounded-full',
              score >= 7 ? 'bg-green-500' : score >= 5 ? 'bg-yellow-500' : 'bg-red-500'
            )}
          />
        </div>
        <span className={cn('text-sm font-medium w-6 text-right', getScoreColor(score))}>
          {score}
        </span>
      </div>
    </div>
  );
});

// ===========================================
// TICKET QUALITY BADGE
// ===========================================

export const TicketQualityBadge = memo(function TicketQualityBadge({
  ticketTitle,
  ticketDescription,
  priority,
  effort,
  labels,
  className,
}: TicketQualityBadgeProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [scores, setScores] = useState<QualityScores | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchQualityScore = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${AGENT_API_BASE}/agent/judge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: ticketTitle,
          description: ticketDescription,
          priority,
          effort,
          labels,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to judge ticket: ${response.status}`);
      }

      const data = await response.json();
      setScores(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze quality');
    } finally {
      setIsLoading(false);
    }
  }, [ticketTitle, ticketDescription, priority, effort, labels]);

  const handleClick = useCallback(() => {
    if (!isOpen && !scores && !isLoading) {
      fetchQualityScore();
    }
    setIsOpen((prev) => !prev);
  }, [isOpen, scores, isLoading, fetchQualityScore]);

  const handleClose = useCallback(() => {
    setIsOpen(false);
  }, []);

  const handleRetry = useCallback(() => {
    fetchQualityScore();
  }, [fetchQualityScore]);

  return (
    <div className={cn('relative', className)}>
      {/* Trigger Button */}
      <button
        onClick={handleClick}
        disabled={isLoading}
        className={cn(
          'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium',
          'border transition-all',
          scores
            ? getScoreBgColor(scores.overall_score)
            : 'bg-zinc-800/50 border-zinc-700 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-300',
          isLoading && 'opacity-50 cursor-not-allowed'
        )}
        title="Check ticket quality"
      >
        {isLoading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Award className="w-3.5 h-3.5" />
        )}
        {scores ? (
          <span className={getScoreColor(scores.overall_score)}>
            {scores.overall_score.toFixed(1)}
          </span>
        ) : (
          <span>Quality</span>
        )}
      </button>

      {/* Popover */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-40"
              onClick={handleClose}
            />

            {/* Popover Content */}
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className={cn(
                'absolute top-full right-0 mt-2 z-50',
                'w-80 p-4 rounded-xl',
                'bg-zinc-900 border border-zinc-800',
                'shadow-xl shadow-black/50'
              )}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-indigo-400" />
                  <h3 className="font-semibold text-white">Ticket Quality</h3>
                </div>
                <button
                  onClick={handleClose}
                  className="p-1 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Content */}
              {isLoading ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mb-3" />
                  <p className="text-sm text-zinc-400">Analyzing ticket quality...</p>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-6 text-center">
                  <AlertCircle className="w-8 h-8 text-red-400 mb-3" />
                  <p className="text-sm text-zinc-400 mb-4">{error}</p>
                  <button
                    onClick={handleRetry}
                    className="px-4 py-2 text-sm bg-indigo-500 hover:bg-indigo-400 rounded-lg text-white transition-colors"
                  >
                    Retry
                  </button>
                </div>
              ) : scores ? (
                <div className="space-y-4">
                  {/* Overall Score */}
                  <div
                    className={cn(
                      'p-3 rounded-lg border text-center',
                      getScoreBgColor(scores.overall_score)
                    )}
                  >
                    <div className={cn('text-3xl font-bold', getScoreColor(scores.overall_score))}>
                      {scores.overall_score.toFixed(1)}
                    </div>
                    <div className="text-xs text-zinc-400 mt-1">
                      {getOverallLabel(scores.overall_score)}
                    </div>
                  </div>

                  {/* Individual Scores */}
                  <div className="divide-y divide-zinc-800">
                    <ScoreItem
                      icon={CheckCircle}
                      label="Clarity"
                      score={scores.clarity_score}
                    />
                    <ScoreItem
                      icon={FileText}
                      label="Completeness"
                      score={scores.completeness_score}
                    />
                    <ScoreItem
                      icon={Target}
                      label="Actionability"
                      score={scores.actionability_score}
                    />
                  </div>

                  {/* Feedback */}
                  {scores.feedback && (
                    <div className="pt-3 border-t border-zinc-800">
                      <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 mb-2">
                        Suggestions
                      </h4>
                      <p className="text-sm text-zinc-400 leading-relaxed">
                        {scores.feedback}
                      </p>
                    </div>
                  )}

                  {/* Refresh Button */}
                  <button
                    onClick={handleRetry}
                    className="w-full px-3 py-2 text-sm text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
                  >
                    Refresh Score
                  </button>
                </div>
              ) : null}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
});

export default TicketQualityBadge;

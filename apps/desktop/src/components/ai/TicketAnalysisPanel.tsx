// components/ai/TicketAnalysisPanel.tsx
import { useState, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Loader2,
  AlertCircle,
  X,
  Lightbulb,
  GitBranch,
  Target,
  ChevronDown,
  ChevronUp,
  RefreshCw,
} from 'lucide-react';
import { cn } from '../../lib/utils';

// ===========================================
// TYPES
// ===========================================

interface AnalysisResult {
  context_summary: string;
  key_themes: string[];
  patterns: string[];
  dependencies: string;
  insights: string;
  recommendations: string;
  complexity: 'low' | 'medium' | 'high';
}

interface TicketAnalysisPanelProps {
  ticketTitle: string;
  ticketDescription: string;
  className?: string;
}

// ===========================================
// CONSTANTS
// ===========================================

const AGENT_API_BASE = 'http://localhost:8765/api';

const COMPLEXITY_CONFIG = {
  low: {
    label: 'Low Complexity',
    color: 'text-green-400',
    bg: 'bg-green-500/20 border-green-500/30',
  },
  medium: {
    label: 'Medium Complexity',
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/20 border-yellow-500/30',
  },
  high: {
    label: 'High Complexity',
    color: 'text-red-400',
    bg: 'bg-red-500/20 border-red-500/30',
  },
};

// ===========================================
// SKELETON COMPONENT
// ===========================================

const AnalysisSkeleton = memo(function AnalysisSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="space-y-2">
        <div className="h-4 bg-zinc-800 rounded w-1/4" />
        <div className="h-20 bg-zinc-800 rounded" />
      </div>
      <div className="space-y-2">
        <div className="h-4 bg-zinc-800 rounded w-1/3" />
        <div className="flex gap-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-6 bg-zinc-800 rounded w-16" />
          ))}
        </div>
      </div>
      <div className="space-y-2">
        <div className="h-4 bg-zinc-800 rounded w-1/4" />
        <div className="h-16 bg-zinc-800 rounded" />
      </div>
    </div>
  );
});

// ===========================================
// SECTION COMPONENT
// ===========================================

interface SectionProps {
  title: string;
  icon: typeof Lightbulb;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}

const Section = memo(function Section({
  title,
  icon: Icon,
  children,
  defaultExpanded = true,
}: SectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="border border-zinc-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded((prev) => !prev)}
        className="w-full flex items-center justify-between p-3 bg-zinc-900/50 hover:bg-zinc-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-indigo-400" />
          <span className="text-sm font-medium text-white">{title}</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-zinc-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-zinc-500" />
        )}
      </button>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-3 bg-zinc-950/50">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

// ===========================================
// TICKET ANALYSIS PANEL
// ===========================================

export const TicketAnalysisPanel = memo(function TicketAnalysisPanel({
  ticketTitle,
  ticketDescription,
  className,
}: TicketAnalysisPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${AGENT_API_BASE}/agent/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: ticketTitle,
          description: ticketDescription,
        }),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.status}`);
      }

      const data = await response.json();

      // Parse patterns if they're a string
      let patterns = data.patterns;
      if (typeof patterns === 'string') {
        try {
          patterns = JSON.parse(patterns);
        } catch {
          patterns = patterns.split(',').map((p: string) => p.trim());
        }
      }

      // Parse key_themes if they're a string
      let keyThemes = data.key_themes;
      if (typeof keyThemes === 'string') {
        keyThemes = keyThemes.split(',').map((t: string) => t.trim());
      }

      setResult({
        ...data,
        patterns: Array.isArray(patterns) ? patterns : [],
        key_themes: Array.isArray(keyThemes) ? keyThemes : [],
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsLoading(false);
    }
  }, [ticketTitle, ticketDescription]);

  const handleAnalyze = useCallback(() => {
    setIsOpen(true);
    if (!result && !isLoading) {
      fetchAnalysis();
    }
  }, [result, isLoading, fetchAnalysis]);

  const handleClose = useCallback(() => {
    setIsOpen(false);
  }, []);

  const handleRetry = useCallback(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  const complexityConfig = result?.complexity
    ? COMPLEXITY_CONFIG[result.complexity]
    : COMPLEXITY_CONFIG.medium;

  return (
    <div className={className}>
      {/* Trigger Button */}
      <button
        onClick={handleAnalyze}
        disabled={isLoading}
        className={cn(
          'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium',
          'bg-zinc-800 text-zinc-100 border border-zinc-700',
          'hover:bg-zinc-700 transition-colors',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Brain className="w-4 h-4" />
            Deep Analyze
          </>
        )}
      </button>

      {/* Analysis Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="mt-4 overflow-hidden"
          >
            <div
              className={cn(
                'p-4 rounded-xl border',
                'bg-gradient-to-br from-zinc-900/80 to-zinc-950/80',
                'border-indigo-500/20 backdrop-blur-sm'
              )}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-indigo-400" />
                  <h3 className="font-semibold text-white">Deep Analysis</h3>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleRetry}
                    disabled={isLoading}
                    className="p-1.5 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors disabled:opacity-50"
                    title="Refresh analysis"
                  >
                    <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
                  </button>
                  <button
                    onClick={handleClose}
                    className="p-1.5 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Content */}
              {isLoading ? (
                <AnalysisSkeleton />
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <AlertCircle className="w-10 h-10 text-red-400 mb-3" />
                  <p className="text-sm text-zinc-400 mb-4">{error}</p>
                  <button
                    onClick={handleRetry}
                    className="px-4 py-2 text-sm bg-indigo-500 hover:bg-indigo-400 rounded-lg text-white transition-colors"
                  >
                    Retry Analysis
                  </button>
                </div>
              ) : result ? (
                <div className="space-y-3">
                  {/* Complexity Badge */}
                  <div
                    className={cn(
                      'inline-flex items-center gap-2 px-3 py-1.5 rounded-full border',
                      complexityConfig.bg
                    )}
                  >
                    <Target className={cn('w-4 h-4', complexityConfig.color)} />
                    <span className={cn('text-sm font-medium', complexityConfig.color)}>
                      {complexityConfig.label}
                    </span>
                  </div>

                  {/* Context Summary */}
                  <Section title="Context Summary" icon={Lightbulb}>
                    <p className="text-sm text-zinc-300 leading-relaxed">
                      {result.context_summary || 'No context available'}
                    </p>
                  </Section>

                  {/* Patterns/Themes */}
                  {(result.patterns?.length > 0 || result.key_themes?.length > 0) && (
                    <Section title="Identified Patterns" icon={GitBranch}>
                      <div className="flex flex-wrap gap-2">
                        {[...(result.patterns || []), ...(result.key_themes || [])].map(
                          (pattern, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 text-xs rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30"
                            >
                              {pattern}
                            </span>
                          )
                        )}
                      </div>
                    </Section>
                  )}

                  {/* Insights */}
                  {result.insights && (
                    <Section title="Key Insights" icon={Lightbulb}>
                      <div className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">
                        {result.insights}
                      </div>
                    </Section>
                  )}

                  {/* Recommendations */}
                  {result.recommendations && (
                    <Section title="Recommendations" icon={Target} defaultExpanded={false}>
                      <div className="text-sm text-zinc-300 leading-relaxed whitespace-pre-wrap">
                        {result.recommendations}
                      </div>
                    </Section>
                  )}

                  {/* Dependencies */}
                  {result.dependencies && (
                    <Section title="Dependencies" icon={GitBranch} defaultExpanded={false}>
                      <p className="text-sm text-zinc-400 leading-relaxed">
                        {result.dependencies}
                      </p>
                    </Section>
                  )}
                </div>
              ) : null}

              {/* Footer Note */}
              <div className="mt-4 pt-3 border-t border-zinc-800">
                <p className="text-xs text-zinc-500 text-center">
                  Analysis uses multi-hop reasoning for deeper insights
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

export default TicketAnalysisPanel;

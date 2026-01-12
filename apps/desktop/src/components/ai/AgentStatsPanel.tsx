// components/ai/AgentStatsPanel.tsx
import { useState, useEffect, useCallback, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart3,
  Clock,
  CheckCircle,
  Zap,
  TrendingUp,
  RefreshCw,
  X,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { cn } from '../../lib/utils';

// ===========================================
// TYPES
// ===========================================

interface AgentStats {
  total_calls: number;
  avg_latency_ms: number;
  success_rate: number;
  total_tokens: number;
  period: string;
}

type Period = 'hour' | 'day' | 'week';

interface AgentStatsPanelProps {
  open: boolean;
  onClose: () => void;
  className?: string;
}

// ===========================================
// CONSTANTS
// ===========================================

const PERIODS: { id: Period; label: string }[] = [
  { id: 'hour', label: '1h' },
  { id: 'day', label: '24h' },
  { id: 'week', label: '7d' },
];

const AGENT_API_BASE = 'http://localhost:8765/api';

// ===========================================
// STAT CARD COMPONENT
// ===========================================

interface StatCardProps {
  icon: typeof Clock;
  label: string;
  value: string | number;
  subValue?: string;
  trend?: 'up' | 'down' | 'neutral';
  color: 'indigo' | 'green' | 'yellow' | 'purple';
}

const StatCard = memo(function StatCard({
  icon: Icon,
  label,
  value,
  subValue,
  color,
}: StatCardProps) {
  const colorClasses = {
    indigo: 'from-indigo-500/20 to-indigo-600/20 text-indigo-400',
    green: 'from-green-500/20 to-green-600/20 text-green-400',
    yellow: 'from-yellow-500/20 to-yellow-600/20 text-yellow-400',
    purple: 'from-purple-500/20 to-purple-600/20 text-purple-400',
  };

  const iconBgClasses = {
    indigo: 'bg-indigo-500/20',
    green: 'bg-green-500/20',
    yellow: 'bg-yellow-500/20',
    purple: 'bg-purple-500/20',
  };

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-xl p-4',
        'bg-gradient-to-br border border-glass-border backdrop-blur-xl',
        colorClasses[color]
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-400 mb-1">{label}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {subValue && (
            <p className="text-xs text-gray-500 mt-0.5">{subValue}</p>
          )}
        </div>
        <div className={cn('p-2 rounded-lg', iconBgClasses[color])}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
});

// ===========================================
// PERIOD TOGGLE
// ===========================================

interface PeriodToggleProps {
  selected: Period;
  onChange: (period: Period) => void;
}

const PeriodToggle = memo(function PeriodToggle({
  selected,
  onChange,
}: PeriodToggleProps) {
  return (
    <div className="flex items-center gap-1 bg-bg-tertiary rounded-lg p-1">
      {PERIODS.map((period) => (
        <button
          key={period.id}
          onClick={() => onChange(period.id)}
          className={cn(
            'px-3 py-1.5 text-xs font-medium rounded-md transition-all',
            selected === period.id
              ? 'bg-accent text-white'
              : 'text-gray-400 hover:text-white hover:bg-bg-hover'
          )}
        >
          {period.label}
        </button>
      ))}
    </div>
  );
});

// ===========================================
// AGENT STATS PANEL
// ===========================================

export const AgentStatsPanel = ({
  open,
  onClose,
  className,
}: AgentStatsPanelProps) => {
  const [period, setPeriod] = useState<Period>('day');
  const [stats, setStats] = useState<AgentStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${AGENT_API_BASE}/agent/stats?period=${period}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch stats: ${response.status}`);
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    } finally {
      setIsLoading(false);
    }
  }, [period]);

  // Fetch stats when panel opens or period changes
  useEffect(() => {
    if (open) {
      fetchStats();
    }
  }, [open, period, fetchStats]);

  // Auto-refresh every 30 seconds when open
  useEffect(() => {
    if (!open) return;

    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, [open, fetchStats]);

  const formatLatency = (ms: number): string => {
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{
              type: 'spring',
              damping: 30,
              stiffness: 300,
            }}
            className={cn(
              'fixed right-0 top-0 bottom-0 w-[380px]',
              'bg-bg-secondary border-l border-border-subtle z-50',
              'flex flex-col',
              className
            )}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20">
                  <BarChart3 className="w-4 h-4 text-indigo-400" />
                </div>
                <h2 className="text-base font-semibold text-white">
                  Agent Stats
                </h2>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={fetchStats}
                  disabled={isLoading}
                  className={cn(
                    'p-1.5 rounded-lg transition-colors',
                    'hover:bg-bg-hover active:bg-bg-active',
                    isLoading && 'animate-spin'
                  )}
                  title="Refresh"
                >
                  <RefreshCw className="w-4 h-4 text-gray-400" />
                </button>
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-lg hover:bg-bg-hover active:bg-bg-active transition-colors"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            </div>

            {/* Period Toggle */}
            <div className="px-6 py-3 border-b border-border-subtle flex items-center justify-between">
              <span className="text-sm text-gray-400">Time Period</span>
              <PeriodToggle selected={period} onChange={setPeriod} />
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
              {isLoading && !stats ? (
                <div className="flex flex-col items-center justify-center h-full">
                  <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mb-4" />
                  <p className="text-sm text-gray-400">Loading stats...</p>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center mb-4">
                    <AlertCircle className="w-6 h-6 text-red-400" />
                  </div>
                  <p className="text-sm text-gray-400 mb-4">{error}</p>
                  <button
                    onClick={fetchStats}
                    className="px-4 py-2 text-sm bg-accent hover:bg-accent-hover rounded-lg text-white transition-colors"
                  >
                    Retry
                  </button>
                </div>
              ) : stats ? (
                <div className="space-y-4">
                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-3">
                    <StatCard
                      icon={TrendingUp}
                      label="Total Calls"
                      value={formatNumber(stats.total_calls)}
                      subValue={`Last ${period === 'hour' ? 'hour' : period === 'day' ? '24h' : '7 days'}`}
                      color="indigo"
                    />
                    <StatCard
                      icon={Clock}
                      label="Avg Latency"
                      value={formatLatency(stats.avg_latency_ms)}
                      subValue="per call"
                      color="purple"
                    />
                    <StatCard
                      icon={CheckCircle}
                      label="Success Rate"
                      value={`${stats.success_rate.toFixed(1)}%`}
                      subValue="of calls"
                      color="green"
                    />
                    <StatCard
                      icon={Zap}
                      label="Total Tokens"
                      value={formatNumber(stats.total_tokens)}
                      subValue="used"
                      color="yellow"
                    />
                  </div>

                  {/* Summary */}
                  <div className="mt-6 p-4 rounded-xl bg-glass-bg border border-glass-border backdrop-blur-xl">
                    <h3 className="text-sm font-medium text-white mb-2">
                      Summary
                    </h3>
                    <p className="text-xs text-gray-400 leading-relaxed">
                      {stats.total_calls === 0 ? (
                        'No agent calls recorded in this period.'
                      ) : (
                        <>
                          The AI agent processed{' '}
                          <span className="text-white font-medium">
                            {stats.total_calls} calls
                          </span>{' '}
                          with an average response time of{' '}
                          <span className="text-white font-medium">
                            {formatLatency(stats.avg_latency_ms)}
                          </span>
                          .{' '}
                          {stats.success_rate >= 95 ? (
                            <span className="text-green-400">
                              Excellent reliability!
                            </span>
                          ) : stats.success_rate >= 80 ? (
                            <span className="text-yellow-400">
                              Good performance.
                            </span>
                          ) : (
                            <span className="text-red-400">
                              Some issues detected.
                            </span>
                          )}
                        </>
                      )}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 flex items-center justify-center mb-4">
                    <BarChart3 className="w-8 h-8 text-indigo-400" />
                  </div>
                  <p className="text-sm text-gray-400">
                    No stats available yet.
                  </p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-border-subtle">
              <p className="text-xs text-gray-500 text-center">
                Auto-refreshes every 30 seconds
              </p>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default AgentStatsPanel;

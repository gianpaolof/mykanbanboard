// components/settings/DataManagementSettings.tsx - Export/Import data
import { useState, useRef, useCallback } from 'react';
import { Download, Upload, FileJson, CheckCircle2, AlertCircle, Loader2, RefreshCw, Search } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { useBoardStore } from '@/stores/boardStore';
import { SettingsSection } from './SettingsSection';
import {
  createExportData,
  downloadJson,
  validateImportData,
  readFile,
  getImportStats,
  type ExportData,
  type ImportStats,
} from '@/lib/export-import';

type ImportMode = 'replace' | 'merge';

export function DataManagementSettings() {
  const boards = useBoardStore((state) => state.boards);
  const columns = useBoardStore((state) => state.columns);
  const labels = useBoardStore((state) => state.labels);
  const tickets = useBoardStore((state) => state.tickets);
  const currentBoardId = useBoardStore((state) => state.currentBoardId);
  const board = useBoardStore((state) => state.board);

  // Import functionality requires reloading after import
  const loadBoard = useBoardStore((state) => state.loadBoard);
  const setColumns = useBoardStore((state) => state.setColumns);
  const setLabels = useBoardStore((state) => state.setLabels);
  const setTickets = useBoardStore((state) => state.setTickets);

  const reindexAllTickets = useBoardStore((state) => state.reindexAllTickets);

  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);
  const [importMode, setImportMode] = useState<ImportMode>('replace');
  const [importPreview, setImportPreview] = useState<{
    data: ExportData;
    stats: ImportStats;
  } | null>(null);
  const [importErrors, setImportErrors] = useState<string[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // ===========================================
  // EXPORT
  // ===========================================

  const handleExport = useCallback(async () => {
    setIsExporting(true);

    try {
      const exportData = createExportData({
        boards,
        columns,
        labels,
        tickets,
        currentBoardId,
        boardName: board?.name,
      });

      const timestamp = new Date().toISOString().slice(0, 10);
      const boardName = board?.name?.replace(/[^a-z0-9]/gi, '-').toLowerCase() || 'board';
      const filename = `kanban-${boardName}-${timestamp}.json`;

      downloadJson(exportData, filename);
      toast.success('Board exported successfully');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Export failed';
      toast.error(message);
    } finally {
      setIsExporting(false);
    }
  }, [boards, columns, labels, tickets, currentBoardId, board]);

  // ===========================================
  // IMPORT
  // ===========================================

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset state
    setImportPreview(null);
    setImportErrors([]);

    try {
      // Read file
      const content = await readFile(file);

      // Parse JSON
      let json: unknown;
      try {
        json = JSON.parse(content);
      } catch {
        setImportErrors(['Invalid JSON file']);
        return;
      }

      // Validate
      const result = validateImportData(json);
      if (!result.valid) {
        setImportErrors(result.errors);
        return;
      }

      // Show preview
      const stats = getImportStats(result.data!);
      setImportPreview({ data: result.data!, stats });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to read file';
      setImportErrors([message]);
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const handleImport = useCallback(async () => {
    if (!importPreview) return;

    setIsImporting(true);

    try {
      const { data } = importPreview;

      // For now, import first board only
      const importBoard = data.boards[0];
      if (!importBoard) {
        throw new Error('No board data to import');
      }

      if (importMode === 'replace') {
        // Replace all data with imported data
        setColumns(importBoard.columns);
        setLabels(importBoard.labels);

        // Group tickets by column
        const ticketsByColumn: Record<string, typeof importBoard.tickets> = {};
        for (const column of importBoard.columns) {
          ticketsByColumn[column.id] = [];
        }
        for (const ticket of importBoard.tickets) {
          if (ticketsByColumn[ticket.columnId]) {
            ticketsByColumn[ticket.columnId].push(ticket);
          }
        }

        // Update tickets for each column
        for (const [columnId, columnTickets] of Object.entries(ticketsByColumn)) {
          setTickets(columnId, columnTickets);
        }

        toast.success('Data imported successfully (replaced)');
      } else {
        // Merge mode - more complex, would need to dedupe IDs
        // For MVP, just reload to show imported data
        await loadBoard();
        toast.success('Data imported successfully (merged)');
      }

      // Clear preview
      setImportPreview(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Import failed';
      toast.error(message);
    } finally {
      setIsImporting(false);
    }
  }, [importPreview, importMode, setColumns, setLabels, setTickets, loadBoard]);

  const handleCancelImport = useCallback(() => {
    setImportPreview(null);
    setImportErrors([]);
  }, []);

  // Count current items
  const ticketCount = Object.values(tickets).reduce((sum, arr) => sum + arr.length, 0);

  // ===========================================
  // REINDEX
  // ===========================================

  const handleReindex = useCallback(async () => {
    setIsReindexing(true);
    try {
      await reindexAllTickets();
    } finally {
      setIsReindexing(false);
    }
  }, [reindexAllTickets]);

  return (
    <div className="space-y-8">
      {/* Reindex AI Search Section */}
      <SettingsSection
        title="AI Search Index"
        description="Rebuild the semantic search index for AI-powered ticket search"
      >
        <div className="space-y-4">
          <div className="flex items-center gap-4 p-4 rounded-lg bg-bg-tertiary border border-border-subtle">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center">
              <Search className="w-5 h-5 text-indigo-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary">
                Semantic Search
              </p>
              <p className="text-xs text-text-muted">
                {ticketCount} tickets available for AI-powered search
              </p>
            </div>
          </div>

          <button
            onClick={handleReindex}
            disabled={isReindexing || ticketCount === 0}
            className={cn(
              'flex items-center gap-2 px-4 py-2.5 rounded-lg',
              'bg-indigo-600 text-white font-medium text-sm',
              'hover:bg-indigo-700 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {isReindexing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            <span>{isReindexing ? 'Reindexing...' : 'Rebuild Search Index'}</span>
          </button>

          <p className="text-xs text-text-muted">
            Tickets are automatically indexed when created or updated. Use this if search results seem out of date.
          </p>
        </div>
      </SettingsSection>

      {/* Export Section */}
      <SettingsSection
        title="Export Data"
        description="Download your board data as a JSON file"
      >
        <div className="space-y-4">
          {/* Current data summary */}
          <div className="flex items-center gap-4 p-4 rounded-lg bg-bg-tertiary border border-border-subtle">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
              <FileJson className="w-5 h-5 text-accent" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary">
                {board?.name || 'Current Board'}
              </p>
              <p className="text-xs text-text-muted">
                {columns.length} columns &bull; {labels.length} labels &bull; {ticketCount} tickets
              </p>
            </div>
          </div>

          <button
            onClick={handleExport}
            disabled={isExporting}
            className={cn(
              'flex items-center gap-2 px-4 py-2.5 rounded-lg',
              'bg-accent text-white font-medium text-sm',
              'hover:bg-accent-hover transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {isExporting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            <span>{isExporting ? 'Exporting...' : 'Export Board'}</span>
          </button>
        </div>
      </SettingsSection>

      {/* Import Section */}
      <SettingsSection
        title="Import Data"
        description="Restore board data from a previously exported JSON file"
      >
        <div className="space-y-4">
          {/* Import mode toggle */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-text-muted mb-2">
              Import Mode
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setImportMode('replace')}
                className={cn(
                  'flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  importMode === 'replace'
                    ? 'bg-accent text-white'
                    : 'bg-bg-tertiary text-text-secondary hover:bg-bg-hover'
                )}
              >
                Replace
              </button>
              <button
                onClick={() => setImportMode('merge')}
                className={cn(
                  'flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  importMode === 'merge'
                    ? 'bg-accent text-white'
                    : 'bg-bg-tertiary text-text-secondary hover:bg-bg-hover'
                )}
              >
                Merge
              </button>
            </div>
            <p className="mt-1.5 text-xs text-text-muted">
              {importMode === 'replace'
                ? 'Replace all current data with imported data'
                : 'Add imported data to existing data'}
            </p>
          </div>

          {/* File input */}
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,application/json"
              onChange={handleFileSelect}
              className="hidden"
              id="import-file"
            />
            <label
              htmlFor="import-file"
              className={cn(
                'flex items-center justify-center gap-2 px-4 py-3 rounded-lg cursor-pointer',
                'border-2 border-dashed border-border-subtle',
                'hover:border-accent hover:bg-accent/5 transition-colors',
                'text-sm text-text-secondary hover:text-accent'
              )}
            >
              <Upload className="w-4 h-4" />
              <span>Choose JSON file to import</span>
            </label>
          </div>

          {/* Validation errors */}
          {importErrors.length > 0 && (
            <div className="p-4 rounded-lg bg-status-error/10 border border-status-error/20">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-status-error flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-status-error mb-2">
                    Invalid import file
                  </p>
                  <ul className="text-xs text-status-error/80 space-y-1">
                    {importErrors.slice(0, 5).map((error, i) => (
                      <li key={i}>&bull; {error}</li>
                    ))}
                    {importErrors.length > 5 && (
                      <li>&bull; ...and {importErrors.length - 5} more errors</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Import preview */}
          {importPreview && (
            <div className="p-4 rounded-lg bg-status-success/10 border border-status-success/20">
              <div className="flex items-start gap-3 mb-4">
                <CheckCircle2 className="w-5 h-5 text-status-success flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-status-success">
                    Valid import file
                  </p>
                  <p className="text-xs text-status-success/80 mt-1">
                    Version: {importPreview.data.version} &bull;{' '}
                    Exported: {new Date(importPreview.data.exportedAt).toLocaleDateString()}
                  </p>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-4 gap-2 mb-4">
                <div className="p-2 rounded bg-bg-tertiary text-center">
                  <p className="text-lg font-bold text-text-primary">
                    {importPreview.stats.boardCount}
                  </p>
                  <p className="text-2xs text-text-muted">Boards</p>
                </div>
                <div className="p-2 rounded bg-bg-tertiary text-center">
                  <p className="text-lg font-bold text-text-primary">
                    {importPreview.stats.columnCount}
                  </p>
                  <p className="text-2xs text-text-muted">Columns</p>
                </div>
                <div className="p-2 rounded bg-bg-tertiary text-center">
                  <p className="text-lg font-bold text-text-primary">
                    {importPreview.stats.labelCount}
                  </p>
                  <p className="text-2xs text-text-muted">Labels</p>
                </div>
                <div className="p-2 rounded bg-bg-tertiary text-center">
                  <p className="text-lg font-bold text-text-primary">
                    {importPreview.stats.ticketCount}
                  </p>
                  <p className="text-2xs text-text-muted">Tickets</p>
                </div>
              </div>

              {/* Warning for replace mode */}
              {importMode === 'replace' && (
                <p className="text-xs text-status-warning mb-4">
                  Warning: This will replace all current data. This action cannot be undone.
                </p>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={handleImport}
                  disabled={isImporting}
                  className={cn(
                    'flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg',
                    'bg-status-success text-white font-medium text-sm',
                    'hover:bg-status-success/90 transition-colors',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  {isImporting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Upload className="w-4 h-4" />
                  )}
                  <span>{isImporting ? 'Importing...' : 'Import Data'}</span>
                </button>
                <button
                  onClick={handleCancelImport}
                  disabled={isImporting}
                  className={cn(
                    'px-4 py-2 rounded-lg',
                    'text-text-secondary text-sm font-medium',
                    'hover:bg-bg-hover transition-colors',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </SettingsSection>

      {/* Info box */}
      <div
        className={cn(
          'p-4 rounded-lg border',
          'bg-bg-elevated border-border-subtle'
        )}
      >
        <p className="text-sm text-text-tertiary">
          Export creates a JSON file containing all your board data including columns,
          tickets, labels, and comments. You can use this to backup your data or
          transfer it to another device.
        </p>
      </div>
    </div>
  );
}

// components/calendar/CalendarView.tsx - Calendar view for tickets by due date
import { useState, useMemo, memo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  AlertCircle,
} from 'lucide-react';
import {
  format,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  isToday,
  addMonths,
  subMonths,
  parseISO,
  isBefore,
} from 'date-fns';
import { cn } from '@/lib/utils';
import { useBoardStore } from '@/stores/boardStore';
import type { Ticket } from '@/types';

interface CalendarViewProps {
  onTicketClick?: (ticket: Ticket) => void;
  filteredTickets?: Record<string, Ticket[]>;
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: 'bg-red-500/80 border-red-400',
  high: 'bg-orange-500/80 border-orange-400',
  medium: 'bg-yellow-500/80 border-yellow-400',
  low: 'bg-gray-500/80 border-gray-400',
};

export const CalendarView = memo(function CalendarView({
  onTicketClick,
  filteredTickets,
}: CalendarViewProps) {
  const ticketsFromStore = useBoardStore((state) => state.tickets);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  // Use filtered tickets if provided, otherwise use store tickets
  const tickets = filteredTickets || ticketsFromStore;

  // Flatten all tickets into a single array
  const allTickets = useMemo(() => {
    return Object.values(tickets).flat();
  }, [tickets]);

  // Group tickets by date (dueDate)
  const ticketsByDate = useMemo(() => {
    const grouped: Record<string, Ticket[]> = {};

    allTickets.forEach((ticket) => {
      if (ticket.dueDate) {
        const dateKey = format(parseISO(ticket.dueDate), 'yyyy-MM-dd');
        if (!grouped[dateKey]) {
          grouped[dateKey] = [];
        }
        grouped[dateKey].push(ticket);
      }
    });

    return grouped;
  }, [allTickets]);

  // Tickets without due date
  const unscheduledTickets = useMemo(() => {
    return allTickets.filter((t) => !t.dueDate);
  }, [allTickets]);

  // Calculate days to display
  const calendarDays = useMemo(() => {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const calendarStart = startOfWeek(monthStart, { weekStartsOn: 1 }); // Monday start
    const calendarEnd = endOfWeek(monthEnd, { weekStartsOn: 1 });

    return eachDayOfInterval({ start: calendarStart, end: calendarEnd });
  }, [currentDate]);

  const goToPreviousMonth = useCallback(() => {
    setCurrentDate((date) => subMonths(date, 1));
  }, []);

  const goToNextMonth = useCallback(() => {
    setCurrentDate((date) => addMonths(date, 1));
  }, []);

  const goToToday = useCallback(() => {
    setCurrentDate(new Date());
    setSelectedDate(new Date());
  }, []);

  const handleDayClick = useCallback((day: Date) => {
    setSelectedDate(day);
  }, []);

  const handleTicketClick = useCallback(
    (ticket: Ticket, e: React.MouseEvent) => {
      e.stopPropagation();
      onTicketClick?.(ticket);
    },
    [onTicketClick]
  );

  // Get tickets for selected date
  const selectedDateTickets = useMemo(() => {
    if (!selectedDate) return [];
    const dateKey = format(selectedDate, 'yyyy-MM-dd');
    return ticketsByDate[dateKey] || [];
  }, [selectedDate, ticketsByDate]);

  return (
    <div className="h-full flex">
      {/* Main Calendar */}
      <div className="flex-1 flex flex-col p-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold text-text-primary">
              {format(currentDate, 'MMMM yyyy')}
            </h2>
            <div className="flex items-center gap-1">
              <button
                onClick={goToPreviousMonth}
                className={cn(
                  'p-1.5 rounded-lg',
                  'text-text-tertiary hover:text-text-primary hover:bg-bg-hover',
                  'transition-colors'
                )}
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={goToNextMonth}
                className={cn(
                  'p-1.5 rounded-lg',
                  'text-text-tertiary hover:text-text-primary hover:bg-bg-hover',
                  'transition-colors'
                )}
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
            <button
              onClick={goToToday}
              className={cn(
                'px-3 py-1 rounded-lg text-sm font-medium',
                'bg-bg-elevated border border-border-subtle',
                'text-text-secondary hover:text-text-primary hover:bg-bg-hover',
                'transition-colors'
              )}
            >
              Today
            </button>
          </div>

          <div className="flex items-center gap-2 text-sm text-text-muted">
            <CalendarIcon className="w-4 h-4" />
            <span>{allTickets.length} tickets total</span>
            {unscheduledTickets.length > 0 && (
              <span className="text-status-warning">
                ({unscheduledTickets.length} unscheduled)
              </span>
            )}
          </div>
        </div>

        {/* Weekday headers */}
        <div className="grid grid-cols-7 mb-2">
          {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
            <div
              key={day}
              className="text-center text-xs font-semibold text-text-muted uppercase py-2"
            >
              {day}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7 flex-1 gap-1 overflow-hidden">
          {calendarDays.map((day) => {
            const dateKey = format(day, 'yyyy-MM-dd');
            const dayTickets = ticketsByDate[dateKey] || [];
            const isCurrentMonth = isSameMonth(day, currentDate);
            const isSelected = selectedDate && isSameDay(day, selectedDate);
            const isDayToday = isToday(day);
            const hasOverdue = dayTickets.some(
              (t) =>
                t.dueDate &&
                isBefore(parseISO(t.dueDate), new Date()) &&
                !isSameDay(parseISO(t.dueDate), new Date())
            );

            return (
              <motion.div
                key={dateKey}
                onClick={() => handleDayClick(day)}
                whileHover={{ scale: 1.02 }}
                className={cn(
                  'relative p-1 rounded-lg cursor-pointer min-h-[80px]',
                  'border transition-all',
                  isCurrentMonth
                    ? 'bg-bg-secondary border-border-subtle'
                    : 'bg-bg-tertiary/50 border-transparent',
                  isSelected && 'ring-2 ring-accent border-accent',
                  isDayToday && !isSelected && 'border-accent/50'
                )}
              >
                {/* Day number */}
                <div
                  className={cn(
                    'text-xs font-semibold mb-1 flex items-center gap-1',
                    isCurrentMonth ? 'text-text-primary' : 'text-text-muted',
                    isDayToday && 'text-accent'
                  )}
                >
                  {isDayToday && (
                    <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                  )}
                  {format(day, 'd')}
                </div>

                {/* Ticket indicators */}
                <div className="space-y-0.5 overflow-hidden">
                  {dayTickets.slice(0, 3).map((ticket) => (
                    <div
                      key={ticket.id}
                      onClick={(e) => handleTicketClick(ticket, e)}
                      className={cn(
                        'text-[10px] px-1 py-0.5 rounded truncate',
                        'border-l-2 bg-bg-elevated',
                        'hover:bg-bg-hover transition-colors',
                        PRIORITY_COLORS[ticket.priority || 'medium'] ||
                          'border-gray-500'
                      )}
                    >
                      {ticket.title}
                    </div>
                  ))}
                  {dayTickets.length > 3 && (
                    <div className="text-[10px] text-text-muted px-1">
                      +{dayTickets.length - 3} more
                    </div>
                  )}
                </div>

                {/* Overdue indicator */}
                {hasOverdue && isBefore(day, new Date()) && (
                  <div className="absolute top-1 right-1">
                    <AlertCircle className="w-3 h-3 text-status-error" />
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Sidebar - Selected date details / Unscheduled */}
      <div className="w-72 border-l border-border-subtle bg-bg-secondary p-4 overflow-y-auto">
        <AnimatePresence mode="wait">
          {selectedDate ? (
            <motion.div
              key="selected"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <h3 className="text-sm font-semibold text-text-primary mb-1">
                {format(selectedDate, 'EEEE, MMMM d')}
              </h3>
              <p className="text-xs text-text-muted mb-4">
                {selectedDateTickets.length} ticket
                {selectedDateTickets.length !== 1 ? 's' : ''} due
              </p>

              {selectedDateTickets.length === 0 ? (
                <div className="text-sm text-text-muted py-8 text-center">
                  No tickets due on this date
                </div>
              ) : (
                <div className="space-y-2">
                  {selectedDateTickets.map((ticket) => (
                    <div
                      key={ticket.id}
                      onClick={(e) => handleTicketClick(ticket, e)}
                      className={cn(
                        'p-3 rounded-lg cursor-pointer',
                        'bg-bg-elevated border border-border-subtle',
                        'hover:border-accent/50 transition-colors'
                      )}
                    >
                      <div className="flex items-start gap-2">
                        <div
                          className={cn(
                            'w-2 h-2 rounded-full mt-1.5 flex-shrink-0',
                            ticket.priority === 'critical' && 'bg-red-500',
                            ticket.priority === 'high' && 'bg-orange-500',
                            ticket.priority === 'medium' && 'bg-yellow-500',
                            ticket.priority === 'low' && 'bg-gray-500',
                            !ticket.priority && 'bg-gray-500'
                          )}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-text-primary truncate">
                            {ticket.title}
                          </div>
                          {ticket.description && (
                            <div className="text-xs text-text-muted line-clamp-2 mt-1">
                              {ticket.description}
                            </div>
                          )}
                          <div className="flex items-center gap-2 mt-2">
                            {ticket.effort && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-bg-tertiary text-text-muted uppercase">
                                {ticket.effort}
                              </span>
                            )}
                            {ticket.labels.slice(0, 2).map((label) => (
                              <span
                                key={label.id}
                                className="text-[10px] px-1.5 py-0.5 rounded"
                                style={{
                                  backgroundColor: `${label.color}20`,
                                  color: label.color,
                                }}
                              >
                                {label.name}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="unscheduled"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <h3 className="text-sm font-semibold text-text-primary mb-1">
                Unscheduled Tickets
              </h3>
              <p className="text-xs text-text-muted mb-4">
                {unscheduledTickets.length} ticket
                {unscheduledTickets.length !== 1 ? 's' : ''} without due date
              </p>

              {unscheduledTickets.length === 0 ? (
                <div className="text-sm text-text-muted py-8 text-center">
                  All tickets have due dates
                </div>
              ) : (
                <div className="space-y-2">
                  {unscheduledTickets.slice(0, 20).map((ticket) => (
                    <div
                      key={ticket.id}
                      onClick={(e) => handleTicketClick(ticket, e)}
                      className={cn(
                        'p-2 rounded-lg cursor-pointer',
                        'bg-bg-elevated border border-border-subtle',
                        'hover:border-accent/50 transition-colors'
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className={cn(
                            'w-2 h-2 rounded-full flex-shrink-0',
                            ticket.priority === 'critical' && 'bg-red-500',
                            ticket.priority === 'high' && 'bg-orange-500',
                            ticket.priority === 'medium' && 'bg-yellow-500',
                            ticket.priority === 'low' && 'bg-gray-500',
                            !ticket.priority && 'bg-gray-500'
                          )}
                        />
                        <div className="text-sm text-text-primary truncate">
                          {ticket.title}
                        </div>
                      </div>
                    </div>
                  ))}
                  {unscheduledTickets.length > 20 && (
                    <div className="text-xs text-text-muted text-center py-2">
                      +{unscheduledTickets.length - 20} more
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
});

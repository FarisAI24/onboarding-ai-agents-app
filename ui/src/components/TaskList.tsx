'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle2,
  Circle,
  Clock,
  AlertTriangle,
  ChevronDown,
  Building2,
  Shield,
  Laptop,
  DollarSign,
  Calendar,
} from 'lucide-react';
import { api, Task } from '@/lib/api';
import { format, isAfter, parseISO, startOfWeek, endOfWeek, addWeeks } from 'date-fns';
import clsx from 'clsx';

interface TaskListProps {
  userId: number;
  refreshTrigger?: number;
}

const departmentIcons: Record<string, React.ReactNode> = {
  HR: <Building2 className="w-4 h-4" />,
  IT: <Laptop className="w-4 h-4" />,
  Security: <Shield className="w-4 h-4" />,
  Finance: <DollarSign className="w-4 h-4" />,
};

const departmentColors: Record<string, string> = {
  HR: 'from-blue-500 to-blue-600',
  IT: 'from-emerald-500 to-emerald-600',
  Security: 'from-amber-500 to-amber-600',
  Finance: 'from-purple-500 to-purple-600',
};

const statusColors: Record<string, string> = {
  NOT_STARTED: 'bg-surface-200 dark:bg-surface-600',
  IN_PROGRESS: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300',
  DONE: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300',
};

export default function TaskList({ userId, refreshTrigger }: TaskListProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedDept, setExpandedDept] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed'>('all');
  const [timeline, setTimeline] = useState<'all' | 'this_week' | 'next_week'>('all');

  useEffect(() => {
    loadTasks();
  }, [userId, refreshTrigger]);

  const loadTasks = async () => {
    try {
      const data = await api.getTasks(userId);
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateTaskStatus = async (taskId: number, status: Task['status']) => {
    try {
      await api.updateTaskStatus(taskId, status);
      setTasks((prev) =>
        prev.map((t) =>
          t.id === taskId
            ? { ...t, status, completed_at: status === 'DONE' ? new Date().toISOString() : undefined }
            : t
        )
      );
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const filteredTasks = tasks.filter((task) => {
    // Status filter
    if (filter === 'pending' && task.status === 'DONE') return false;
    if (filter === 'completed' && task.status !== 'DONE') return false;

    // Timeline filter
    if (timeline !== 'all') {
      const dueDate = parseISO(task.due_date);
      const today = new Date();
      const thisWeekStart = startOfWeek(today);
      const thisWeekEnd = endOfWeek(today);
      const nextWeekStart = startOfWeek(addWeeks(today, 1));
      const nextWeekEnd = endOfWeek(addWeeks(today, 1));

      if (timeline === 'this_week') {
        if (dueDate < thisWeekStart || dueDate > thisWeekEnd) return false;
      } else if (timeline === 'next_week') {
        if (dueDate < nextWeekStart || dueDate > nextWeekEnd) return false;
      }
    }

    return true;
  });

  // Group by department
  const groupedTasks = filteredTasks.reduce((acc, task) => {
    const dept = task.department;
    if (!acc[dept]) acc[dept] = [];
    acc[dept].push(task);
    return acc;
  }, {} as Record<string, Task[]>);

  // Calculate progress
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((t) => t.status === 'DONE').length;
  const overdueTasks = tasks.filter((t) => t.is_overdue).length;
  const progressPercent = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-white/60 dark:bg-surface-800/60 backdrop-blur-lg rounded-2xl shadow-xl border border-surface-200/50 dark:border-surface-700/50 overflow-hidden">
      {/* Header with Progress */}
      <div className="p-6 border-b border-surface-200/50 dark:border-surface-700/50">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-surface-900 dark:text-surface-100">
            Onboarding Tasks
          </h2>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-surface-600 dark:text-surface-400">
              {completedTasks}/{totalTasks} completed
            </span>
            {overdueTasks > 0 && (
              <span className="flex items-center gap-1 text-red-500">
                <AlertTriangle className="w-4 h-4" />
                {overdueTasks} overdue
              </span>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="relative h-3 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
            className="absolute inset-y-0 left-0 bg-gradient-to-r from-primary-500 to-accent-500 rounded-full"
          />
        </div>
        <p className="text-sm text-surface-500 mt-2">
          {progressPercent.toFixed(0)}% complete
        </p>

        {/* Filters */}
        <div className="flex flex-wrap gap-2 mt-4">
          <div className="flex bg-surface-100 dark:bg-surface-700 rounded-lg p-1">
            {(['all', 'pending', 'completed'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={clsx(
                  'px-3 py-1 text-sm rounded-md transition-colors capitalize',
                  filter === f
                    ? 'bg-white dark:bg-surface-600 shadow text-surface-900 dark:text-surface-100'
                    : 'text-surface-500 hover:text-surface-700 dark:hover:text-surface-300'
                )}
              >
                {f}
              </button>
            ))}
          </div>
          <div className="flex bg-surface-100 dark:bg-surface-700 rounded-lg p-1">
            {([
              { value: 'all', label: 'All time' },
              { value: 'this_week', label: 'This week' },
              { value: 'next_week', label: 'Next week' },
            ] as const).map((t) => (
              <button
                key={t.value}
                onClick={() => setTimeline(t.value)}
                className={clsx(
                  'px-3 py-1 text-sm rounded-md transition-colors flex items-center gap-1',
                  timeline === t.value
                    ? 'bg-white dark:bg-surface-600 shadow text-surface-900 dark:text-surface-100'
                    : 'text-surface-500 hover:text-surface-700 dark:hover:text-surface-300'
                )}
              >
                <Calendar className="w-3 h-3" />
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tasks by Department */}
      <div className="divide-y divide-surface-200/50 dark:divide-surface-700/50">
        {Object.entries(groupedTasks).map(([dept, deptTasks]) => (
          <div key={dept} className="group">
            {/* Department Header */}
            <button
              onClick={() => setExpandedDept(expandedDept === dept ? null : dept)}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-surface-50 dark:hover:bg-surface-700/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div
                  className={clsx(
                    'w-8 h-8 rounded-lg bg-gradient-to-br flex items-center justify-center text-white',
                    departmentColors[dept] || 'from-gray-500 to-gray-600'
                  )}
                >
                  {departmentIcons[dept] || <Building2 className="w-4 h-4" />}
                </div>
                <span className="font-medium text-surface-800 dark:text-surface-200">
                  {dept}
                </span>
                <span className="text-sm text-surface-500">
                  {deptTasks.filter((t) => t.status === 'DONE').length}/{deptTasks.length}
                </span>
              </div>
              <ChevronDown
                className={clsx(
                  'w-5 h-5 text-surface-400 transition-transform',
                  expandedDept === dept && 'rotate-180'
                )}
              />
            </button>

            {/* Tasks */}
            <AnimatePresence>
              {(expandedDept === dept || expandedDept === null) && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="px-6 pb-4 space-y-2">
                    {deptTasks.map((task) => (
                      <TaskItem
                        key={task.id}
                        task={task}
                        onStatusChange={updateTaskStatus}
                      />
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>

      {filteredTasks.length === 0 && (
        <div className="p-8 text-center text-surface-500">
          No tasks found for the selected filters.
        </div>
      )}
    </div>
  );
}

interface TaskItemProps {
  task: Task;
  onStatusChange: (taskId: number, status: Task['status']) => void;
}

function TaskItem({ task, onStatusChange }: TaskItemProps) {
  const cycleStatus = () => {
    const nextStatus: Record<Task['status'], Task['status']> = {
      NOT_STARTED: 'IN_PROGRESS',
      IN_PROGRESS: 'DONE',
      DONE: 'NOT_STARTED',
    };
    onStatusChange(task.id, nextStatus[task.status]);
  };

  return (
    <motion.div
      layout
      className={clsx(
        'flex items-start gap-3 p-3 rounded-xl transition-colors',
        task.status === 'DONE'
          ? 'bg-emerald-50 dark:bg-emerald-900/20'
          : task.is_overdue
          ? 'bg-red-50 dark:bg-red-900/20'
          : 'bg-surface-50 dark:bg-surface-700/50'
      )}
    >
      <button
        onClick={cycleStatus}
        className="mt-0.5 flex-shrink-0"
      >
        {task.status === 'DONE' ? (
          <CheckCircle2 className="w-5 h-5 text-emerald-500" />
        ) : task.status === 'IN_PROGRESS' ? (
          <Clock className="w-5 h-5 text-amber-500" />
        ) : (
          <Circle className="w-5 h-5 text-surface-400 hover:text-primary-500 transition-colors" />
        )}
      </button>

      <div className="flex-1 min-w-0">
        <p
          className={clsx(
            'text-sm font-medium',
            task.status === 'DONE'
              ? 'text-surface-500 line-through'
              : 'text-surface-800 dark:text-surface-200'
          )}
        >
          {task.title}
        </p>
        {task.description && (
          <p className="text-xs text-surface-500 mt-0.5 truncate">
            {task.description}
          </p>
        )}
        <div className="flex items-center gap-2 mt-1">
          <span
            className={clsx(
              'text-xs px-2 py-0.5 rounded-full',
              statusColors[task.status]
            )}
          >
            {task.status.replace('_', ' ')}
          </span>
          <span
            className={clsx(
              'text-xs flex items-center gap-1',
              task.is_overdue ? 'text-red-500' : 'text-surface-400'
            )}
          >
            <Calendar className="w-3 h-3" />
            {format(parseISO(task.due_date), 'MMM d')}
            {task.is_overdue && <AlertTriangle className="w-3 h-3" />}
          </span>
        </div>
      </div>
    </motion.div>
  );
}


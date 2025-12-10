'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  TrendingUp,
  Clock,
  AlertTriangle,
  CheckCircle2,
  BarChart3,
  MessageSquare,
  Activity,
  Zap,
  Server,
  Shield,
  RefreshCw,
} from 'lucide-react';
import { api, AggregateMetrics, UserProgressStats } from '@/lib/api';
import clsx from 'clsx';

const departmentColors: Record<string, string> = {
  HR: 'bg-blue-500',
  IT: 'bg-emerald-500',
  Security: 'bg-amber-500',
  Finance: 'bg-purple-500',
  General: 'bg-gray-500',
};

interface SystemMetrics {
  uptime_seconds: number;
  total_requests: number;
  error_count: number;
  error_rate: number;
  response_times: {
    p50_ms: number;
    p95_ms: number;
    p99_ms: number;
    avg_ms: number;
  };
  department_queries: Record<string, number>;
}

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState<AggregateMetrics | null>(null);
  const [users, setUsers] = useState<UserProgressStats[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const loadData = async () => {
    try {
      const [metricsData, usersData] = await Promise.all([
        api.getAggregateMetrics(),
        api.getAllUsersProgress(),
      ]);
      setMetrics(metricsData);
      setUsers(usersData);
      
      // Try to load system metrics
      try {
        const response = await fetch('http://localhost:8000/api/v1/dashboard/metrics');
        if (response.ok) {
          const sysMetrics = await response.json();
          setSystemMetrics(sysMetrics);
        }
      } catch (e) {
        console.log('System metrics not available');
      }
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="text-center text-surface-500 py-8">
        Failed to load metrics. Please try again.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900 dark:text-surface-100">
            Admin Dashboard
          </h1>
          <p className="text-surface-500 mt-1">
            Monitor onboarding progress and system health
            {lastUpdated && (
              <span className="ml-2 text-xs">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-surface-600 dark:text-surface-400">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-surface-300"
            />
            Auto-refresh
          </label>
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* System Health Metrics */}
      {systemMetrics && (
        <div className="bg-gradient-to-r from-surface-900 to-surface-800 rounded-2xl p-6 text-white">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Server className="w-5 h-5" />
            System Health
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <SystemMetricItem
              label="Uptime"
              value={formatUptime(systemMetrics.uptime_seconds)}
              icon={<Activity className="w-4 h-4" />}
            />
            <SystemMetricItem
              label="Total Requests"
              value={systemMetrics.total_requests.toLocaleString()}
              icon={<Zap className="w-4 h-4" />}
            />
            <SystemMetricItem
              label="Error Rate"
              value={`${(systemMetrics.error_rate * 100).toFixed(2)}%`}
              icon={<AlertTriangle className="w-4 h-4" />}
              alert={systemMetrics.error_rate > 0.05}
            />
            <SystemMetricItem
              label="Avg Response"
              value={`${systemMetrics.response_times.avg_ms.toFixed(0)}ms`}
              icon={<Clock className="w-4 h-4" />}
            />
            <SystemMetricItem
              label="P95 Response"
              value={`${systemMetrics.response_times.p95_ms.toFixed(0)}ms`}
              icon={<TrendingUp className="w-4 h-4" />}
            />
            <SystemMetricItem
              label="P99 Response"
              value={`${systemMetrics.response_times.p99_ms.toFixed(0)}ms`}
              icon={<BarChart3 className="w-4 h-4" />}
            />
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={<Users className="w-5 h-5" />}
          label="Total New Hires"
          value={metrics.total_new_hires}
          color="from-blue-500 to-blue-600"
        />
        <MetricCard
          icon={<TrendingUp className="w-5 h-5" />}
          label="Avg Completion"
          value={`${metrics.avg_completion_percentage.toFixed(1)}%`}
          color="from-emerald-500 to-emerald-600"
          subtitle={metrics.avg_completion_percentage >= 70 ? "On track" : "Needs attention"}
        />
        <MetricCard
          icon={<Clock className="w-5 h-5" />}
          label="Avg Days to Complete"
          value={metrics.avg_days_to_complete?.toFixed(1) || 'N/A'}
          color="from-amber-500 to-amber-600"
        />
        <MetricCard
          icon={<CheckCircle2 className="w-5 h-5" />}
          label="Resolution Rate"
          value={`${(metrics.resolution_rate * 100).toFixed(0)}%`}
          color="from-purple-500 to-purple-600"
          subtitle="Without escalation"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Queries by Department */}
        <div className="bg-white/60 dark:bg-surface-800/60 backdrop-blur-lg rounded-2xl shadow-xl border border-surface-200/50 dark:border-surface-700/50 p-6">
          <h3 className="text-lg font-semibold text-surface-900 dark:text-surface-100 mb-4 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-primary-500" />
            Queries by Department
          </h3>
          <div className="space-y-3">
            {Object.entries(metrics.queries_by_department).map(([dept, count]) => {
              const total = Object.values(metrics.queries_by_department).reduce((a, b) => a + b, 0);
              const percent = total > 0 ? (count / total) * 100 : 0;
              return (
                <div key={dept}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-surface-600 dark:text-surface-400">{dept}</span>
                    <span className="text-surface-900 dark:text-surface-100 font-medium">
                      {count} ({percent.toFixed(0)}%)
                    </span>
                  </div>
                  <div className="h-2 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${percent}%` }}
                      transition={{ duration: 0.5, delay: 0.1 }}
                      className={clsx('h-full rounded-full', departmentColors[dept])}
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <p className="text-sm text-surface-500 mt-4">
            {metrics.total_queries_today} queries today
          </p>
        </div>

        {/* Completion by Department */}
        <div className="bg-white/60 dark:bg-surface-800/60 backdrop-blur-lg rounded-2xl shadow-xl border border-surface-200/50 dark:border-surface-700/50 p-6">
          <h3 className="text-lg font-semibold text-surface-900 dark:text-surface-100 mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary-500" />
            Completion by Department
          </h3>
          <div className="space-y-3">
            {Object.entries(metrics.completion_by_department).map(([dept, percent]) => (
              <div key={dept}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-surface-600 dark:text-surface-400">{dept}</span>
                  <span className="text-surface-900 dark:text-surface-100 font-medium">
                    {percent.toFixed(0)}%
                  </span>
                </div>
                <div className="h-2 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percent}%` }}
                    transition={{ duration: 0.5, delay: 0.1 }}
                    className={clsx(
                      'h-full rounded-full',
                      percent >= 80 ? 'bg-emerald-500' : percent >= 50 ? 'bg-amber-500' : 'bg-red-500'
                    )}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Security & AI Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white/60 dark:bg-surface-800/60 backdrop-blur-lg rounded-2xl shadow-xl border border-surface-200/50 dark:border-surface-700/50 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-surface-900 dark:text-surface-100">Security</h4>
              <p className="text-xs text-surface-500">PII Protection Active</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            ✓ Protected
          </div>
        </div>
        
        <div className="bg-white/60 dark:bg-surface-800/60 backdrop-blur-lg rounded-2xl shadow-xl border border-surface-200/50 dark:border-surface-700/50 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-surface-900 dark:text-surface-100">AI Routing</h4>
              <p className="text-xs text-surface-500">ML Model Active</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {Object.values(metrics.queries_by_department).reduce((a, b) => a + b, 0)} Routed
          </div>
        </div>
        
        <div className="bg-white/60 dark:bg-surface-800/60 backdrop-blur-lg rounded-2xl shadow-xl border border-surface-200/50 dark:border-surface-700/50 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center text-white">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-semibold text-surface-900 dark:text-surface-100">RAG System</h4>
              <p className="text-xs text-surface-500">Hybrid Search Active</p>
            </div>
          </div>
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            ✓ Operational
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white/60 dark:bg-surface-800/60 backdrop-blur-lg rounded-2xl shadow-xl border border-surface-200/50 dark:border-surface-700/50 overflow-hidden">
        <div className="p-6 border-b border-surface-200/50 dark:border-surface-700/50">
          <h3 className="text-lg font-semibold text-surface-900 dark:text-surface-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-primary-500" />
            New Hire Progress
            <span className="ml-2 text-sm font-normal text-surface-500">
              ({users.length} employees)
            </span>
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-surface-50 dark:bg-surface-700/50">
              <tr>
                <th className="text-left px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">
                  Employee
                </th>
                <th className="text-left px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="text-left px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">
                  Department
                </th>
                <th className="text-left px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">
                  Days
                </th>
                <th className="text-left px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">
                  Progress
                </th>
                <th className="text-left px-6 py-3 text-xs font-medium text-surface-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-200/50 dark:divide-surface-700/50">
              {users.map((user) => (
                <tr key={user.user_id} className="hover:bg-surface-50 dark:hover:bg-surface-700/30 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white text-sm font-medium">
                        {user.user_name.charAt(0)}
                      </div>
                      <span className="font-medium text-surface-900 dark:text-surface-100">
                        {user.user_name}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-surface-600 dark:text-surface-400">
                    {user.role}
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-100 dark:bg-surface-700 text-surface-700 dark:text-surface-300">
                      {user.department}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-surface-600 dark:text-surface-400">
                    {user.days_since_start}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-surface-200 dark:bg-surface-700 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${user.progress_percentage}%` }}
                          transition={{ duration: 0.5 }}
                          className={clsx(
                            'h-full rounded-full',
                            user.progress_percentage >= 80
                              ? 'bg-emerald-500'
                              : user.progress_percentage >= 50
                              ? 'bg-amber-500'
                              : 'bg-red-500'
                          )}
                        />
                      </div>
                      <span className="text-sm text-surface-600 dark:text-surface-400 w-12">
                        {user.progress_percentage.toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {user.overdue_tasks > 0 ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300">
                        <AlertTriangle className="w-3 h-3" />
                        {user.overdue_tasks} overdue
                      </span>
                    ) : user.progress_percentage === 100 ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300">
                        <CheckCircle2 className="w-3 h-3" />
                        Complete
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                        <Clock className="w-3 h-3" />
                        On track
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {users.length === 0 && (
          <div className="text-center text-surface-500 py-8">
            No new hires found.
          </div>
        )}
      </div>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
  subtitle?: string;
}

function MetricCard({ icon, label, value, color, subtitle }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/60 dark:bg-surface-800/60 backdrop-blur-lg rounded-2xl shadow-xl border border-surface-200/50 dark:border-surface-700/50 p-6"
    >
      <div className="flex items-center gap-4">
        <div className={clsx('w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center text-white', color)}>
          {icon}
        </div>
        <div>
          <p className="text-sm text-surface-500 dark:text-surface-400">{label}</p>
          <p className="text-2xl font-bold text-surface-900 dark:text-surface-100">{value}</p>
          {subtitle && (
            <p className="text-xs text-surface-400">{subtitle}</p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

interface SystemMetricItemProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  alert?: boolean;
}

function SystemMetricItem({ label, value, icon, alert }: SystemMetricItemProps) {
  return (
    <div className={clsx(
      "p-3 rounded-lg",
      alert ? "bg-red-500/20" : "bg-white/10"
    )}>
      <div className="flex items-center gap-2 text-white/70 text-xs mb-1">
        {icon}
        {label}
      </div>
      <div className={clsx(
        "text-lg font-bold",
        alert ? "text-red-300" : "text-white"
      )}>
        {value}
      </div>
    </div>
  );
}

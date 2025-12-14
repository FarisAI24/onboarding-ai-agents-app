'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, Search, Filter, AlertCircle, CheckCircle, 
  Info, Clock, User, Activity, RefreshCw, Download
} from 'lucide-react';
import { api } from '@/lib/api';
import clsx from 'clsx';

interface AuditLog {
  id: number;
  timestamp: string;
  action: string;
  resource_type: string;
  resource_id?: number;
  user_id?: number;
  user_email?: string;
  ip_address?: string;
  status: string;
  details?: {
    query?: string;
    response?: string;
    department?: string;
    duration_ms?: number;
    status_code?: number;
    method?: string;
    path?: string;
    [key: string]: any;
  };
}

interface AuditSummary {
  period_days: number;
  action_counts: Record<string, number>;
  status_counts: Record<string, number>;
  recent_failures: any[];
}

export default function AuditLogExplorer() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    action: '',
    user_id: '',
    resource_type: '',
    status: '',
    start_date: '',
    end_date: '',
  });
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [logsData, summaryData] = await Promise.all([
        api.searchAuditLogs({ limit: 100 }),
        api.getAuditLogSummary(7),
      ]);
      
      setLogs(logsData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to load audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = async () => {
    setLoading(true);
    try {
      const params: any = { limit: 100 };
      if (filters.action) params.action = filters.action;
      if (filters.user_id) params.user_id = parseInt(filters.user_id);
      if (filters.resource_type) params.resource_type = filters.resource_type;
      if (filters.start_date) params.start_date = filters.start_date;
      if (filters.end_date) params.end_date = filters.end_date;
      
      const logsData = await api.searchAuditLogs(params);
      setLogs(logsData);
    } catch (error) {
      console.error('Failed to filter logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => {
    setFilters({
      action: '',
      user_id: '',
      resource_type: '',
      status: '',
      start_date: '',
      end_date: '',
    });
    loadData();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failure':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Info className="w-4 h-4 text-blue-500" />;
    }
  };

  const getActionColor = (action: string) => {
    if (action.includes('chat')) return 'bg-purple-100 text-purple-800 font-medium';
    if (action.includes('auth')) return 'bg-blue-100 text-blue-800 font-medium';
    if (action.includes('create') || action.includes('register')) return 'bg-green-100 text-green-800 font-medium';
    if (action.includes('delete')) return 'bg-red-100 text-red-800 font-medium';
    if (action.includes('update')) return 'bg-amber-100 text-amber-800 font-medium';
    return 'bg-gray-100 text-gray-800 font-medium';
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const exportLogs = () => {
    const csv = [
      ['Timestamp', 'Action', 'Resource', 'User', 'Status', 'IP Address'].join(','),
      ...logs.map(log => [
        log.timestamp,
        log.action,
        `${log.resource_type}:${log.resource_id || ''}`,
        log.user_email || log.user_id || '',
        log.status,
        log.ip_address || ''
      ].join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  if (loading && logs.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl p-4 border border-gray-300">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <Activity className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {Object.values(summary.action_counts).reduce((a, b) => a + b, 0)}
                </p>
                <p className="text-sm font-medium text-gray-700">Total Events</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-4 border border-gray-300">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-green-700">
                  {summary.status_counts.success || 0}
                </p>
                <p className="text-sm font-medium text-gray-700">Successful</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-4 border border-gray-300">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                <AlertCircle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-red-700">
                  {summary.status_counts.failure || 0}
                </p>
                <p className="text-sm font-medium text-gray-700">Failed</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-4 border border-gray-300">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                <Clock className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{summary.period_days}</p>
                <p className="text-sm font-medium text-gray-700">Days Tracked</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 border border-gray-300">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-700" />
          <h3 className="font-bold text-gray-900">Filters</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Action (e.g., chat.send)"
            value={filters.action}
            onChange={(e) => setFilters({ ...filters, action: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder:text-gray-500"
          />
          <input
            type="text"
            placeholder="User ID"
            value={filters.user_id}
            onChange={(e) => setFilters({ ...filters, user_id: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder:text-gray-500"
          />
          <input
            type="date"
            value={filters.start_date}
            onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
          />
          <input
            type="date"
            value={filters.end_date}
            onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
          />
        </div>
        
        <div className="flex gap-2 mt-4">
          <button
            onClick={applyFilters}
            className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            Apply Filters
          </button>
          <button
            onClick={clearFilters}
            className="px-4 py-2 bg-gray-200 text-gray-900 font-medium rounded-lg hover:bg-gray-300"
          >
            Clear
          </button>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-gray-200 text-gray-900 font-medium rounded-lg hover:bg-gray-300 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={exportLogs}
            className="px-4 py-2 bg-gray-200 text-gray-900 font-medium rounded-lg hover:bg-gray-300 flex items-center gap-2 ml-auto"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-xl border border-gray-300 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-bold text-gray-800 uppercase">Timestamp</th>
                <th className="px-4 py-3 text-left text-xs font-bold text-gray-800 uppercase">Action</th>
                <th className="px-4 py-3 text-left text-xs font-bold text-gray-800 uppercase">User</th>
                <th className="px-4 py-3 text-left text-xs font-bold text-gray-800 uppercase">Query</th>
                <th className="px-4 py-3 text-left text-xs font-bold text-gray-800 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-bold text-gray-800 uppercase">Department</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {logs.map((log) => (
                <motion.tr
                  key={log.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => setSelectedLog(log)}
                >
                  <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                    {formatTimestamp(log.timestamp)}
                  </td>
                  <td className="px-4 py-3">
                    <span className={clsx(
                      'px-2 py-1 text-xs rounded-full',
                      getActionColor(log.action)
                    )}>
                      {log.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-gray-600" />
                      <span className="text-gray-900 font-medium">{log.user_email || `User #${log.user_id}` || '-'}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate" title={log.details?.query}>
                    {log.details?.query ? (
                      <span className="italic">&quot;{log.details.query.substring(0, 40)}...&quot;</span>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(log.status)}
                      <span className={clsx(
                        'text-sm font-medium',
                        log.status === 'success' ? 'text-green-700' :
                        log.status === 'failure' ? 'text-red-700' : 'text-blue-700'
                      )}>
                        {log.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900 font-medium">
                    {log.details?.department || log.resource_type || '-'}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>

        {logs.length === 0 && (
          <div className="py-12 text-center">
            <FileText className="w-12 h-12 mx-auto mb-4 text-gray-500" />
            <p className="text-gray-700 font-medium">No audit logs found</p>
          </div>
        )}
      </div>

      {/* Log Details Modal */}
      {selectedLog && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setSelectedLog(null)}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl p-6 w-full max-w-lg z-50 shadow-2xl"
          >
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2 text-gray-900">
              <FileText className="w-5 h-5 text-gray-700" />
              Audit Log Details
            </h3>
            
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm font-semibold text-gray-700">Timestamp</span>
                  <p className="font-medium text-gray-900">{formatTimestamp(selectedLog.timestamp)}</p>
                </div>
                <div>
                  <span className="text-sm font-semibold text-gray-700">Action</span>
                  <p>
                    <span className={clsx('px-2 py-1 text-xs rounded-full', getActionColor(selectedLog.action))}>
                      {selectedLog.action}
                    </span>
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm font-semibold text-gray-700">User</span>
                  <p className="font-medium text-gray-900">{selectedLog.user_email || `User #${selectedLog.user_id}` || '-'}</p>
                </div>
                <div>
                  <span className="text-sm font-semibold text-gray-700">Department</span>
                  <p className="font-medium text-gray-900">{selectedLog.details?.department || '-'}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm font-semibold text-gray-700">IP Address</span>
                  <p className="font-medium text-gray-900">{selectedLog.ip_address || '-'}</p>
                </div>
                <div>
                  <span className="text-sm font-semibold text-gray-700">Status</span>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(selectedLog.status)}
                    <span className="font-medium text-gray-900">{selectedLog.status}</span>
                  </div>
                </div>
              </div>
              {selectedLog.details?.query && (
                <div>
                  <span className="text-sm font-semibold text-gray-700">User Query</span>
                  <p className="mt-1 p-3 bg-blue-50 rounded-lg text-sm text-gray-900 border border-blue-200">
                    {selectedLog.details.query}
                  </p>
                </div>
              )}
              {selectedLog.details?.response && (
                <div>
                  <span className="text-sm font-semibold text-gray-700">AI Response</span>
                  <p className="mt-1 p-3 bg-green-50 rounded-lg text-sm text-gray-900 border border-green-200 max-h-40 overflow-auto">
                    {selectedLog.details.response.substring(0, 500)}{selectedLog.details.response.length > 500 ? '...' : ''}
                  </p>
                </div>
              )}
              {selectedLog.details && !selectedLog.details.query && (
                <div>
                  <span className="text-sm font-semibold text-gray-700">Details</span>
                  <pre className="mt-1 p-3 bg-gray-100 rounded-lg text-xs overflow-auto max-h-40 text-gray-900">
                    {JSON.stringify(selectedLog.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
            
            <button
              onClick={() => setSelectedLog(null)}
              className="mt-6 w-full py-2 bg-gray-200 text-gray-900 font-medium rounded-lg hover:bg-gray-300"
            >
              Close
            </button>
          </motion.div>
        </>
      )}
    </div>
  );
}


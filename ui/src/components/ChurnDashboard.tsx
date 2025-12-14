'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  AlertTriangle,
  TrendingDown,
  Users,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  ChevronRight,
  MessageSquare,
} from 'lucide-react';
import { api } from '@/lib/api';
import clsx from 'clsx';

interface AtRiskUser {
  user_id: number;
  user_name: string;
  user_email: string;
  department: string;
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW' | 'CRITICAL';
  risk_score: number;
  factors?: {
    login_frequency: number;
    task_completion_rate: number;
    chat_engagement: number;
    training_progress: number;
    days_since_last_activity: number;
  };
  recommendations?: string[];
  predicted_at: string;
}

interface ChurnStats {
  total_users: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  avg_engagement_score: number;
}

interface ChurnDashboardProps {
  language?: 'en' | 'ar';
}

export default function ChurnDashboard({ language = 'en' }: ChurnDashboardProps) {
  const [atRiskUsers, setAtRiskUsers] = useState<AtRiskUser[]>([]);
  const [stats, setStats] = useState<ChurnStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedRisk, setSelectedRisk] = useState<string>('all');

  const t = {
    en: {
      title: 'Churn Risk Analysis',
      subtitle: 'Monitor at-risk employees and take action',
      refresh: 'Refresh Analysis',
      totalUsers: 'Total Users',
      highRisk: 'High Risk',
      mediumRisk: 'Medium Risk',
      lowRisk: 'Low Risk',
      avgEngagement: 'Avg. Engagement',
      atRiskUsers: 'At-Risk Users',
      allRisks: 'All Risks',
      riskScore: 'Risk Score',
      factors: {
        login_frequency: 'Login Frequency',
        task_completion_rate: 'Task Completion',
        chat_engagement: 'Chat Engagement',
        training_progress: 'Training Progress',
        days_since_last_activity: 'Days Inactive',
      },
      recommendations: 'Recommended Actions',
      noUsersAtRisk: 'No at-risk users found. Great job!',
      contact: 'Contact',
      viewProfile: 'View Profile',
    },
    ar: {
      title: 'تحليل مخاطر التسرب',
      subtitle: 'مراقبة الموظفين المعرضين للخطر واتخاذ إجراءات',
      refresh: 'تحديث التحليل',
      totalUsers: 'إجمالي المستخدمين',
      highRisk: 'خطر عالي',
      mediumRisk: 'خطر متوسط',
      lowRisk: 'خطر منخفض',
      avgEngagement: 'متوسط المشاركة',
      atRiskUsers: 'المستخدمون المعرضون للخطر',
      allRisks: 'جميع المخاطر',
      riskScore: 'درجة الخطر',
      factors: {
        login_frequency: 'تكرار تسجيل الدخول',
        task_completion_rate: 'معدل إكمال المهام',
        chat_engagement: 'تفاعل المحادثة',
        training_progress: 'تقدم التدريب',
        days_since_last_activity: 'أيام عدم النشاط',
      },
      recommendations: 'الإجراءات الموصى بها',
      noUsersAtRisk: 'لا يوجد مستخدمون معرضون للخطر. عمل رائع!',
      contact: 'تواصل',
      viewProfile: 'عرض الملف',
    },
  };

  const text = t[language];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [usersData] = await Promise.all([
        api.getAtRiskUsers(),
      ]);
      setAtRiskUsers(usersData);
      
      // Calculate stats
      const highRisk = usersData.filter((u: AtRiskUser) => u.risk_level === 'HIGH').length;
      const mediumRisk = usersData.filter((u: AtRiskUser) => u.risk_level === 'MEDIUM').length;
      const lowRisk = usersData.filter((u: AtRiskUser) => u.risk_level === 'LOW').length;
      const avgScore = usersData.length > 0 
        ? usersData.reduce((sum: number, u: AtRiskUser) => sum + u.risk_score, 0) / usersData.length 
        : 0;
      
      setStats({
        total_users: usersData.length,
        high_risk: highRisk,
        medium_risk: mediumRisk,
        low_risk: lowRisk,
        avg_engagement_score: avgScore,
      });
    } catch (error) {
      console.error('Failed to load churn data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const filteredUsers = atRiskUsers.filter((user) => {
    if (selectedRisk === 'all') return true;
    return user.risk_level === selectedRisk;
  });

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'HIGH':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-700 border-amber-200';
      case 'LOW':
        return 'bg-green-100 text-green-700 border-green-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getFactorStatus = (value: number, inverse: boolean = false) => {
    const threshold = inverse ? 0.5 : 0.5;
    const isGood = inverse ? value < threshold : value > threshold;
    return isGood ? 'text-green-600' : 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">{text.title}</h2>
          <p className="text-slate-600">{text.subtitle}</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-xl transition-colors disabled:opacity-50"
        >
          <RefreshCw className={clsx('w-4 h-4', refreshing && 'animate-spin')} />
          {text.refresh}
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-xl">
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">{text.totalUsers}</p>
                <p className="text-2xl font-bold text-slate-900">{stats.total_users}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-2xl shadow-sm border border-red-100 p-4"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-xl">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">{text.highRisk}</p>
                <p className="text-2xl font-bold text-red-600">{stats.high_risk}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-2xl shadow-sm border border-amber-100 p-4"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-xl">
                <TrendingDown className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">{text.mediumRisk}</p>
                <p className="text-2xl font-bold text-amber-600">{stats.medium_risk}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-2xl shadow-sm border border-green-100 p-4"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-xl">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">{text.lowRisk}</p>
                <p className="text-2xl font-bold text-green-600">{stats.low_risk}</p>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-2xl shadow-sm border border-slate-100 p-4"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-xl">
                <Activity className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">{text.avgEngagement}</p>
                <p className="text-2xl font-bold text-slate-900">
                  {(stats.avg_engagement_score * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 flex-wrap">
        {['all', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((risk) => (
          <button
            key={risk}
            onClick={() => setSelectedRisk(risk)}
            className={clsx(
              'px-4 py-2 rounded-xl text-sm font-medium transition-colors',
              selectedRisk === risk
                ? 'bg-primary-500 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            )}
          >
            {risk === 'all' ? text.allRisks : 
             risk === 'CRITICAL' ? 'Critical' :
             risk === 'HIGH' ? text.highRisk : 
             risk === 'MEDIUM' ? text.mediumRisk : text.lowRisk}
          </button>
        ))}
      </div>

      {/* At-Risk Users List */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-slate-900">{text.atRiskUsers}</h3>
        
        {filteredUsers.length === 0 ? (
          <div className="text-center py-12 bg-green-50 rounded-2xl border border-green-100">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <p className="text-green-700">{text.noUsersAtRisk}</p>
          </div>
        ) : (
          filteredUsers.map((user, index) => (
            <motion.div
              key={user.user_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className={clsx(
                'bg-white rounded-2xl shadow-sm border p-6',
                user.risk_level === 'CRITICAL' && 'border-purple-300 bg-purple-50/30',
                user.risk_level === 'HIGH' && 'border-red-200',
                user.risk_level === 'MEDIUM' && 'border-amber-200',
                user.risk_level === 'LOW' && 'border-green-200'
              )}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white font-semibold text-lg">
                    {user.user_name?.charAt(0) || '?'}
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900">{user.user_name}</h4>
                    <p className="text-sm text-slate-500">{user.user_email}</p>
                    <p className="text-xs text-gray-400">{user.department}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className={clsx(
                    'px-3 py-1 rounded-full text-sm font-medium border',
                    getRiskColor(user.risk_level)
                  )}>
                    {user.risk_level === 'CRITICAL' ? 'Critical' : user.risk_level === 'HIGH' ? text.highRisk : user.risk_level === 'MEDIUM' ? text.mediumRisk : text.lowRisk}
                  </span>
                  <p className="text-sm text-slate-500 mt-1">
                    {text.riskScore}: {((user.risk_score ?? 0) * 100).toFixed(0)}%
                  </p>
                </div>
              </div>

              {/* Risk Factors */}
              {user.factors && (
              <div className="grid grid-cols-5 gap-4 mb-4">
                <div className="text-center p-3 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-500 mb-1">{text.factors.login_frequency}</p>
                  <p className={clsx('font-semibold', getFactorStatus(user.factors?.login_frequency ?? 0))}>
                    {((user.factors?.login_frequency ?? 0) * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-500 mb-1">{text.factors.task_completion_rate}</p>
                  <p className={clsx('font-semibold', getFactorStatus(user.factors?.task_completion_rate ?? 0))}>
                    {((user.factors?.task_completion_rate ?? 0) * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-500 mb-1">{text.factors.chat_engagement}</p>
                  <p className={clsx('font-semibold', getFactorStatus(user.factors?.chat_engagement ?? 0))}>
                    {((user.factors?.chat_engagement ?? 0) * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-500 mb-1">{text.factors.training_progress}</p>
                  <p className={clsx('font-semibold', getFactorStatus(user.factors?.training_progress ?? 0))}>
                    {((user.factors?.training_progress ?? 0) * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-xl">
                  <p className="text-xs text-slate-500 mb-1">{text.factors.days_since_last_activity}</p>
                  <p className={clsx('font-semibold', getFactorStatus((user.factors?.days_since_last_activity ?? 0) / 30, true))}>
                    {user.factors?.days_since_last_activity ?? 0}d
                  </p>
                </div>
              </div>
              )}

              {/* Recommendations */}
              {user.recommendations && user.recommendations.length > 0 && (
                <div className="bg-blue-50 rounded-xl p-4">
                  <p className="text-sm font-medium text-blue-900 mb-2">{text.recommendations}:</p>
                  <ul className="space-y-1">
                    {user.recommendations.map((rec, idx) => (
                      <li key={idx} className="text-sm text-blue-700 flex items-start gap-2">
                        <ChevronRight className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end gap-3 mt-4 pt-4 border-t border-slate-100">
                <button className="flex items-center gap-2 px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-xl transition-colors">
                  <MessageSquare className="w-4 h-4" />
                  {text.contact}
                </button>
                <button className="flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-xl transition-colors">
                  {text.viewProfile}
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}


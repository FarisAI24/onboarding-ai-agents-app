'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare,
  CheckSquare,
  LayoutDashboard,
  LogOut,
  Sparkles,
  Shield,
  GraduationCap,
  Trophy,
  Calendar,
  Globe,
  FileText,
  HelpCircle,
  AlertTriangle,
} from 'lucide-react';
import ChatInterface from '@/components/ChatInterface';
import TaskList from '@/components/TaskList';
import AdminDashboard from '@/components/AdminDashboard';
import LoginForm from '@/components/LoginForm';
import RegisterForm from '@/components/RegisterForm';
import AchievementsPanel from '@/components/AchievementsPanel';
import TrainingModules from '@/components/TrainingModules';
import AuditLogExplorer from '@/components/AuditLogExplorer';
import CalendarView from '@/components/CalendarView';
import FAQManagement from '@/components/FAQManagement';
import ChurnDashboard from '@/components/ChurnDashboard';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { api, User as UserType, ChatMessage } from '@/lib/api';
import clsx from 'clsx';

type View = 'chat' | 'tasks' | 'training' | 'achievements' | 'calendar' | 'admin' | 'audit' | 'faqs' | 'churn';
type AuthView = 'login' | 'register';

export default function Home() {
  const { user, isLoading: authLoading, isAuthenticated, logout, isAdmin } = useAuth();
  const { t, language } = useI18n();
  const [currentUser, setCurrentUser] = useState<UserType | null>(null);
  const [view, setView] = useState<View>('chat');
  const [authView, setAuthView] = useState<AuthView>('login');
  const [taskRefresh, setTaskRefresh] = useState(0);
  const [loadingUser, setLoadingUser] = useState(false);
  // Chat messages state lifted here to persist across tab switches (but clears on page refresh)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);

  // Fetch full user data when authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      setLoadingUser(true);
      api.getUser(user.id)
        .then((userData) => {
          setCurrentUser(userData);
        })
        .catch((error) => {
          console.error('Failed to get user data:', error);
        })
        .finally(() => {
          setLoadingUser(false);
        });
    } else {
      setCurrentUser(null);
    }
  }, [isAuthenticated, user]);

  const handleLogout = async () => {
    await logout();
    setCurrentUser(null);
    setView('chat');
  };

  const handleTaskUpdate = () => {
    setTaskRefresh((prev) => prev + 1);
  };

  // Loading state
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-gray-700 dark:text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  // Auth screens (login/register)
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <AnimatePresence mode="wait">
          {authView === 'login' ? (
            <motion.div
              key="login"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <LoginForm
                onSuccess={() => {}}
                onSwitchToRegister={() => setAuthView('register')}
              />
            </motion.div>
          ) : (
            <motion.div
              key="register"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <RegisterForm
                onSuccess={() => setAuthView('login')}
                onSwitchToLogin={() => setAuthView('login')}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // Loading user data
  if (loadingUser || !currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-gray-700 dark:text-gray-500">Loading user data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex overflow-hidden">
      {/* Sidebar */}
      <motion.aside
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="w-64 bg-white/60 dark:bg-surface-800/60 backdrop-blur-xl border-r border-surface-200/50 dark:border-surface-700/50 flex flex-col flex-shrink-0"
      >
        {/* Logo */}
        <div className="p-6 border-b border-surface-200/50 dark:border-surface-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-gray-950 dark:text-surface-100">Copilot</h1>
              <p className="text-xs text-gray-600">Onboarding Assistant</p>
            </div>
          </div>
        </div>

        {/* User Info */}
        <div className="p-4 border-b border-surface-200/50 dark:border-surface-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white font-semibold">
              {currentUser?.name?.charAt(0) || '?'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-950 dark:text-surface-100 truncate">
                {currentUser?.name || 'User'}
              </p>
              <p className="text-xs text-gray-600 truncate">{currentUser?.role || ''}</p>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <RoleBadge role={user?.user_type || 'new_hire'} />
            <span className="px-2 py-1 text-xs bg-surface-100 dark:bg-surface-700 text-gray-700 dark:text-gray-500 rounded-full">
              {currentUser?.department || ''}
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          <NavButton
            icon={<MessageSquare className="w-5 h-5" />}
            label={t('chat')}
            active={view === 'chat'}
            onClick={() => setView('chat')}
          />
          <NavButton
            icon={<CheckSquare className="w-5 h-5" />}
            label={t('tasks')}
            active={view === 'tasks'}
            onClick={() => setView('tasks')}
          />
          <NavButton
            icon={<GraduationCap className="w-5 h-5" />}
            label={t('training')}
            active={view === 'training'}
            onClick={() => setView('training')}
          />
          <NavButton
            icon={<Trophy className="w-5 h-5" />}
            label={t('achievements')}
            active={view === 'achievements'}
            onClick={() => setView('achievements')}
          />
          <NavButton
            icon={<Calendar className="w-5 h-5" />}
            label={t('calendar')}
            active={view === 'calendar'}
            onClick={() => setView('calendar')}
          />
          {isAdmin && (
            <>
              <div className="pt-4 pb-2">
                <p className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('admin')}</p>
              </div>
              <NavButton
                icon={<LayoutDashboard className="w-5 h-5" />}
                label={language === 'ar' ? 'لوحة التحكم' : 'Dashboard'}
                active={view === 'admin'}
                onClick={() => setView('admin')}
                badge={<Shield className="w-3 h-3" />}
              />
              <NavButton
                icon={<HelpCircle className="w-5 h-5" />}
                label={language === 'ar' ? 'إدارة الأسئلة' : 'FAQ Management'}
                active={view === 'faqs'}
                onClick={() => setView('faqs')}
              />
              <NavButton
                icon={<AlertTriangle className="w-5 h-5" />}
                label={language === 'ar' ? 'تحليل التسرب' : 'Churn Analysis'}
                active={view === 'churn'}
                onClick={() => setView('churn')}
              />
              <NavButton
                icon={<FileText className="w-5 h-5" />}
                label={language === 'ar' ? 'سجلات التدقيق' : 'Audit Logs'}
                active={view === 'audit'}
                onClick={() => setView('audit')}
              />
            </>
          )}
        </nav>

        {/* User Menu */}
        <div className="p-4 border-t border-surface-200/50 dark:border-surface-700/50 space-y-2">
          {/* Language Switcher */}
          <div className="px-4 py-2">
            <LanguageSwitcher />
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 text-gray-700 dark:text-gray-500 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 rounded-xl transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>{t('logout')}</span>
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <AnimatePresence mode="wait">
          {view === 'chat' && (
            <motion.div
              key="chat"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex-1 p-6 overflow-hidden flex flex-col"
            >
              {/* Fixed height container for chat - takes full available space */}
              <div className="flex-1 max-w-4xl mx-auto w-full min-h-0">
                <ChatInterface
                  userId={currentUser.id}
                  userName={currentUser.name}
                  onTaskUpdate={handleTaskUpdate}
                  messages={chatMessages}
                  setMessages={setChatMessages}
                />
              </div>
            </motion.div>
          )}

          {view === 'tasks' && (
            <motion.div
              key="tasks"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex-1 p-6 overflow-auto"
            >
              <div className="max-w-4xl mx-auto">
                <TaskList userId={currentUser.id} refreshTrigger={taskRefresh} />
              </div>
            </motion.div>
          )}

          {view === 'training' && (
            <motion.div
              key="training"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex-1 p-6 overflow-auto"
            >
              <div className="max-w-4xl mx-auto">
                <h2 className="text-2xl font-bold mb-6 text-gray-950 dark:text-surface-100">
                  Training Modules
                </h2>
                <TrainingModules />
              </div>
            </motion.div>
          )}

          {view === 'achievements' && (
            <motion.div
              key="achievements"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex-1 p-6 overflow-auto"
            >
              <div className="max-w-4xl mx-auto">
                <h2 className="text-2xl font-bold mb-6 text-gray-950 dark:text-surface-100">
                  Achievements & Rewards
                </h2>
                <AchievementsPanel />
              </div>
            </motion.div>
          )}

          {view === 'admin' && isAdmin && (
            <motion.div
              key="admin"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex-1 p-6 overflow-auto"
            >
              <div className="max-w-6xl mx-auto">
                <AdminDashboard />
              </div>
            </motion.div>
          )}

          {view === 'calendar' && (
            <motion.div
              key="calendar"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex-1 p-6 overflow-auto"
            >
              <div className="max-w-6xl mx-auto">
                <CalendarView />
              </div>
            </motion.div>
          )}

          {view === 'faqs' && isAdmin && (
            <motion.div
              key="faqs"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex-1 p-6 overflow-auto"
            >
              <div className="max-w-6xl mx-auto">
                <FAQManagement />
              </div>
            </motion.div>
          )}

          {view === 'churn' && isAdmin && (
            <motion.div
              key="churn"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex-1 p-6 overflow-auto"
            >
              <div className="max-w-6xl mx-auto">
                <ChurnDashboard />
              </div>
            </motion.div>
          )}

          {view === 'audit' && isAdmin && (
            <motion.div
              key="audit"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex-1 p-6 overflow-auto"
            >
              <div className="max-w-6xl mx-auto">
                <h2 className="text-2xl font-bold mb-6 text-gray-950 dark:text-surface-100">
                  Audit Log Explorer
                </h2>
                <AuditLogExplorer />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

interface NavButtonProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
  badge?: React.ReactNode;
}

function NavButton({ icon, label, active, onClick, badge }: NavButtonProps) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all',
        active
          ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white shadow-lg shadow-primary-500/25'
          : 'text-gray-700 dark:text-gray-500 hover:bg-surface-100 dark:hover:bg-surface-700/50'
      )}
    >
      {icon}
      <span className="font-medium flex-1 text-left">{label}</span>
      {badge && (
        <span className={clsx(
          'p-1 rounded',
          active ? 'bg-white/20' : 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400'
        )}>
          {badge}
        </span>
      )}
    </button>
  );
}

function RoleBadge({ role }: { role: string }) {
  const roleStyles: Record<string, string> = {
    new_hire: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
    employee: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
    manager: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
    hr_admin: 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300',
    it_admin: 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300',
    security_admin: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300',
    admin: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
    super_admin: 'bg-gradient-to-r from-red-500 to-purple-500 text-white',
  };

  const roleLabels: Record<string, string> = {
    new_hire: 'New Hire',
    employee: 'Employee',
    manager: 'Manager',
    hr_admin: 'HR Admin',
    it_admin: 'IT Admin',
    security_admin: 'Security',
    admin: 'Admin',
    super_admin: 'Super Admin',
  };

  return (
    <span className={clsx('px-2 py-1 text-xs rounded-full font-medium', roleStyles[role] || roleStyles.new_hire)}>
      {roleLabels[role] || role}
    </span>
  );
}

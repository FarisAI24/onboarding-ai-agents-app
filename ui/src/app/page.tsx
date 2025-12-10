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
  Settings,
  User as UserIcon,
} from 'lucide-react';
import ChatInterface from '@/components/ChatInterface';
import TaskList from '@/components/TaskList';
import AdminDashboard from '@/components/AdminDashboard';
import LoginForm from '@/components/LoginForm';
import RegisterForm from '@/components/RegisterForm';
import { useAuth } from '@/lib/auth-context';
import { api, User as UserType } from '@/lib/api';
import clsx from 'clsx';

type View = 'chat' | 'tasks' | 'admin';
type AuthView = 'login' | 'register';

export default function Home() {
  const { user, isLoading: authLoading, isAuthenticated, logout, isAdmin } = useAuth();
  const [currentUser, setCurrentUser] = useState<UserType | null>(null);
  const [view, setView] = useState<View>('chat');
  const [authView, setAuthView] = useState<AuthView>('login');
  const [taskRefresh, setTaskRefresh] = useState(0);
  const [loadingUser, setLoadingUser] = useState(false);

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
          <p className="mt-4 text-surface-600 dark:text-surface-400">Loading...</p>
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
          <p className="mt-4 text-surface-600 dark:text-surface-400">Loading user data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <motion.aside
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="w-64 bg-white/60 dark:bg-surface-800/60 backdrop-blur-xl border-r border-surface-200/50 dark:border-surface-700/50 flex flex-col"
      >
        {/* Logo */}
        <div className="p-6 border-b border-surface-200/50 dark:border-surface-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-surface-900 dark:text-surface-100">Copilot</h1>
              <p className="text-xs text-surface-500">Onboarding Assistant</p>
            </div>
          </div>
        </div>

        {/* User Info */}
        <div className="p-4 border-b border-surface-200/50 dark:border-surface-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-400 to-accent-400 flex items-center justify-center text-white font-semibold">
              {currentUser.name.charAt(0)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-surface-900 dark:text-surface-100 truncate">
                {currentUser.name}
              </p>
              <p className="text-xs text-surface-500 truncate">{currentUser.role}</p>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <RoleBadge role={user?.user_type || 'new_hire'} />
            <span className="px-2 py-1 text-xs bg-surface-100 dark:bg-surface-700 text-surface-600 dark:text-surface-400 rounded-full">
              {currentUser.department}
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          <NavButton
            icon={<MessageSquare className="w-5 h-5" />}
            label="Chat"
            active={view === 'chat'}
            onClick={() => setView('chat')}
          />
          <NavButton
            icon={<CheckSquare className="w-5 h-5" />}
            label="Tasks"
            active={view === 'tasks'}
            onClick={() => setView('tasks')}
          />
          {isAdmin && (
            <NavButton
              icon={<LayoutDashboard className="w-5 h-5" />}
              label="Admin Dashboard"
              active={view === 'admin'}
              onClick={() => setView('admin')}
              badge={<Shield className="w-3 h-3" />}
            />
          )}
        </nav>

        {/* User Menu */}
        <div className="p-4 border-t border-surface-200/50 dark:border-surface-700/50 space-y-2">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 text-surface-600 dark:text-surface-400 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 rounded-xl transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>Logout</span>
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
              className="flex-1 p-6 overflow-hidden"
            >
              <div className="h-full max-w-4xl mx-auto">
                <ChatInterface
                  userId={currentUser.id}
                  userName={currentUser.name}
                  onTaskUpdate={handleTaskUpdate}
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
          : 'text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-700/50'
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

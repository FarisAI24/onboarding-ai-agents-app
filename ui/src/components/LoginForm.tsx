'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Lock, LogIn, UserPlus, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import clsx from 'clsx';

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
}

export default function LoginForm({ onSuccess, onSwitchToRegister }: LoginFormProps) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login({ email, password });
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-md"
    >
      <div className="bg-surface-50 dark:bg-surface-800 rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 mb-4">
            <LogIn className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-950 dark:text-surface-100">
            Welcome Back
          </h2>
          <p className="text-gray-700 dark:text-gray-500 mt-2">
            Sign in to your account
          </p>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-3"
          >
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </motion.div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-800 dark:text-surface-300 mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@company.com"
                className={clsx(
                  'w-full pl-10 pr-4 py-3 rounded-lg border transition-colors',
                  'bg-white dark:bg-surface-700',
                  'border-surface-200 dark:border-surface-600',
                  'text-gray-950 dark:text-surface-100',
                  'placeholder-surface-400',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
                )}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-800 dark:text-surface-300 mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                placeholder="••••••••"
                className={clsx(
                  'w-full pl-10 pr-4 py-3 rounded-lg border transition-colors',
                  'bg-white dark:bg-surface-700',
                  'border-surface-200 dark:border-surface-600',
                  'text-gray-950 dark:text-surface-100',
                  'placeholder-surface-400',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
                )}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={clsx(
              'w-full py-3 px-4 rounded-lg font-medium transition-all',
              'bg-gradient-to-r from-primary-500 to-primary-600',
              'text-white shadow-lg shadow-primary-500/25',
              'hover:shadow-xl hover:shadow-primary-500/30',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'flex items-center justify-center gap-2'
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                <LogIn className="w-5 h-5" />
                Sign In
              </>
            )}
          </button>
        </form>

        {onSwitchToRegister && (
          <div className="mt-6 text-center">
            <p className="text-gray-700 dark:text-gray-500">
              Don't have an account?{' '}
              <button
                onClick={onSwitchToRegister}
                className="text-primary-500 hover:text-primary-600 font-medium"
              >
                Register
              </button>
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
}


'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, Lock, User, Building2, Briefcase, UserPlus, AlertCircle, Loader2, CheckCircle } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import clsx from 'clsx';

interface RegisterFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
}

const DEPARTMENTS = ['Engineering', 'Sales', 'Marketing', 'Operations', 'Finance', 'HR', 'Legal'];

export default function RegisterForm({ onSuccess, onSwitchToLogin }: RegisterFormProps) {
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: '',
    department: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      await register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        role: formData.role,
        department: formData.department,
      });
      setSuccess(true);
      setTimeout(() => {
        onSuccess?.();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md"
      >
        <div className="bg-surface-50 dark:bg-surface-800 rounded-2xl shadow-xl p-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 mb-4">
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
          <h2 className="text-2xl font-bold text-surface-900 dark:text-surface-100">
            Registration Successful!
          </h2>
          <p className="text-surface-600 dark:text-surface-400 mt-2">
            Redirecting to login...
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-md"
    >
      <div className="bg-surface-50 dark:bg-surface-800 rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 mb-4">
            <UserPlus className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-surface-900 dark:text-surface-100">
            Create Account
          </h2>
          <p className="text-surface-600 dark:text-surface-400 mt-2">
            Join the team
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

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
              Full Name
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="John Doe"
                className={clsx(
                  'w-full pl-10 pr-4 py-3 rounded-lg border transition-colors',
                  'bg-white dark:bg-surface-700',
                  'border-surface-200 dark:border-surface-600',
                  'text-surface-900 dark:text-surface-100',
                  'placeholder-surface-400',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
                )}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="you@company.com"
                className={clsx(
                  'w-full pl-10 pr-4 py-3 rounded-lg border transition-colors',
                  'bg-white dark:bg-surface-700',
                  'border-surface-200 dark:border-surface-600',
                  'text-surface-900 dark:text-surface-100',
                  'placeholder-surface-400',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
                )}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
                Job Role
              </label>
              <div className="relative">
                <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
                <input
                  type="text"
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  required
                  placeholder="Software Engineer"
                  className={clsx(
                    'w-full pl-10 pr-4 py-3 rounded-lg border transition-colors',
                    'bg-white dark:bg-surface-700',
                    'border-surface-200 dark:border-surface-600',
                    'text-surface-900 dark:text-surface-100',
                    'placeholder-surface-400',
                    'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
                  )}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
                Department
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
                <select
                  name="department"
                  value={formData.department}
                  onChange={handleChange}
                  required
                  className={clsx(
                    'w-full pl-10 pr-4 py-3 rounded-lg border transition-colors appearance-none',
                    'bg-white dark:bg-surface-700',
                    'border-surface-200 dark:border-surface-600',
                    'text-surface-900 dark:text-surface-100',
                    'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
                  )}
                >
                  <option value="">Select...</option>
                  {DEPARTMENTS.map(dept => (
                    <option key={dept} value={dept}>{dept}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                minLength={8}
                placeholder="••••••••"
                className={clsx(
                  'w-full pl-10 pr-4 py-3 rounded-lg border transition-colors',
                  'bg-white dark:bg-surface-700',
                  'border-surface-200 dark:border-surface-600',
                  'text-surface-900 dark:text-surface-100',
                  'placeholder-surface-400',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
                )}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
              Confirm Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400" />
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                minLength={8}
                placeholder="••••••••"
                className={clsx(
                  'w-full pl-10 pr-4 py-3 rounded-lg border transition-colors',
                  'bg-white dark:bg-surface-700',
                  'border-surface-200 dark:border-surface-600',
                  'text-surface-900 dark:text-surface-100',
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
                Creating account...
              </>
            ) : (
              <>
                <UserPlus className="w-5 h-5" />
                Create Account
              </>
            )}
          </button>
        </form>

        {onSwitchToLogin && (
          <div className="mt-6 text-center">
            <p className="text-surface-600 dark:text-surface-400">
              Already have an account?{' '}
              <button
                onClick={onSwitchToLogin}
                className="text-primary-500 hover:text-primary-600 font-medium"
              >
                Sign In
              </button>
            </p>
          </div>
        )}
      </div>
    </motion.div>
  );
}


'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Star, Lock, Sparkles, Medal } from 'lucide-react';
import { api } from '@/lib/api';
import clsx from 'clsx';

interface Achievement {
  id: number;
  name: string;
  name_ar?: string;
  description: string;
  description_ar?: string;
  icon: string;
  category: string;
  points: number;
  unlocked: boolean;
  progress: number;
  unlocked_at?: string;
}

interface AchievementsPanelProps {
  language?: 'en' | 'ar';
}

export default function AchievementsPanel({ language = 'en' }: AchievementsPanelProps) {
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [points, setPoints] = useState(0);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'unlocked' | 'leaderboard'>('all');
  const [newAchievement, setNewAchievement] = useState<Achievement | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setError(null);
    try {
      // Load achievements first
      const achievementsData = await api.getAchievements(true);
      setAchievements(achievementsData || []);
      
      // Try to load points (may fail if endpoint doesn't exist)
      try {
        const pointsData = await api.getAchievementPoints();
        setPoints(pointsData?.points || 0);
      } catch {
        // Calculate points from achievements
        const totalPoints = (achievementsData || [])
          .filter((a: Achievement) => a.unlocked)
          .reduce((sum: number, a: Achievement) => sum + a.points, 0);
        setPoints(totalPoints);
      }
      
      // Try to load leaderboard
      try {
        const leaderboardData = await api.getLeaderboard(10);
        setLeaderboard(leaderboardData || []);
      } catch {
        setLeaderboard([]);
      }
    } catch (err) {
      console.error('Failed to load achievements:', err);
      setError('Failed to load achievements. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      onboarding: 'from-blue-500 to-blue-600',
      learning: 'from-purple-500 to-purple-600',
      engagement: 'from-green-500 to-green-600',
      speed: 'from-amber-500 to-amber-600',
      social: 'from-pink-500 to-pink-600',
    };
    return colors[category] || 'from-gray-500 to-gray-600';
  };

  const unlockedCount = achievements.filter(a => a.unlocked).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <p className="text-red-700 font-medium">{error}</p>
        <button 
          onClick={loadData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* New Achievement Toast */}
      <AnimatePresence>
        {newAchievement && (
          <motion.div
            initial={{ opacity: 0, y: -50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -50, scale: 0.9 }}
            className="fixed top-4 right-4 z-50 bg-gradient-to-r from-amber-400 to-yellow-500 p-4 rounded-2xl shadow-2xl"
          >
            <div className="flex items-center gap-3 text-white">
              <Sparkles className="w-8 h-8 animate-pulse" />
              <div>
                <p className="font-bold">Achievement Unlocked!</p>
                <p className="text-sm opacity-90">
                  {newAchievement.icon} {language === 'ar' && newAchievement.name_ar ? newAchievement.name_ar : newAchievement.name}
                </p>
                <p className="text-xs opacity-75">+{newAchievement.points} points</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Points Summary */}
      <div className="bg-gradient-to-r from-amber-500 to-yellow-500 rounded-2xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Trophy className="w-6 h-6" />
              {points} {language === 'ar' ? 'نقاط' : 'Points'}
            </h2>
            <p className="text-white/80">
              {unlockedCount} / {achievements.length} {language === 'ar' ? 'إنجازات مفتوحة' : 'Achievements Unlocked'}
            </p>
          </div>
          <div className="text-6xl">{unlockedCount > 10 ? '🏆' : unlockedCount > 5 ? '⭐' : '🎯'}</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {[
          { id: 'all', label: language === 'ar' ? 'الكل' : 'All' },
          { id: 'unlocked', label: language === 'ar' ? 'المفتوحة' : 'Unlocked' },
          { id: 'leaderboard', label: language === 'ar' ? 'المتصدرين' : 'Leaderboard' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={clsx(
              'px-4 py-2 font-medium transition-colors border-b-2 -mb-px',
              activeTab === tab.id
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'leaderboard' ? (
        <div className="space-y-3">
          {leaderboard.map((user, index) => (
            <motion.div
              key={user.user_id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={clsx(
                'flex items-center gap-4 p-4 rounded-xl',
                index === 0 ? 'bg-amber-50 border border-amber-200' :
                index === 1 ? 'bg-slate-50 border border-slate-200' :
                index === 2 ? 'bg-orange-50 border border-orange-200' :
                'bg-gray-50 border border-gray-200'
              )}
            >
              <div className={clsx(
                'w-10 h-10 rounded-full flex items-center justify-center font-bold',
                index === 0 ? 'bg-amber-500 text-white' :
                index === 1 ? 'bg-slate-400 text-white' :
                index === 2 ? 'bg-orange-400 text-white' :
                'bg-gray-300 text-gray-700'
              )}>
                {index + 1}
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-900">{user.name}</p>
                <p className="text-sm text-gray-600">
                  {user.achievement_count} achievements
                </p>
              </div>
              <div className="flex items-center gap-1 text-amber-600 font-bold">
                <Star className="w-4 h-4 fill-current" />
                {user.total_points}
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {achievements
            .filter(a => activeTab === 'all' || a.unlocked)
            // Sort: locked first in "all" tab, by points in "unlocked" tab
            .sort((a, b) => {
              if (activeTab === 'all') {
                // Locked first, then unlocked
                if (a.unlocked === b.unlocked) return b.points - a.points;
                return a.unlocked ? 1 : -1;
              }
              // In unlocked tab, sort by points
              return b.points - a.points;
            })
            .map((achievement, index) => {
              // Determine if this achievement should be shown as muted
              // In "all" tab: unlocked achievements are muted
              // In "unlocked" tab: nothing is muted (full vibrant)
              const isMuted = activeTab === 'all' && achievement.unlocked;
              const isLocked = !achievement.unlocked;
              const isVibrant = activeTab === 'unlocked' || (!achievement.unlocked && activeTab === 'all');
              
              return (
                <motion.div
                  key={achievement.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={clsx(
                    'relative p-4 rounded-xl border transition-all',
                    isLocked && 'bg-white border-gray-200 shadow-md',
                    isMuted && 'bg-gray-100 border-gray-200 opacity-60',
                    !isLocked && !isMuted && 'bg-gradient-to-br from-white to-amber-50 border-amber-200 shadow-lg'
                  )}
                >
                  {isLocked && (
                    <div className="absolute top-2 right-2">
                      <Lock className="w-4 h-4 text-gray-500" />
                    </div>
                  )}
                  {isMuted && (
                    <div className="absolute top-2 right-2">
                      <Sparkles className="w-4 h-4 text-gray-400" />
                    </div>
                  )}
                  {!isLocked && !isMuted && (
                    <div className="absolute top-2 right-2">
                      <Sparkles className="w-4 h-4 text-amber-500" />
                    </div>
                  )}
                  
                  <div className="flex items-start gap-3">
                    <div className={clsx(
                      'w-12 h-12 rounded-xl flex items-center justify-center text-2xl',
                      isLocked && `bg-gradient-to-br ${getCategoryColor(achievement.category)} text-white`,
                      isMuted && 'bg-gray-300',
                      !isLocked && !isMuted && `bg-gradient-to-br ${getCategoryColor(achievement.category)} text-white shadow-lg`
                    )}>
                      {isLocked ? '🔒' : achievement.icon}
                    </div>
                    
                    <div className="flex-1">
                      <h3 className={clsx(
                        'font-medium',
                        isMuted ? 'text-gray-500' : 'text-gray-900'
                      )}>
                        {language === 'ar' && achievement.name_ar ? achievement.name_ar : achievement.name}
                      </h3>
                      <p className={clsx(
                        'text-sm',
                        isMuted ? 'text-gray-400' : 'text-gray-600'
                      )}>
                        {language === 'ar' && achievement.description_ar ? achievement.description_ar : achievement.description}
                      </p>
                      
                      {isLocked && achievement.progress > 0 && (
                        <div className="mt-2">
                          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary-500 transition-all"
                              style={{ width: `${achievement.progress}%` }}
                            />
                          </div>
                          <p className="text-xs text-gray-500 mt-1">{Math.round(achievement.progress)}% complete</p>
                        </div>
                      )}
                      
                      {!isLocked && !isMuted && achievement.unlocked_at && (
                        <p className="text-xs text-amber-600 mt-1">
                          ✓ Unlocked {new Date(achievement.unlocked_at).toLocaleDateString()}
                        </p>
                      )}
                      
                      <div className="flex items-center gap-2 mt-2">
                        <span className={clsx(
                          'px-2 py-0.5 text-xs rounded-full',
                          isMuted 
                            ? 'bg-gray-200 text-gray-500'
                            : `bg-gradient-to-r ${getCategoryColor(achievement.category)} text-white`
                        )}>
                          {achievement.category}
                        </span>
                        <span className={clsx(
                          'text-xs font-medium flex items-center gap-1',
                          isMuted ? 'text-gray-400' : 'text-amber-600'
                        )}>
                          <Medal className="w-3 h-3" />
                          {achievement.points} pts
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
        </div>
      )}
    </div>
  );
}


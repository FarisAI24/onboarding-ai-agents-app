'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  GraduationCap, Play, Check, Clock, BookOpen, 
  ChevronRight, Trophy, RefreshCw, AlertCircle 
} from 'lucide-react';
import { api } from '@/lib/api';
import clsx from 'clsx';

interface TrainingModule {
  id: number;
  title: string;
  title_ar?: string;
  description?: string;
  department: string;
  duration_minutes: number;
  passing_score: number;
  is_required: boolean;
  order_index: number;
  content?: any;
}

interface TrainingProgress {
  module_id: number;
  module_title: string;
  status: string;
  current_step: number;
  score?: number;
  attempts: number;
}

interface TrainingModulesProps {
  language?: 'en' | 'ar';
}

export default function TrainingModules({ language = 'en' }: TrainingModulesProps) {
  const [modules, setModules] = useState<TrainingModule[]>([]);
  const [progress, setProgress] = useState<TrainingProgress[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [selectedModule, setSelectedModule] = useState<TrainingModule | null>(null);
  const [moduleContent, setModuleContent] = useState<any>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [quizAnswers, setQuizAnswers] = useState<number[]>([]);
  const [quizResult, setQuizResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [modulesData, progressData, summaryData] = await Promise.all([
        api.getTrainingModules(),
        api.getTrainingProgress(),
        api.getTrainingSummary(),
      ]);
      
      setModules(modulesData);
      setProgress(progressData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to load training data:', error);
    } finally {
      setLoading(false);
    }
  };

  const startModule = async (module: TrainingModule) => {
    try {
      await api.startTrainingModule(module.id);
      const content = await api.getTrainingModule(module.id, language);
      setModuleContent(content);
      setSelectedModule(module);
      setCurrentStep(0);
      setQuizAnswers([]);
      setQuizResult(null);
    } catch (error) {
      console.error('Failed to start module:', error);
    }
  };

  const nextStep = async () => {
    if (!moduleContent || !selectedModule) return;
    
    const sections = moduleContent.content?.sections || [];
    const quiz = moduleContent.content?.quiz || [];
    const totalSteps = sections.length + (quiz.length > 0 ? 1 : 0);
    
    if (currentStep < totalSteps - 1) {
      const newStep = currentStep + 1;
      setCurrentStep(newStep);
      await api.updateTrainingProgress(selectedModule.id, newStep);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleQuizAnswer = (questionIndex: number, answerIndex: number) => {
    const newAnswers = [...quizAnswers];
    newAnswers[questionIndex] = answerIndex;
    setQuizAnswers(newAnswers);
  };

  const submitQuiz = async () => {
    if (!selectedModule) return;
    
    try {
      const result = await api.submitQuiz(selectedModule.id, quizAnswers);
      setQuizResult(result);
      await loadData(); // Refresh progress
    } catch (error) {
      console.error('Failed to submit quiz:', error);
    }
  };

  const closeModule = () => {
    setSelectedModule(null);
    setModuleContent(null);
    setCurrentStep(0);
    setQuizAnswers([]);
    setQuizResult(null);
  };

  const getModuleProgress = (moduleId: number) => {
    return progress.find(p => p.module_id === moduleId);
  };

  const getDepartmentColor = (dept: string) => {
    const colors: Record<string, string> = {
      HR: 'from-pink-500 to-rose-500',
      IT: 'from-blue-500 to-cyan-500',
      Security: 'from-amber-500 to-orange-500',
      Finance: 'from-green-500 to-emerald-500',
      General: 'from-purple-500 to-violet-500',
    };
    return colors[dept] || 'from-gray-500 to-gray-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  // Module Content View
  if (selectedModule && moduleContent) {
    const sections = moduleContent.content?.sections || [];
    const quiz = moduleContent.content?.quiz || [];
    const isQuizStep = currentStep >= sections.length;
    const totalSteps = sections.length + (quiz.length > 0 ? 1 : 0);

    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-6"
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <button
            onClick={closeModule}
            className="text-gray-600 hover:text-gray-900"
          >
            ← Back to modules
          </button>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            {moduleContent.duration_minutes} min
          </div>
        </div>

        {/* Progress */}
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-primary-500"
            initial={{ width: 0 }}
            animate={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
          />
        </div>

        <h2 className="text-2xl font-bold text-gray-900">{moduleContent.title}</h2>

        {/* Content */}
        <AnimatePresence mode="wait">
          {!isQuizStep ? (
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
            >
              <h3 className="text-xl font-semibold mb-4 text-gray-900">
                {sections[currentStep]?.title}
              </h3>
              
              {sections[currentStep]?.type === 'text' && (
                <p className="text-gray-700 leading-relaxed">
                  {sections[currentStep].content}
                </p>
              )}
              
              {sections[currentStep]?.type === 'list' && (
                <ul className="space-y-2">
                  {sections[currentStep].items?.map((item: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <Check className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{item}</span>
                    </li>
                  ))}
                </ul>
              )}
            </motion.div>
          ) : quizResult ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-xl p-8 shadow-sm border border-gray-200 text-center"
            >
              {quizResult.passed ? (
                <>
                  <Trophy className="w-16 h-16 mx-auto text-amber-500 mb-4" />
                  <h3 className="text-2xl font-bold text-green-600 mb-2">
                    {language === 'ar' ? 'تهانينا!' : 'Congratulations!'}
                  </h3>
                  <p className="text-gray-700 mb-4">
                    {language === 'ar' ? 'لقد اجتزت الاختبار' : 'You passed the quiz'}
                  </p>
                </>
              ) : (
                <>
                  <AlertCircle className="w-16 h-16 mx-auto text-red-500 mb-4" />
                  <h3 className="text-2xl font-bold text-red-600 mb-2">
                    {language === 'ar' ? 'حاول مرة أخرى' : 'Try Again'}
                  </h3>
                  <p className="text-gray-700 mb-4">
                    {language === 'ar' 
                      ? `تحتاج ${moduleContent.passing_score}% للنجاح` 
                      : `You need ${moduleContent.passing_score}% to pass`}
                  </p>
                </>
              )}
              
              <div className="text-4xl font-bold mb-4 text-gray-900">
                {quizResult.score}%
              </div>
              
              <p className="text-gray-600 mb-6">
                {quizResult.correct} / {quizResult.total} correct
              </p>
              
              <div className="flex gap-3 justify-center">
                <button
                  onClick={closeModule}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  {language === 'ar' ? 'إغلاق' : 'Close'}
                </button>
                {!quizResult.passed && (
                  <button
                    onClick={() => {
                      setCurrentStep(0);
                      setQuizAnswers([]);
                      setQuizResult(null);
                    }}
                    className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    {language === 'ar' ? 'إعادة المحاولة' : 'Retry'}
                  </button>
                )}
              </div>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-200"
            >
              <h3 className="text-xl font-semibold mb-6 text-gray-900">
                {language === 'ar' ? 'اختبار' : 'Quiz'}
              </h3>
              
              <div className="space-y-6">
                {quiz.map((q: any, qIndex: number) => (
                  <div key={qIndex} className="space-y-3">
                    <p className="font-medium text-gray-900">
                      {qIndex + 1}. {q.question}
                    </p>
                    <div className="space-y-2">
                      {q.options.map((option: string, oIndex: number) => (
                        <button
                          key={oIndex}
                          onClick={() => handleQuizAnswer(qIndex, oIndex)}
                          className={clsx(
                            'w-full text-left p-3 rounded-lg border transition-all',
                            quizAnswers[qIndex] === oIndex
                              ? 'border-primary-500 bg-primary-50 text-primary-700'
                              : 'border-gray-300 text-gray-800 hover:border-primary-400 hover:bg-gray-50'
                          )}
                        >
                          {option}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              
              <button
                onClick={submitQuiz}
                disabled={quizAnswers.length < quiz.length}
                className="mt-6 w-full py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {language === 'ar' ? 'إرسال الإجابات' : 'Submit Answers'}
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Navigation */}
        {!quizResult && (
          <div className="flex justify-between">
            <button
              onClick={prevStep}
              disabled={currentStep === 0}
              className="px-4 py-2 text-gray-700 hover:text-gray-900 disabled:opacity-50"
            >
              ← {language === 'ar' ? 'السابق' : 'Previous'}
            </button>
            {!isQuizStep && (
              <button
                onClick={nextStep}
                className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center gap-2"
              >
                {currentStep < sections.length - 1 
                  ? (language === 'ar' ? 'التالي' : 'Next')
                  : (language === 'ar' ? 'الاختبار' : 'Take Quiz')}
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
        )}
      </motion.div>
    );
  }

  // Module List View
  return (
    <div className="space-y-6">
      {/* Summary */}
      {summary && (
        <div className="bg-gradient-to-r from-purple-500 to-violet-500 rounded-2xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <GraduationCap className="w-6 h-6" />
                {language === 'ar' ? 'التدريب' : 'Training Progress'}
              </h2>
              <p className="text-white/80 mt-1">
                {summary.completed_modules} / {summary.total_required_modules} {language === 'ar' ? 'وحدات مكتملة' : 'modules completed'}
              </p>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold">{Math.round(summary.completion_percentage)}%</div>
              <p className="text-sm text-white/80">{language === 'ar' ? 'مكتمل' : 'Complete'}</p>
            </div>
          </div>
          
          <div className="mt-4 h-2 bg-white/30 rounded-full overflow-hidden">
            <div
              className="h-full bg-white transition-all"
              style={{ width: `${summary.completion_percentage}%` }}
            />
          </div>
        </div>
      )}

      {/* Module List */}
      <div className="grid gap-4">
        {modules.map((module, index) => {
          const moduleProgress = getModuleProgress(module.id);
          const isCompleted = moduleProgress?.status === 'completed';
          const isInProgress = moduleProgress?.status === 'in_progress';

          return (
            <motion.div
              key={module.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={clsx(
                'p-4 rounded-xl border transition-all',
                isCompleted
                  ? 'bg-green-50 border-green-200'
                  : 'bg-white border-gray-200 hover:border-primary-300'
              )}
            >
              <div className="flex items-center gap-4">
                <div className={clsx(
                  'w-12 h-12 rounded-xl flex items-center justify-center',
                  isCompleted
                    ? 'bg-green-500 text-white'
                    : `bg-gradient-to-br ${getDepartmentColor(module.department)} text-white`
                )}>
                  {isCompleted ? <Check className="w-6 h-6" /> : <BookOpen className="w-6 h-6" />}
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-gray-900">
                      {language === 'ar' && module.title_ar ? module.title_ar : module.title}
                    </h3>
                    {module.is_required && (
                      <span className="px-2 py-0.5 text-xs bg-red-100 text-red-600 rounded-full">
                        {language === 'ar' ? 'مطلوب' : 'Required'}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">
                    {module.description?.slice(0, 80)}...
                  </p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {module.duration_minutes} min
                    </span>
                    <span className={clsx(
                      'px-2 py-0.5 rounded-full',
                      `bg-gradient-to-r ${getDepartmentColor(module.department)} text-white`
                    )}>
                      {module.department}
                    </span>
                    {moduleProgress?.score && (
                      <span className="text-green-600">
                        Score: {moduleProgress.score}%
                      </span>
                    )}
                  </div>
                </div>
                
                <button
                  onClick={() => startModule(module)}
                  className={clsx(
                    'px-4 py-2 rounded-lg flex items-center gap-2 transition-all',
                    isCompleted
                      ? 'bg-green-100 text-green-700 hover:bg-green-200'
                      : isInProgress
                        ? 'bg-primary-500 text-white hover:bg-primary-600'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  )}
                >
                  {isCompleted ? (
                    <>
                      <RefreshCw className="w-4 h-4" />
                      {language === 'ar' ? 'إعادة' : 'Retake'}
                    </>
                  ) : isInProgress ? (
                    <>
                      <Play className="w-4 h-4" />
                      {language === 'ar' ? 'متابعة' : 'Continue'}
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      {language === 'ar' ? 'ابدأ' : 'Start'}
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}


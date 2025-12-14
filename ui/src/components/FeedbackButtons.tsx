'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThumbsUp, ThumbsDown, MessageSquare, Check } from 'lucide-react';
import { api } from '@/lib/api';
import clsx from 'clsx';

interface FeedbackButtonsProps {
  messageId: number;
  onFeedbackSubmitted?: (type: 'helpful' | 'not_helpful') => void;
}

export default function FeedbackButtons({ messageId, onFeedbackSubmitted }: FeedbackButtonsProps) {
  const [submitted, setSubmitted] = useState<'helpful' | 'not_helpful' | null>(null);
  const [showComment, setShowComment] = useState(false);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFeedback = async (type: 'helpful' | 'not_helpful') => {
    if (submitted) return;
    
    setIsSubmitting(true);
    try {
      await api.submitFeedback({
        message_id: messageId,
        feedback_type: type,
        comment: comment || undefined,
      });
      
      setSubmitted(type);
      onFeedbackSubmitted?.(type);
      
      if (type === 'not_helpful' && !comment) {
        setShowComment(true);
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitComment = async () => {
    if (!comment.trim() || !submitted) return;
    
    setIsSubmitting(true);
    try {
      await api.submitFeedback({
        message_id: messageId,
        feedback_type: submitted,
        comment: comment,
      });
      setShowComment(false);
    } catch (error) {
      console.error('Failed to submit comment:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted && !showComment) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex items-center gap-2 text-sm text-gray-600"
      >
        <Check className="w-4 h-4 text-green-500" />
        <span>Thanks for your feedback!</span>
      </motion.div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-600">Was this helpful?</span>
        
        <button
          onClick={() => handleFeedback('helpful')}
          disabled={isSubmitting || !!submitted}
          className={clsx(
            'p-1.5 rounded-lg transition-all',
            submitted === 'helpful'
              ? 'bg-green-100 text-green-600'
              : 'hover:bg-surface-100 text-gray-500 hover:text-green-500'
          )}
        >
          <ThumbsUp className="w-4 h-4" />
        </button>
        
        <button
          onClick={() => handleFeedback('not_helpful')}
          disabled={isSubmitting || !!submitted}
          className={clsx(
            'p-1.5 rounded-lg transition-all',
            submitted === 'not_helpful'
              ? 'bg-red-100 text-red-600'
              : 'hover:bg-surface-100 text-gray-500 hover:text-red-500'
          )}
        >
          <ThumbsDown className="w-4 h-4" />
        </button>

        {!showComment && submitted === 'not_helpful' && (
          <button
            onClick={() => setShowComment(true)}
            className="p-1.5 rounded-lg hover:bg-surface-100 text-gray-500 hover:text-primary-500"
          >
            <MessageSquare className="w-4 h-4" />
          </button>
        )}
      </div>

      <AnimatePresence>
        {showComment && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex gap-2"
          >
            <input
              type="text"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="How can we improve?"
              className="flex-1 px-3 py-1.5 text-sm border border-surface-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <button
              onClick={submitComment}
              disabled={!comment.trim() || isSubmitting}
              className="px-3 py-1.5 text-sm bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


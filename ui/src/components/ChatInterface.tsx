'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Sparkles, FileText, Clock, ThumbsUp, ThumbsDown } from 'lucide-react';
import { api, ChatMessage, SourceReference, FAQTopic } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import clsx from 'clsx';
import FeedbackButtons from './FeedbackButtons';

interface ChatInterfaceProps {
  userId: number;
  userName: string;
  onTaskUpdate?: () => void;
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
}

export default function ChatInterface({ userId, userName, onTaskUpdate, messages, setMessages }: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [faqTopics, setFaqTopics] = useState<FAQTopic[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize with welcome message if empty
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          role: 'assistant',
          content: `Hello ${userName}! 👋 Welcome to your onboarding journey. I'm your AI assistant, here to help you with any questions about company policies, your tasks, or anything else you need during your first days. What can I help you with today?`,
          timestamp: new Date(),
        },
      ]);
    }
  }, [messages.length, userName, setMessages]);

  useEffect(() => {
    // Load FAQ topics
    api.getFAQTopics().then((data) => setFaqTopics(data.topics)).catch(console.error);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (messageText?: string) => {
    const text = messageText || input.trim();
    if (!text || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await api.sendMessage(userId, text);

      const assistantMessage: ChatMessage = {
        id: response.message_id,  // Include message ID for feedback
        role: 'assistant',
        content: response.response,
        sources: response.sources,
        routing: response.routing,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Notify parent about task updates
      if (response.task_updates?.length > 0 && onTaskUpdate) {
        onTaskUpdate();
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Please try again or contact support if the issue persists.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleFAQClick = async (topic: FAQTopic) => {
    handleSend(topic.question);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-8rem)] bg-white/60 dark:bg-surface-800/60 backdrop-blur-lg rounded-2xl shadow-xl border border-surface-200/50 dark:border-surface-700/50">
      {/* Header - Fixed at top */}
      <div className="flex-shrink-0 flex items-center gap-3 p-4 border-b border-surface-200/50 dark:border-surface-700/50">
        <div className="relative">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 border-2 border-white dark:border-surface-800 rounded-full" />
        </div>
        <div>
          <h2 className="font-semibold text-gray-950 dark:text-surface-100">Onboarding Copilot</h2>
          <p className="text-xs text-gray-600">AI-powered assistant • Always here to help</p>
        </div>
      </div>

      {/* FAQ Quick Actions - Fixed height, won't expand */}
      {messages.length <= 2 && faqTopics.length > 0 && (
        <div className="flex-shrink-0 p-4 border-b border-surface-200/50 dark:border-surface-700/50">
          <p className="text-sm text-gray-700 dark:text-gray-500 mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-500" />
            Quick topics to get you started:
          </p>
          <div className="flex flex-wrap gap-2">
            {faqTopics.slice(0, 6).map((topic) => (
              <button
                key={topic.id}
                onClick={() => handleFAQClick(topic)}
                className="px-3 py-1.5 text-sm bg-surface-100 dark:bg-surface-700 hover:bg-primary-100 dark:hover:bg-primary-900/30 text-gray-800 dark:text-surface-300 rounded-full transition-colors border border-surface-200 dark:border-surface-600 hover:border-primary-300 dark:hover:border-primary-700"
              >
                {topic.title}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages - Scrollable area that takes remaining space */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        <AnimatePresence>
          {messages.map((message, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={clsx(
                'flex gap-3',
                message.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}
              <div
                className={clsx(
                  'max-w-[75%] rounded-2xl px-4 py-3',
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white'
                    : 'bg-surface-100 dark:bg-surface-700 text-gray-900 dark:text-surface-200'
                )}
              >
                {message.role === 'assistant' ? (
                  <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:my-2 prose-headings:text-gray-950 dark:prose-headings:text-surface-100">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                )}
                
                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-surface-200/30 dark:border-surface-600/30">
                    <p className="text-xs text-gray-600 dark:text-gray-500 mb-2 flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      Sources:
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {message.sources.map((source, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center px-2 py-0.5 text-xs bg-surface-200/50 dark:bg-surface-600/50 rounded"
                        >
                          {source.document}
                          {source.section && ` • ${source.section}`}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Timestamp and Feedback */}
                <div className="flex items-center justify-between mt-2">
                  {message.timestamp && (
                    <p className={clsx(
                      'text-xs',
                      message.role === 'user' ? 'text-white/60' : 'text-gray-500'
                    )}>
                      <Clock className="w-3 h-3 inline mr-1" />
                      {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  )}
                  {message.role === 'assistant' && index > 0 && message.id && (
                    <FeedbackButtons messageId={message.id} />
                  )}
                </div>
              </div>
              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-lg bg-surface-200 dark:bg-surface-600 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-gray-700 dark:text-surface-300" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-surface-100 dark:bg-surface-700 rounded-2xl px-4 py-3">
              <div className="typing-indicator flex gap-1">
                <span className="w-2 h-2 bg-surface-400 rounded-full" />
                <span className="w-2 h-2 bg-surface-400 rounded-full" />
                <span className="w-2 h-2 bg-surface-400 rounded-full" />
              </div>
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input - Fixed at bottom */}
      <div className="flex-shrink-0 p-4 border-t border-surface-200/50 dark:border-surface-700/50">
        <div className="flex items-center gap-2 bg-surface-100 dark:bg-surface-700 rounded-xl px-4 py-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about your onboarding..."
            className="flex-1 bg-transparent border-none outline-none text-gray-900 dark:text-surface-200 placeholder:text-gray-500"
            disabled={isLoading}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className={clsx(
              'p-2 rounded-lg transition-all',
              input.trim() && !isLoading
                ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white hover:shadow-lg hover:scale-105'
                : 'bg-surface-200 dark:bg-surface-600 text-gray-500 cursor-not-allowed'
            )}
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}


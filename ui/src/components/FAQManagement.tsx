'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Pencil,
  Trash2,
  Search,
  Filter,
  X,
  HelpCircle,
  Eye,
  EyeOff,
  ThumbsUp,
  ThumbsDown,
} from 'lucide-react';
import { api } from '@/lib/api';
import clsx from 'clsx';

interface FAQ {
  id: number;
  question: string;
  answer: string;
  category: string;
  tags: string[];  // API uses 'tags' not 'keywords'
  is_published: boolean;
  helpful_count: number;
  not_helpful_count: number;
  created_at: string;
  updated_at: string;
}

interface FAQManagementProps {
  language?: 'en' | 'ar';
}

export default function FAQManagement({ language = 'en' }: FAQManagementProps) {
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showModal, setShowModal] = useState(false);
  const [editingFaq, setEditingFaq] = useState<FAQ | null>(null);
  const [formData, setFormData] = useState({
    question: '',
    answer: '',
    category: 'HR',
    keywords: '',
    is_published: true,
  });

  const t = {
    en: {
      title: 'FAQ Management',
      subtitle: 'Manage frequently asked questions',
      addFaq: 'Add FAQ',
      search: 'Search FAQs...',
      allCategories: 'All Categories',
      published: 'Published',
      draft: 'Draft',
      edit: 'Edit',
      delete: 'Delete',
      noFaqs: 'No FAQs found',
      form: {
        title: 'FAQ Details',
        question: 'Question',
        answer: 'Answer',
        category: 'Category',
        keywords: 'Keywords (comma-separated)',
        publish: 'Publish immediately',
        cancel: 'Cancel',
        save: 'Save FAQ',
        create: 'Create FAQ',
      },
      deleteConfirm: 'Are you sure you want to delete this FAQ?',
      helpful: 'Helpful',
      notHelpful: 'Not helpful',
    },
    ar: {
      title: 'إدارة الأسئلة الشائعة',
      subtitle: 'إدارة الأسئلة المتكررة',
      addFaq: 'إضافة سؤال',
      search: 'بحث...',
      allCategories: 'جميع الفئات',
      published: 'منشور',
      draft: 'مسودة',
      edit: 'تعديل',
      delete: 'حذف',
      noFaqs: 'لا توجد أسئلة',
      form: {
        title: 'تفاصيل السؤال',
        question: 'السؤال',
        answer: 'الإجابة',
        category: 'الفئة',
        keywords: 'الكلمات المفتاحية (مفصولة بفواصل)',
        publish: 'نشر فوراً',
        cancel: 'إلغاء',
        save: 'حفظ',
        create: 'إنشاء',
      },
      deleteConfirm: 'هل أنت متأكد من حذف هذا السؤال؟',
      helpful: 'مفيد',
      notHelpful: 'غير مفيد',
    },
  };

  const text = t[language];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [faqsData, categoriesData] = await Promise.all([
        api.getFAQs({ include_unpublished: true }),
        api.getFAQCategories(),
      ]);
      setFaqs(faqsData);
      setCategories(categoriesData.categories);
    } catch (error) {
      console.error('Failed to load FAQs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        question: formData.question,
        answer: formData.answer,
        category: formData.category,
        tags: formData.keywords.split(',').map(k => k.trim()).filter(Boolean),
        is_published: formData.is_published,
      };

      if (editingFaq) {
        await api.updateFAQ(editingFaq.id, data);
      } else {
        await api.createFAQ(data);
      }

      setShowModal(false);
      setEditingFaq(null);
      resetForm();
      await loadData();
    } catch (error) {
      console.error('Failed to save FAQ:', error);
    }
  };

  const handleEdit = (faq: FAQ) => {
    setEditingFaq(faq);
    setFormData({
      question: faq.question,
      answer: faq.answer,
      category: faq.category,
      keywords: (faq.tags || []).join(', '),
      is_published: faq.is_published,
    });
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm(text.deleteConfirm)) {
      try {
        await api.deleteFAQ(id);
        await loadData();
      } catch (error) {
        console.error('Failed to delete FAQ:', error);
      }
    }
  };

  const resetForm = () => {
    setFormData({
      question: '',
      answer: '',
      category: 'HR',
      keywords: '',
      is_published: true,
    });
  };

  const filteredFaqs = faqs.filter((faq) => {
    const matchesSearch =
      searchQuery === '' ||
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      selectedCategory === 'all' || faq.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const categoryColors: Record<string, string> = {
    HR: 'bg-blue-100 text-blue-700',
    IT: 'bg-emerald-100 text-emerald-700',
    Security: 'bg-amber-100 text-amber-700',
    Finance: 'bg-purple-100 text-purple-700',
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
          onClick={() => {
            resetForm();
            setEditingFaq(null);
            setShowModal(true);
          }}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-xl transition-colors"
        >
          <Plus className="w-4 h-4" />
          {text.addFaq}
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder={text.search}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        >
          <option value="all">{text.allCategories}</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      {/* FAQ List */}
      <div className="space-y-4">
        {filteredFaqs.length === 0 ? (
          <div className="text-center py-12 bg-slate-50 rounded-2xl">
            <HelpCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-slate-500">{text.noFaqs}</p>
          </div>
        ) : (
          filteredFaqs.map((faq) => (
            <motion.div
              key={faq.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={clsx(
                      'px-2 py-1 text-xs rounded-full font-medium',
                      categoryColors[faq.category] || 'bg-slate-100 text-slate-700'
                    )}>
                      {faq.category}
                    </span>
                    <span className={clsx(
                      'px-2 py-1 text-xs rounded-full font-medium flex items-center gap-1',
                      faq.is_published
                        ? 'bg-green-100 text-green-700'
                        : 'bg-slate-100 text-slate-600'
                    )}>
                      {faq.is_published ? (
                        <>
                          <Eye className="w-3 h-3" />
                          {text.published}
                        </>
                      ) : (
                        <>
                          <EyeOff className="w-3 h-3" />
                          {text.draft}
                        </>
                      )}
                    </span>
                  </div>
                  <h3 className="font-semibold text-slate-900 mb-2">{faq.question}</h3>
                  <p className="text-slate-600 text-sm line-clamp-2">{faq.answer}</p>
                  {(faq.tags || []).length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-3">
                      {(faq.tags || []).map((keyword, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-slate-100 text-slate-600 text-xs rounded-full"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="flex items-center gap-4 mt-3 text-sm text-slate-500">
                    <span className="flex items-center gap-1">
                      <ThumbsUp className="w-4 h-4 text-green-500" />
                      {faq.helpful_count} {text.helpful}
                    </span>
                    <span className="flex items-center gap-1">
                      <ThumbsDown className="w-4 h-4 text-red-500" />
                      {faq.not_helpful_count} {text.notHelpful}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleEdit(faq)}
                    className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                    title={text.edit}
                  >
                    <Pencil className="w-4 h-4 text-slate-600" />
                  </button>
                  <button
                    onClick={() => handleDelete(faq.id)}
                    className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                    title={text.delete}
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>

      {/* Add/Edit Modal */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-900">
                  {editingFaq ? text.form.title : text.addFaq}
                </h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-2 hover:bg-slate-100 rounded-lg"
                >
                  <X className="w-5 h-5 text-slate-500" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    {text.form.question}
                  </label>
                  <input
                    type="text"
                    value={formData.question}
                    onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                    required
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    {text.form.answer}
                  </label>
                  <textarea
                    value={formData.answer}
                    onChange={(e) => setFormData({ ...formData, answer: e.target.value })}
                    required
                    rows={5}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    {text.form.category}
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="HR">HR</option>
                    <option value="IT">IT</option>
                    <option value="Security">Security</option>
                    <option value="Finance">Finance</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    {text.form.keywords}
                  </label>
                  <input
                    type="text"
                    value={formData.keywords}
                    onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
                    placeholder="benefits, health, insurance"
                    className="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_published"
                    checked={formData.is_published}
                    onChange={(e) => setFormData({ ...formData, is_published: e.target.checked })}
                    className="w-4 h-4 rounded border-slate-300 text-primary-500 focus:ring-primary-500"
                  />
                  <label htmlFor="is_published" className="text-sm text-slate-700">
                    {text.form.publish}
                  </label>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                  >
                    {text.form.cancel}
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-xl transition-colors"
                  >
                    {editingFaq ? text.form.save : text.form.create}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}


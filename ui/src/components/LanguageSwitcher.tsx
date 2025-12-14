'use client';

import { useState } from 'react';
import { Globe } from 'lucide-react';
import { useI18n, Language } from '@/lib/i18n-context';
import clsx from 'clsx';

interface LanguageSwitcherProps {
  className?: string;
}

export default function LanguageSwitcher({ className }: LanguageSwitcherProps) {
  const { language, setLanguage } = useI18n();
  const [isOpen, setIsOpen] = useState(false);

  const languages = [
    { code: 'en' as Language, name: 'English', flag: '🇺🇸' },
    { code: 'ar' as Language, name: 'العربية', flag: '🇸🇦' },
  ];

  const currentLanguage = languages.find(l => l.code === language) || languages[0];

  return (
    <div className={clsx('relative', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors w-full"
      >
        <Globe className="w-4 h-4 text-slate-600" />
        <span className="text-sm font-medium text-slate-800">{currentLanguage.flag} {currentLanguage.name}</span>
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)} 
          />
          <div className="absolute bottom-full left-0 mb-2 bg-white rounded-lg shadow-lg border border-slate-200 z-50 min-w-[150px]">
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => {
                  setLanguage(lang.code);
                  setIsOpen(false);
                }}
                className={clsx(
                  'w-full flex items-center gap-2 px-4 py-2 text-left hover:bg-slate-50 first:rounded-t-lg last:rounded-b-lg text-slate-800',
                  language === lang.code && 'bg-blue-50 text-blue-700'
                )}
              >
                <span>{lang.flag}</span>
                <span className="text-sm font-medium">{lang.name}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

"""Internationalization (i18n) service for Arabic and English support."""
import logging
from typing import Dict, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Supported languages."""
    ENGLISH = "en"
    ARABIC = "ar"


# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # UI Elements
    "welcome_message": {
        "en": "Welcome to the Onboarding Copilot! How can I help you today?",
        "ar": "مرحباً بك في مساعد الإعداد! كيف يمكنني مساعدتك اليوم؟"
    },
    "chat_placeholder": {
        "en": "Type your message here...",
        "ar": "اكتب رسالتك هنا..."
    },
    "send_button": {
        "en": "Send",
        "ar": "إرسال"
    },
    "tasks_title": {
        "en": "Onboarding Tasks",
        "ar": "مهام الإعداد"
    },
    "progress_title": {
        "en": "Your Progress",
        "ar": "تقدمك"
    },
    "admin_dashboard": {
        "en": "Admin Dashboard",
        "ar": "لوحة تحكم المسؤول"
    },
    
    # Task statuses
    "status_not_started": {
        "en": "Not Started",
        "ar": "لم يبدأ"
    },
    "status_in_progress": {
        "en": "In Progress",
        "ar": "قيد التنفيذ"
    },
    "status_done": {
        "en": "Completed",
        "ar": "مكتمل"
    },
    
    # Departments
    "department_hr": {
        "en": "Human Resources",
        "ar": "الموارد البشرية"
    },
    "department_it": {
        "en": "Information Technology",
        "ar": "تكنولوجيا المعلومات"
    },
    "department_security": {
        "en": "Security & Compliance",
        "ar": "الأمن والامتثال"
    },
    "department_finance": {
        "en": "Finance & Admin",
        "ar": "المالية والإدارة"
    },
    
    # Common phrases
    "loading": {
        "en": "Loading...",
        "ar": "جاري التحميل..."
    },
    "error_occurred": {
        "en": "An error occurred. Please try again.",
        "ar": "حدث خطأ. يرجى المحاولة مرة أخرى."
    },
    "no_results": {
        "en": "No results found.",
        "ar": "لم يتم العثور على نتائج."
    },
    "confirm": {
        "en": "Confirm",
        "ar": "تأكيد"
    },
    "cancel": {
        "en": "Cancel",
        "ar": "إلغاء"
    },
    "save": {
        "en": "Save",
        "ar": "حفظ"
    },
    "delete": {
        "en": "Delete",
        "ar": "حذف"
    },
    "edit": {
        "en": "Edit",
        "ar": "تعديل"
    },
    "close": {
        "en": "Close",
        "ar": "إغلاق"
    },
    "back": {
        "en": "Back",
        "ar": "رجوع"
    },
    "next": {
        "en": "Next",
        "ar": "التالي"
    },
    "previous": {
        "en": "Previous",
        "ar": "السابق"
    },
    "submit": {
        "en": "Submit",
        "ar": "إرسال"
    },
    "logout": {
        "en": "Logout",
        "ar": "تسجيل الخروج"
    },
    "login": {
        "en": "Login",
        "ar": "تسجيل الدخول"
    },
    "email": {
        "en": "Email",
        "ar": "البريد الإلكتروني"
    },
    "password": {
        "en": "Password",
        "ar": "كلمة المرور"
    },
    
    # Feedback
    "feedback_helpful": {
        "en": "Was this helpful?",
        "ar": "هل كان هذا مفيداً؟"
    },
    "feedback_yes": {
        "en": "Yes",
        "ar": "نعم"
    },
    "feedback_no": {
        "en": "No",
        "ar": "لا"
    },
    "feedback_thanks": {
        "en": "Thank you for your feedback!",
        "ar": "شكراً على ملاحظاتك!"
    },
    
    # Achievements
    "achievements_title": {
        "en": "Achievements",
        "ar": "الإنجازات"
    },
    "achievement_unlocked": {
        "en": "Achievement Unlocked!",
        "ar": "تم فتح إنجاز جديد!"
    },
    "points": {
        "en": "Points",
        "ar": "نقاط"
    },
    
    # Training
    "training_title": {
        "en": "Training Modules",
        "ar": "وحدات التدريب"
    },
    "start_training": {
        "en": "Start Training",
        "ar": "ابدأ التدريب"
    },
    "continue_training": {
        "en": "Continue",
        "ar": "استمرار"
    },
    "quiz": {
        "en": "Quiz",
        "ar": "اختبار"
    },
    "score": {
        "en": "Score",
        "ar": "النتيجة"
    },
    "passed": {
        "en": "Passed",
        "ar": "ناجح"
    },
    "failed": {
        "en": "Failed",
        "ar": "فاشل"
    },
    
    # Calendar
    "calendar_title": {
        "en": "Calendar",
        "ar": "التقويم"
    },
    "add_to_calendar": {
        "en": "Add to Calendar",
        "ar": "إضافة إلى التقويم"
    },
    "reminder": {
        "en": "Reminder",
        "ar": "تذكير"
    },
    "due_date": {
        "en": "Due Date",
        "ar": "تاريخ الاستحقاق"
    },
    "overdue": {
        "en": "Overdue",
        "ar": "متأخر"
    },
    
    # FAQ
    "faq_title": {
        "en": "Frequently Asked Questions",
        "ar": "الأسئلة المتكررة"
    },
    "search_faq": {
        "en": "Search FAQs...",
        "ar": "البحث في الأسئلة المتكررة..."
    },
    
    # Escalation messages
    "escalation_message": {
        "en": "I'll connect you with a human representative who can better assist you.",
        "ar": "سأقوم بتوصيلك بممثل بشري يمكنه مساعدتك بشكل أفضل."
    },
    "contact_support": {
        "en": "Contact Support",
        "ar": "اتصل بالدعم"
    },
    
    # Time-related
    "today": {
        "en": "Today",
        "ar": "اليوم"
    },
    "yesterday": {
        "en": "Yesterday",
        "ar": "أمس"
    },
    "tomorrow": {
        "en": "Tomorrow",
        "ar": "غداً"
    },
    "this_week": {
        "en": "This Week",
        "ar": "هذا الأسبوع"
    },
    "next_week": {
        "en": "Next Week",
        "ar": "الأسبوع القادم"
    },
}


class TranslationService:
    """Service for handling translations."""
    
    def __init__(self, default_language: Language = Language.ENGLISH):
        self.default_language = default_language
        self.translations = TRANSLATIONS
    
    def t(self, key: str, language: Optional[str] = None, **kwargs) -> str:
        """
        Translate a key to the specified language.
        
        Args:
            key: Translation key
            language: Target language code (en, ar)
            **kwargs: Variables to interpolate into the translation
        
        Returns:
            Translated string
        """
        lang = language or self.default_language.value
        
        if key not in self.translations:
            logger.warning(f"Translation key not found: {key}")
            return key
        
        translation = self.translations[key].get(lang)
        if translation is None:
            # Fall back to English
            translation = self.translations[key].get("en", key)
        
        # Interpolate variables
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except KeyError as e:
                logger.error(f"Missing interpolation variable: {e}")
        
        return translation
    
    def get_all_translations(self, language: str) -> Dict[str, str]:
        """Get all translations for a language."""
        return {
            key: trans.get(language, trans.get("en", key))
            for key, trans in self.translations.items()
        }
    
    def add_translation(self, key: str, translations: Dict[str, str]):
        """Add a new translation."""
        self.translations[key] = translations
    
    def get_direction(self, language: str) -> str:
        """Get text direction for a language."""
        return "rtl" if language == "ar" else "ltr"
    
    def get_font_family(self, language: str) -> str:
        """Get appropriate font family for a language."""
        if language == "ar":
            return "'Cairo', 'Noto Sans Arabic', sans-serif"
        return "'Inter', 'Segoe UI', sans-serif"
    
    def detect_language(self, text: str) -> Language:
        """Simple language detection based on character ranges."""
        arabic_chars = 0
        latin_chars = 0
        
        for char in text:
            if '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F':
                arabic_chars += 1
            elif 'a' <= char.lower() <= 'z':
                latin_chars += 1
        
        if arabic_chars > latin_chars:
            return Language.ARABIC
        return Language.ENGLISH
    
    def format_number(self, number: float, language: str) -> str:
        """Format a number according to language conventions."""
        if language == "ar":
            # Convert to Eastern Arabic numerals
            eastern_arabic = str(number).translate(
                str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
            )
            return eastern_arabic
        return str(number)
    
    def format_date(self, date_str: str, language: str) -> str:
        """Format a date string according to language conventions."""
        # This is a simplified implementation
        # In production, use proper date formatting libraries
        if language == "ar":
            # Could convert to Hijri calendar if needed
            pass
        return date_str


# Global translation service instance
_translation_service: Optional[TranslationService] = None


def get_translation_service() -> TranslationService:
    """Get or create the translation service singleton."""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service


def t(key: str, language: Optional[str] = None, **kwargs) -> str:
    """Shorthand for translation."""
    return get_translation_service().t(key, language, **kwargs)


'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Calendar,
  Clock,
  Plus,
  Download,
  ChevronLeft,
  ChevronRight,
  X,
  CalendarCheck,
  AlertCircle,
  Bell,
} from 'lucide-react';
import { api } from '@/lib/api';
import { useI18n } from '@/lib/i18n-context';
import clsx from 'clsx';

interface CalendarEvent {
  id: number;
  title: string;
  description: string;
  start_time: string;
  end_time: string;
  event_type: string;
  related_task_id: number | null;
}

export default function CalendarView() {
  const { language, t } = useI18n();
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [showAddModal, setShowAddModal] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    start_time: '',
    end_time: '',
    event_type: 'deadline',
  });

  // Translations
  const text = {
    title: language === 'ar' ? 'التقويم' : 'Calendar',
    subtitle: language === 'ar' ? 'تتبع جدول التأهيل الخاص بك' : 'Track your onboarding schedule',
    addEvent: language === 'ar' ? 'إضافة حدث' : 'Add Event',
    syncTasks: language === 'ar' ? 'مزامنة المهام' : 'Sync Tasks',
    export: language === 'ar' ? 'تصدير' : 'Export',
    noEvents: language === 'ar' ? 'لا توجد أحداث لهذا اليوم' : 'No events for this day',
    eventTypes: {
      deadline: language === 'ar' ? 'موعد نهائي' : 'Deadline',
      meeting: language === 'ar' ? 'اجتماع' : 'Meeting',
      reminder: language === 'ar' ? 'تذكير' : 'Reminder',
    },
    form: {
      title: language === 'ar' ? 'عنوان الحدث' : 'Event Title',
      description: language === 'ar' ? 'الوصف' : 'Description',
      startTime: language === 'ar' ? 'وقت البدء' : 'Start Time',
      endTime: language === 'ar' ? 'وقت الانتهاء' : 'End Time',
      type: language === 'ar' ? 'نوع الحدث' : 'Event Type',
      cancel: language === 'ar' ? 'إلغاء' : 'Cancel',
      create: language === 'ar' ? 'إنشاء حدث' : 'Create Event',
    },
    syncSuccess: language === 'ar' ? 'تمت مزامنة المهام مع التقويم' : 'Tasks synced to calendar',
    today: language === 'ar' ? 'اليوم' : 'Today',
    upcomingEvents: language === 'ar' ? 'الأحداث القادمة' : 'Upcoming Events',
    note: language === 'ar' ? 'ملاحظة: هذا تقويم داخلي' : 'Note: This is an internal calendar',
  };

  useEffect(() => {
    loadEvents();
  }, [currentDate]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const startOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
      const endOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
      
      const data = await api.getCalendarEvents({
        start_date: startOfMonth.toISOString().split('T')[0],
        end_date: endOfMonth.toISOString().split('T')[0],
      });
      setEvents(data);
    } catch (error) {
      console.error('Failed to load calendar events:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncTasks = async () => {
    try {
      setSyncing(true);
      await api.syncTasksToCalendar({ include_completed: false });
      await loadEvents();
    } catch (error) {
      console.error('Failed to sync tasks:', error);
    } finally {
      setSyncing(false);
    }
  };

  const handleExport = async () => {
    try {
      const icsContent = await api.exportCalendar('ics');
      // Create download link
      const blob = new Blob([icsContent], { type: 'text/calendar' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'onboarding-calendar.ics';
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export calendar:', error);
    }
  };

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Convert local datetime to ISO format
      const startTime = newEvent.start_time ? new Date(newEvent.start_time).toISOString() : new Date().toISOString();
      const endTime = newEvent.end_time ? new Date(newEvent.end_time).toISOString() : new Date(new Date(startTime).getTime() + 60*60*1000).toISOString();
      
      await api.createCalendarEvent({
        title: `[${newEvent.event_type.toUpperCase()}] ${newEvent.title}`,
        description: newEvent.description || undefined,
        start_time: startTime,
        end_time: endTime,
      });
      setShowAddModal(false);
      setNewEvent({
        title: '',
        description: '',
        start_time: '',
        end_time: '',
        event_type: 'deadline',
      });
      await loadEvents();
    } catch (error) {
      console.error('Failed to create event:', error);
      alert('Failed to create event. Please try again.');
    }
  };

  const getDaysInMonth = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();
    
    const days = [];
    
    // Add empty cells for days before the first of the month
    for (let i = 0; i < startingDay; i++) {
      days.push(null);
    }
    
    // Add the days of the month
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(i);
    }
    
    return days;
  };

  const getEventsForDay = (day: number) => {
    const dateStr = new Date(currentDate.getFullYear(), currentDate.getMonth(), day)
      .toISOString().split('T')[0];
    return events.filter(e => e.start_time.startsWith(dateStr));
  };

  const isToday = (day: number) => {
    const today = new Date();
    return (
      day === today.getDate() &&
      currentDate.getMonth() === today.getMonth() &&
      currentDate.getFullYear() === today.getFullYear()
    );
  };

  const eventTypeColors: Record<string, string> = {
    deadline: 'bg-red-500',
    meeting: 'bg-blue-500',
    reminder: 'bg-amber-500',
  };

  const monthNames = language === 'ar' 
    ? ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
    : ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

  const dayNames = language === 'ar'
    ? ['أحد', 'إثنين', 'ثلاثاء', 'أربعاء', 'خميس', 'جمعة', 'سبت']
    : ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">{text.title}</h2>
          <p className="text-slate-600">{text.subtitle}</p>
          <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {text.note}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSyncTasks}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl transition-colors disabled:opacity-50"
          >
            <CalendarCheck className={clsx('w-4 h-4', syncing && 'animate-spin')} />
            {text.syncTasks}
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl transition-colors"
          >
            <Download className="w-4 h-4" />
            {text.export}
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors"
          >
            <Plus className="w-4 h-4" />
            {text.addEvent}
          </button>
        </div>
      </div>

      {/* Calendar Navigation */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-slate-50">
          <button
            onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1))}
            className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-slate-700" />
          </button>
          <h3 className="text-lg font-semibold text-slate-900">
            {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
          </h3>
          <button
            onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1))}
            className="p-2 hover:bg-slate-200 rounded-lg transition-colors"
          >
            <ChevronRight className="w-5 h-5 text-slate-700" />
          </button>
        </div>

        {/* Calendar Grid */}
        <div className="p-4">
          {/* Day Headers */}
          <div className="grid grid-cols-7 gap-1 mb-2">
            {dayNames.map((day) => (
              <div key={day} className="text-center text-sm font-semibold text-slate-700 py-2 bg-slate-50 rounded">
                {day}
              </div>
            ))}
          </div>

          {/* Days Grid */}
          <div className="grid grid-cols-7 gap-1">
            {getDaysInMonth().map((day, index) => (
              <div
                key={index}
                className={clsx(
                  'min-h-[100px] p-2 border border-slate-200 rounded-lg',
                  day && 'hover:bg-slate-50 cursor-pointer',
                  isToday(day || 0) && 'bg-blue-50 border-blue-300'
                )}
              >
                {day && (
                  <>
                    <div className={clsx(
                      'text-sm font-bold mb-1',
                      isToday(day) ? 'text-blue-700' : 'text-slate-900'
                    )}>
                      {day}
                      {isToday(day) && (
                        <span className="ml-1 text-xs font-medium text-blue-600">({text.today})</span>
                      )}
                    </div>
                    <div className="space-y-1">
                      {getEventsForDay(day).slice(0, 3).map((event) => (
                        <div
                          key={event.id}
                          className={clsx(
                            'text-xs px-2 py-1 rounded text-white truncate font-medium',
                            eventTypeColors[event.event_type] || 'bg-slate-500'
                          )}
                          title={event.title}
                        >
                          {event.title}
                        </div>
                      ))}
                      {getEventsForDay(day).length > 3 && (
                        <div className="text-xs font-medium text-slate-600">
                          +{getEventsForDay(day).length - 3} more
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Upcoming Events */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
        <h3 className="text-lg font-bold text-slate-900 mb-4">
          {text.upcomingEvents}
        </h3>
        <div className="space-y-3">
          {events
            .filter(e => new Date(e.start_time) >= new Date())
            .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
            .slice(0, 5)
            .map((event) => (
              <div
                key={event.id}
                className="flex items-center gap-4 p-3 bg-slate-50 rounded-xl border border-slate-100"
              >
                <div className={clsx(
                  'w-3 h-3 rounded-full',
                  eventTypeColors[event.event_type] || 'bg-slate-500'
                )} />
                <div className="flex-1">
                  <p className="font-semibold text-slate-900">{event.title}</p>
                  <p className="text-sm text-slate-600">
                    {new Date(event.start_time).toLocaleDateString()} at{' '}
                    {new Date(event.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                <span className={clsx(
                  'px-2 py-1 text-xs font-semibold rounded-full',
                  event.event_type === 'deadline' && 'bg-red-100 text-red-800',
                  event.event_type === 'meeting' && 'bg-blue-100 text-blue-800',
                  event.event_type === 'reminder' && 'bg-amber-100 text-amber-800'
                )}>
                  {text.eventTypes[event.event_type as keyof typeof text.eventTypes] || event.event_type}
                </span>
              </div>
            ))}
          {events.filter(e => new Date(e.start_time) >= new Date()).length === 0 && (
            <p className="text-slate-600 text-center py-4">{text.noEvents}</p>
          )}
        </div>
      </div>

      {/* Add Event Modal */}
      <AnimatePresence>
        {showAddModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowAddModal(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl p-6 max-w-md w-full shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-slate-900">{text.addEvent}</h3>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="p-2 hover:bg-slate-100 rounded-lg"
                >
                  <X className="w-5 h-5 text-slate-600" />
                </button>
              </div>

              <form onSubmit={handleCreateEvent} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-slate-800 mb-1">
                    {text.form.title}
                  </label>
                  <input
                    type="text"
                    value={newEvent.title}
                    onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                    required
                    className="w-full px-4 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-800 mb-1">
                    {text.form.description}
                  </label>
                  <textarea
                    value={newEvent.description}
                    onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                    rows={3}
                    className="w-full px-4 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-slate-800 mb-1">
                      {text.form.startTime}
                    </label>
                    <input
                      type="datetime-local"
                      value={newEvent.start_time}
                      onChange={(e) => setNewEvent({ ...newEvent, start_time: e.target.value })}
                      required
                      className="w-full px-4 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-800 mb-1">
                      {text.form.endTime}
                    </label>
                    <input
                      type="datetime-local"
                      value={newEvent.end_time}
                      onChange={(e) => setNewEvent({ ...newEvent, end_time: e.target.value })}
                      required
                      className="w-full px-4 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-slate-800 mb-1">
                    {text.form.type}
                  </label>
                  <select
                    value={newEvent.event_type}
                    onChange={(e) => setNewEvent({ ...newEvent, event_type: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900"
                  >
                    <option value="deadline">{text.eventTypes.deadline}</option>
                    <option value="meeting">{text.eventTypes.meeting}</option>
                    <option value="reminder">{text.eventTypes.reminder}</option>
                  </select>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 text-slate-700 hover:bg-slate-100 rounded-xl transition-colors font-medium"
                  >
                    {text.form.cancel}
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors font-medium"
                  >
                    {text.form.create}
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


// =============================================================================
// FUTURE: External Calendar Integration UI
// =============================================================================
// 
// Uncomment and integrate the following code when external calendar OAuth
// is enabled in the backend (see app/services/external_calendar_integration.py)
//
// Required: Add these icons to imports:
// import { Cloud, Link2, Unlink } from 'lucide-react';
//
// Add to component state:
// const [calendarConnections, setCalendarConnections] = useState({
//   google: { connected: false, configured: false },
//   microsoft: { connected: false, configured: false }
// });
// const [connectingProvider, setConnectingProvider] = useState<string | null>(null);
//
// Add useEffect to check connections:
// useEffect(() => {
//   const checkConnections = async () => {
//     try {
//       const connections = await api.request('/calendar/connections');
//       setCalendarConnections(connections);
//     } catch (error) {
//       console.log('External calendar integration not configured');
//     }
//   };
//   checkConnections();
// }, []);
//
// Add handler functions:
// const handleConnectGoogle = async () => {
//   setConnectingProvider('google');
//   try {
//     const { authorization_url } = await api.request('/calendar/oauth/google/authorize');
//     window.location.href = authorization_url;
//   } catch (error) {
//     console.error('Failed to get Google auth URL:', error);
//     setConnectingProvider(null);
//   }
// };
//
// const handleConnectMicrosoft = async () => {
//   setConnectingProvider('microsoft');
//   try {
//     const { authorization_url } = await api.request('/calendar/oauth/microsoft/authorize');
//     window.location.href = authorization_url;
//   } catch (error) {
//     console.error('Failed to get Microsoft auth URL:', error);
//     setConnectingProvider(null);
//   }
// };
//
// const handleDisconnect = async (provider: 'google' | 'microsoft') => {
//   try {
//     await api.request(`/calendar/oauth/${provider}/disconnect`, { method: 'DELETE' });
//     setCalendarConnections(prev => ({
//       ...prev,
//       [provider]: { ...prev[provider], connected: false }
//     }));
//   } catch (error) {
//     console.error(`Failed to disconnect ${provider}:`, error);
//   }
// };
//
// const handleSyncToExternal = async (provider: 'google' | 'microsoft') => {
//   setSyncing(true);
//   try {
//     const result = await api.request(`/calendar/sync/${provider}`, { method: 'POST' });
//     alert(`Synced ${result.synced_count} events to ${provider === 'google' ? 'Google Calendar' : 'Outlook'}`);
//   } catch (error) {
//     console.error(`Failed to sync to ${provider}:`, error);
//   } finally {
//     setSyncing(false);
//   }
// };
//
// Add this JSX after the Export button in the header:
// {/* External Calendar Connections */}
// {(calendarConnections.google.configured || calendarConnections.microsoft.configured) && (
//   <div className="flex items-center gap-2 ml-4 pl-4 border-l border-slate-200">
//     {/* Google Calendar */}
//     {calendarConnections.google.configured && (
//       calendarConnections.google.connected ? (
//         <div className="flex items-center gap-1">
//           <button
//             onClick={() => handleSyncToExternal('google')}
//             disabled={syncing}
//             className="flex items-center gap-1 px-3 py-1.5 bg-green-50 text-green-700 text-sm rounded-lg hover:bg-green-100"
//             title="Sync to Google Calendar"
//           >
//             <Cloud className="w-4 h-4" />
//             Google
//           </button>
//           <button
//             onClick={() => handleDisconnect('google')}
//             className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg"
//             title="Disconnect Google Calendar"
//           >
//             <Unlink className="w-4 h-4" />
//           </button>
//         </div>
//       ) : (
//         <button
//           onClick={handleConnectGoogle}
//           disabled={connectingProvider === 'google'}
//           className="flex items-center gap-1 px-3 py-1.5 bg-white border border-slate-200 text-slate-700 text-sm rounded-lg hover:bg-slate-50"
//         >
//           <svg className="w-4 h-4" viewBox="0 0 24 24">
//             <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
//             <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
//             <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
//             <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
//           </svg>
//           Connect Google
//         </button>
//       )
//     )}
//     
//     {/* Microsoft Outlook */}
//     {calendarConnections.microsoft.configured && (
//       calendarConnections.microsoft.connected ? (
//         <div className="flex items-center gap-1">
//           <button
//             onClick={() => handleSyncToExternal('microsoft')}
//             disabled={syncing}
//             className="flex items-center gap-1 px-3 py-1.5 bg-blue-50 text-blue-700 text-sm rounded-lg hover:bg-blue-100"
//             title="Sync to Outlook"
//           >
//             <Cloud className="w-4 h-4" />
//             Outlook
//           </button>
//           <button
//             onClick={() => handleDisconnect('microsoft')}
//             className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg"
//             title="Disconnect Outlook"
//           >
//             <Unlink className="w-4 h-4" />
//           </button>
//         </div>
//       ) : (
//         <button
//           onClick={handleConnectMicrosoft}
//           disabled={connectingProvider === 'microsoft'}
//           className="flex items-center gap-1 px-3 py-1.5 bg-white border border-slate-200 text-slate-700 text-sm rounded-lg hover:bg-slate-50"
//         >
//           <svg className="w-4 h-4" viewBox="0 0 23 23">
//             <path fill="#f25022" d="M1 1h10v10H1z"/>
//             <path fill="#00a4ef" d="M1 12h10v10H1z"/>
//             <path fill="#7fba00" d="M12 1h10v10H12z"/>
//             <path fill="#ffb900" d="M12 12h10v10H12z"/>
//           </svg>
//           Connect Outlook
//         </button>
//       )
//     )}
//   </div>
// )}
//
// =============================================================================


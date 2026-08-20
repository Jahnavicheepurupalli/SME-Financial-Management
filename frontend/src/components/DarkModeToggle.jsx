import React from 'react';
import * as Lucide from 'lucide-react';

export default function DarkModeToggle({ darkMode, toggleDarkMode, className = '' }) {
  return (
    <button
      onClick={toggleDarkMode}
      className={`p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm transition-all ${className}`}
    >
      {darkMode ? <Lucide.Sun className="h-5 w-5 text-teal-400" /> : <Lucide.Moon className="h-5 w-5 text-slate-600" />}
    </button>
  );
}

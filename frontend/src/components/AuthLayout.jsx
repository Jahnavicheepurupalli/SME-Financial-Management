import React from 'react';
import { motion } from 'framer-motion';
import * as Lucide from 'lucide-react';
import DarkModeToggle from './DarkModeToggle';

export default function AuthLayout({
  darkMode,
  toggleDarkMode,
  title,
  subtitle,
  subtitleClassName = '',
  headerSpacing = 'mb-6',
  children
}) {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-6 transition-colors duration-300 relative">
      <DarkModeToggle darkMode={darkMode} toggleDarkMode={toggleDarkMode} className="absolute top-6 right-6" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-md p-8 rounded-2xl glass-card border border-white/40 dark:border-slate-800 shadow-xl"
      >
        <div className={`text-center space-y-2 ${headerSpacing}`}>
          <div className="flex items-center justify-center gap-2">
            <Lucide.TrendingUp className="h-7 w-7 text-teal-600 dark:text-teal-400" />
            <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-teal-600 to-indigo-500 bg-clip-text text-transparent">
              FinIntel SME
            </span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
          <p className={`text-sm text-slate-500 ${subtitleClassName}`}>{subtitle}</p>
        </div>

        {children}
      </motion.div>
    </div>
  );
}

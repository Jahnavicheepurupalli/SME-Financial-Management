import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import * as Lucide from 'lucide-react';

export default function ForgotPassword({ darkMode, toggleDarkMode }) {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-6 transition-colors duration-300">
      <button 
        onClick={toggleDarkMode} 
        className="absolute top-6 right-6 p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm transition-all"
      >
        {darkMode ? <Lucide.Sun className="h-5 w-5 text-teal-400" /> : <Lucide.Moon className="h-5 w-5 text-slate-600" />}
      </button>

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-md p-8 rounded-2xl glass-card border border-white/40 dark:border-slate-800 shadow-xl"
      >
        <div className="text-center space-y-2 mb-6">
          <div className="flex items-center justify-center gap-2">
            <Lucide.TrendingUp className="h-7 w-7 text-teal-600 dark:text-teal-400" />
            <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-teal-600 to-indigo-500 bg-clip-text text-transparent">
              FinIntel SME
            </span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight">Reset Password</h2>
          <p className="text-sm text-slate-500">Password resets require administrator assistance</p>
        </div>

        <div className="p-4 bg-teal-50/70 border border-teal-100 dark:bg-teal-900/20 dark:border-teal-800 rounded-lg text-sm text-slate-600 dark:text-slate-300 space-y-3">
          <div className="flex items-start gap-3">
            <Lucide.Info className="h-5 w-5 text-teal-600 dark:text-teal-400 mt-0.5 shrink-0" />
            <p>
              Self-service password reset is unavailable. Contact an administrator
              to reset your password, or change it while signed in.
            </p>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            For your security, we do not accept password reset requests through
            this page.
          </p>
        </div>

        <p className="text-center text-xs text-slate-500 mt-6">
          Remember credentials?{' '}
          <Link to="/login" className="text-teal-600 hover:text-teal-700 font-semibold transition-colors">
            Back to Log In
          </Link>
        </p>
      </motion.div>
    </div>
  );
}

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import api from '../api/axios';
import { motion } from 'framer-motion';
import * as Lucide from 'lucide-react';

export default function ForgotPassword({ darkMode, toggleDarkMode }) {
  const { register, handleSubmit, watch, formState: { errors } } = useForm();
  const [serverError, setServerError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const password = watch('newPassword', '');

  const onSubmit = async (data) => {
    setIsLoading(true);
    setServerError('');
    setSuccessMsg('');
    try {
      await api.post('/auth/forgot-password', {
        email: data.email,
        new_password: data.newPassword,
        confirm_password: data.confirmNewPassword
      });
      
      setSuccessMsg('Password has been reset successfully! Redirecting to login...');
      setTimeout(() => navigate('/login'), 2000);
    } catch (error) {
      setServerError(error.response?.data?.message || 'Failed to reset password. Verify email is correct.');
    } finally {
      setIsLoading(false);
    }
  };

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
          <p className="text-sm text-slate-500">Provide account email and new credentials</p>
        </div>

        {serverError && (
          <div className="p-3 bg-red-100/70 border border-red-200 dark:bg-red-900/30 dark:border-red-800 rounded-lg text-xs text-red-600 dark:text-red-400 mb-4 flex items-center gap-2">
            <Lucide.AlertCircle className="h-4 w-4" />
            <span>{serverError}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-3 bg-green-100/70 border border-green-200 dark:bg-green-900/30 dark:border-green-800 rounded-lg text-xs text-green-600 dark:text-green-400 mb-4 flex items-center gap-2">
            <Lucide.CheckCircle className="h-4 w-4" />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Account Email</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                <Lucide.Mail className="h-4 w-4" />
              </span>
              <input 
                type="email" 
                {...register('email', { required: 'Email is required' })}
                placeholder="registered-email@company.com" 
                className="w-full pl-9 pr-4 py-1.5 text-sm bg-white/70 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
              />
            </div>
            {errors.email && <span className="text-xs text-red-500">{errors.email.message}</span>}
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">New Password</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                <Lucide.Lock className="h-4 w-4" />
              </span>
              <input 
                type="password" 
                {...register('newPassword', { 
                  required: 'New Password is required',
                  minLength: { value: 8, message: 'Minimum 8 characters' }
                })}
                placeholder="••••••••" 
                className="w-full pl-9 pr-4 py-1.5 text-sm bg-white/70 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
              />
            </div>
            {errors.newPassword && <span className="text-xs text-red-500">{errors.newPassword.message}</span>}
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Confirm New Password</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                <Lucide.Lock className="h-4 w-4" />
              </span>
              <input 
                type="password" 
                {...register('confirmNewPassword', { 
                  required: 'Please confirm password',
                  validate: (v) => v === password || 'Passwords do not match'
                })}
                placeholder="••••••••" 
                className="w-full pl-9 pr-4 py-1.5 text-sm bg-white/70 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
              />
            </div>
            {errors.confirmNewPassword && <span className="text-xs text-red-500">{errors.confirmNewPassword.message}</span>}
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-semibold text-sm shadow-sm transition-all flex items-center justify-center gap-2 mt-2"
          >
            {isLoading ? <Lucide.Loader className="h-4 w-4 animate-spin" /> : 'Reset Password'}
          </button>
        </form>

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

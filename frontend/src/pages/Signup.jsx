import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import api from '../api/axios';
import { motion, AnimatePresence } from 'framer-motion';
import * as Lucide from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';

export default function Signup({ darkMode, toggleDarkMode, googleAuthEnabled }) {
  const { register, handleSubmit, watch, formState: { errors } } = useForm();
  const [serverError, setServerError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showGoogleModal, setShowGoogleModal] = useState(false);
  const [customGoogleEmail, setCustomGoogleEmail] = useState('');
  const [customGoogleName, setCustomGoogleName] = useState('');
  const navigate = useNavigate();

  const password = watch('password', '');

  // Password rules validation regex
  const passwordRules = {
    required: 'Password is required',
    minLength: { value: 8, message: 'Minimum 8 characters' },
    validate: {
      hasUpper: (v) => /[A-Z]/.test(v) || 'Must contain at least one uppercase letter',
      hasLower: (v) => /[a-z]/.test(v) || 'Must contain at least one lowercase letter',
      hasNumber: (v) => /\d/.test(v) || 'Must contain at least one number',
      hasSpecial: (v) => /[@$!%*?&]/.test(v) || 'Must contain at least one special character (@$!%*?&)',
    }
  };

  const onSubmit = async (data) => {
    setIsLoading(true);
    setServerError('');
    setSuccessMsg('');
    try {
      await api.post('/auth/signup', {
        name: data.fullName,
        email: data.email,
        password: data.password,
        confirm_password: data.confirmPassword
      });
      setSuccessMsg('Account created successfully! Redirecting to login...');
      setTimeout(() => navigate('/login'), 2000);
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message || 'Registration failed. Please check your inputs.';
      setServerError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const executeGoogleAuth = async (email, name) => {
    setIsLoading(true);
    setServerError('');
    setShowGoogleModal(false);
    try {
      const response = await api.post('/auth/google', {
        email: email,
        full_name: name
      });
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      navigate('/dashboard');
    } catch (error) {
      setServerError('Google signup failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-6 transition-colors duration-300 relative">
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
          <h2 className="text-2xl font-bold tracking-tight">Create Account</h2>
          <p className="text-sm text-slate-500 font-medium">Register to begin document evaluation</p>
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
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Full Name</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                <Lucide.User className="h-4 w-4" />
              </span>
              <input 
                type="text" 
                {...register('fullName', { required: 'Name is required' })}
                placeholder="Aryan Sharma" 
                className="w-full pl-9 pr-4 py-1.5 text-sm bg-white/70 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
              />
            </div>
            {errors.fullName && <span className="text-xs text-red-500">{errors.fullName.message}</span>}
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Email Address</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                <Lucide.Mail className="h-4 w-4" />
              </span>
              <input 
                type="email" 
                {...register('email', { required: 'Email is required' })}
                placeholder="you@company.com" 
                className="w-full pl-9 pr-4 py-1.5 text-sm bg-white/70 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
              />
            </div>
            {errors.email && <span className="text-xs text-red-500">{errors.email.message}</span>}
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Password</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                <Lucide.Lock className="h-4 w-4" />
              </span>
              <input 
                type={showPassword ? 'text' : 'password'}
                {...register('password', passwordRules)}
                placeholder="••••••••" 
                className="w-full pl-9 pr-10 py-1.5 text-sm bg-white/70 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
              />
              <button 
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
              >
                {showPassword ? <Lucide.EyeOff className="h-4 w-4" /> : <Lucide.Eye className="h-4 w-4" />}
              </button>
            </div>
            {errors.password && <span className="text-xs text-red-500 block">{errors.password.message}</span>}
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">Confirm Password</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
                <Lucide.Lock className="h-4 w-4" />
              </span>
              <input 
                type={showPassword ? 'text' : 'password'}
                {...register('confirmPassword', { 
                  required: 'Please confirm password',
                  validate: (value) => value === password || 'Passwords do not match'
                })}
                placeholder="••••••••" 
                className="w-full pl-9 pr-4 py-1.5 text-sm bg-white/70 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all"
              />
            </div>
            {errors.confirmPassword && <span className="text-xs text-red-500">{errors.confirmPassword.message}</span>}
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-semibold text-sm shadow-sm transition-all flex items-center justify-center gap-2 mt-2"
          >
            {isLoading ? <Lucide.Loader className="h-4 w-4 animate-spin" /> : 'Sign Up'}
          </button>
        </form>

        {googleAuthEnabled && <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-200 dark:border-slate-800" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-slate-50 dark:bg-slate-900 px-2 text-slate-500">Or continue with</span>
          </div>
        </div>}

        {googleAuthEnabled && <div className="flex justify-center w-full">
          <GoogleLogin
            onSuccess={async (credentialResponse) => {
              setIsLoading(true);
              setServerError('');
              try {
                const response = await api.post('/auth/google', {
                  credential: credentialResponse.credential
                });
                localStorage.setItem('token', response.data.token);
                localStorage.setItem('user', JSON.stringify(response.data.user));
                navigate('/dashboard');
              } catch (error) {
                setServerError(error.response?.data?.message || 'Google authentication failed.');
              } finally {
                setIsLoading(false);
              }
            }}
            onError={() => {
              setServerError('Google authentication is temporarily unavailable. Please contact the administrator.');
            }}
            useOneTap
          />
        </div>}

        <p className="text-center text-xs text-slate-500 mt-4">
          Already have an account?{' '}
          <Link to="/login" className="text-teal-600 hover:text-teal-700 font-semibold transition-colors">
            Log In
          </Link>
        </p>
      </motion.div>
    </div>
  );
}

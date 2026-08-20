import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import api from '../api/axios';
import * as Lucide from 'lucide-react';
import AuthLayout from '../components/AuthLayout';
import Alert from '../components/Alert';
import FormField from '../components/FormField';
import PasswordVisibilityToggle from '../components/PasswordVisibilityToggle';
import SubmitButton from '../components/SubmitButton';
import GoogleAuthSection from '../components/GoogleAuthSection';
import { persistSession, getErrorMessage } from '../utils/session';
import { emailRules } from '../utils/validation';

export default function Login({ darkMode, toggleDarkMode }) {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [serverError, setServerError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const onSubmit = async (data) => {
    setIsLoading(true);
    setServerError('');
    try {
      const response = await api.post('/auth/login', {
        email: data.email,
        password: data.password
      });

      persistSession(response.data);
      navigate('/dashboard');
    } catch (error) {
      setServerError(getErrorMessage(error, 'Login failed. Verify your credentials.'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      darkMode={darkMode}
      toggleDarkMode={toggleDarkMode}
      title="Welcome Back"
      subtitle="Access your document intelligence reports"
      headerSpacing="mb-8"
    >
      <Alert variant="error" message={serverError} className="mb-6" />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <FormField
          label="Email Address"
          icon={Lucide.Mail}
          type="email"
          placeholder="you@company.com"
          registration={register('email', emailRules)}
          error={errors.email}
          size="md"
          spacing="space-y-1.5"
        />

        <FormField
          label="Password"
          icon={Lucide.Lock}
          type={showPassword ? 'text' : 'password'}
          placeholder="••••••••"
          registration={register('password', { required: 'Password is required' })}
          error={errors.password}
          size="md"
          spacing="space-y-1.5"
          rightSlot={<PasswordVisibilityToggle visible={showPassword} onToggle={() => setShowPassword(!showPassword)} />}
        />

        <div className="flex items-center justify-between text-xs">
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" className="rounded border-slate-300 dark:border-slate-700 text-teal-600 focus:ring-teal-500" />
            <span className="text-slate-500">Remember me</span>
          </label>
          <Link to="/forgot-password" className="text-teal-600 hover:text-teal-700 font-semibold transition-colors">
            Forgot Password?
          </Link>
        </div>

        <SubmitButton isLoading={isLoading} label="Log In" />
      </form>

      <GoogleAuthSection setIsLoading={setIsLoading} setError={setServerError} dividerClassName="my-6" />

      <p className="text-center text-xs text-slate-500 mt-6">
        Don't have an account?{' '}
        <Link to="/signup" className="text-teal-600 hover:text-teal-700 font-semibold transition-colors">
          Sign Up
        </Link>
      </p>
    </AuthLayout>
  );
}

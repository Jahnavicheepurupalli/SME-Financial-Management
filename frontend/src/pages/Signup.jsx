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
import { getErrorMessage } from '../utils/session';
import { emailRules, passwordRules, confirmPasswordRules } from '../utils/validation';

export default function Signup({ darkMode, toggleDarkMode }) {
  const { register, handleSubmit, watch, formState: { errors } } = useForm();
  const [serverError, setServerError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const password = watch('password', '');

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
      setServerError(getErrorMessage(error, 'Registration failed. Please check your inputs.'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      darkMode={darkMode}
      toggleDarkMode={toggleDarkMode}
      title="Create Account"
      subtitle="Register to begin document evaluation"
      subtitleClassName="font-medium"
    >
      <Alert variant="error" message={serverError} />
      <Alert variant="success" message={successMsg} />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          label="Full Name"
          icon={Lucide.User}
          placeholder="Aryan Sharma"
          registration={register('fullName', { required: 'Name is required' })}
          error={errors.fullName}
        />

        <FormField
          label="Email Address"
          icon={Lucide.Mail}
          type="email"
          placeholder="you@company.com"
          registration={register('email', emailRules)}
          error={errors.email}
        />

        <FormField
          label="Password"
          icon={Lucide.Lock}
          type={showPassword ? 'text' : 'password'}
          placeholder="••••••••"
          registration={register('password', passwordRules)}
          error={errors.password}
          errorClassName="text-xs text-red-500 block"
          rightSlot={<PasswordVisibilityToggle visible={showPassword} onToggle={() => setShowPassword(!showPassword)} />}
        />

        <FormField
          label="Confirm Password"
          icon={Lucide.Lock}
          type={showPassword ? 'text' : 'password'}
          placeholder="••••••••"
          registration={register('confirmPassword', confirmPasswordRules(() => password))}
          error={errors.confirmPassword}
        />

        <SubmitButton isLoading={isLoading} label="Sign Up" className="mt-2" />
      </form>

      <GoogleAuthSection setIsLoading={setIsLoading} setError={setServerError} dividerClassName="my-4" />

      <p className="text-center text-xs text-slate-500 mt-4">
        Already have an account?{' '}
        <Link to="/login" className="text-teal-600 hover:text-teal-700 font-semibold transition-colors">
          Log In
        </Link>
      </p>
    </AuthLayout>
  );
}

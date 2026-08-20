import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import api from '../api/axios';
import * as Lucide from 'lucide-react';
import AuthLayout from '../components/AuthLayout';
import Alert from '../components/Alert';
import FormField from '../components/FormField';
import SubmitButton from '../components/SubmitButton';
import { getServerMessage } from '../utils/session';
import { emailRules, confirmPasswordRules } from '../utils/validation';

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
      setServerError(getServerMessage(error, 'Failed to reset password. Verify email is correct.'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      darkMode={darkMode}
      toggleDarkMode={toggleDarkMode}
      title="Reset Password"
      subtitle="Provide account email and new credentials"
    >
      <Alert variant="error" message={serverError} />
      <Alert variant="success" message={successMsg} />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          label="Account Email"
          icon={Lucide.Mail}
          type="email"
          placeholder="registered-email@company.com"
          registration={register('email', emailRules)}
          error={errors.email}
        />

        <FormField
          label="New Password"
          icon={Lucide.Lock}
          type="password"
          placeholder="••••••••"
          registration={register('newPassword', {
            required: 'New Password is required',
            minLength: { value: 8, message: 'Minimum 8 characters' }
          })}
          error={errors.newPassword}
        />

        <FormField
          label="Confirm New Password"
          icon={Lucide.Lock}
          type="password"
          placeholder="••••••••"
          registration={register('confirmNewPassword', confirmPasswordRules(() => password))}
          error={errors.confirmNewPassword}
        />

        <SubmitButton isLoading={isLoading} label="Reset Password" className="mt-2" />
      </form>

      <p className="text-center text-xs text-slate-500 mt-6">
        Remember credentials?{' '}
        <Link to="/login" className="text-teal-600 hover:text-teal-700 font-semibold transition-colors">
          Back to Log In
        </Link>
      </p>
    </AuthLayout>
  );
}

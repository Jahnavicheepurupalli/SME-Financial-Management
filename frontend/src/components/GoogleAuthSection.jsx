import React from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import api from '../api/axios';
import { persistSession, getServerMessage } from '../utils/session';

const UNAVAILABLE_MESSAGE = 'Google authentication is temporarily unavailable. Please contact the administrator.';

export default function GoogleAuthSection({ setIsLoading, setError, dividerClassName = 'my-6' }) {
  const navigate = useNavigate();

  const handleSuccess = async (credentialResponse) => {
    setIsLoading(true);
    setError('');
    try {
      const response = await api.post('/auth/google', {
        credential: credentialResponse.credential
      });
      persistSession(response.data);
      navigate('/dashboard');
    } catch (error) {
      setError(getServerMessage(error, 'Google authentication failed.'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className={`relative ${dividerClassName}`}>
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-200 dark:border-slate-800" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-slate-50 dark:bg-slate-900 px-2 text-slate-500">Or continue with</span>
        </div>
      </div>

      <div className="flex justify-center w-full">
        <GoogleLogin
          onSuccess={handleSuccess}
          onError={() => setError(UNAVAILABLE_MESSAGE)}
          useOneTap
        />
      </div>
    </>
  );
}

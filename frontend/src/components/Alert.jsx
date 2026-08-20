import React from 'react';
import * as Lucide from 'lucide-react';

const VARIANTS = {
  error: {
    className: 'bg-red-100/70 border-red-200 dark:bg-red-900/30 dark:border-red-800 text-red-600 dark:text-red-400',
    Icon: Lucide.AlertCircle
  },
  success: {
    className: 'bg-green-100/70 border-green-200 dark:bg-green-900/30 dark:border-green-800 text-green-600 dark:text-green-400',
    Icon: Lucide.CheckCircle
  }
};

export default function Alert({ variant = 'error', message, className = 'mb-4' }) {
  if (!message) return null;

  const { className: variantClass, Icon } = VARIANTS[variant] || VARIANTS.error;

  return (
    <div className={`p-3 border rounded-lg text-xs flex items-center gap-2 ${variantClass} ${className}`}>
      <Icon className="h-4 w-4" />
      <span>{message}</span>
    </div>
  );
}

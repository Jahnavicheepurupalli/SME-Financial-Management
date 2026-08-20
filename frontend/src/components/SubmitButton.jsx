import React from 'react';
import * as Lucide from 'lucide-react';

export default function SubmitButton({ isLoading, label, className = '' }) {
  return (
    <button
      type="submit"
      disabled={isLoading}
      className={`w-full py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-semibold text-sm shadow-sm transition-all flex items-center justify-center gap-2 ${className}`}
    >
      {isLoading ? <Lucide.Loader className="h-4 w-4 animate-spin" /> : label}
    </button>
  );
}

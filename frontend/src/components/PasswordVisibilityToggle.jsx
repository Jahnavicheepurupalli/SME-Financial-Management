import React from 'react';
import * as Lucide from 'lucide-react';

export default function PasswordVisibilityToggle({ visible, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
    >
      {visible ? <Lucide.EyeOff className="h-4 w-4" /> : <Lucide.Eye className="h-4 w-4" />}
    </button>
  );
}

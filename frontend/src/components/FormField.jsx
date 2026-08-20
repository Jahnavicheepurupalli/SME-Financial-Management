import React from 'react';

const SIZES = {
  md: 'py-2',
  sm: 'py-1.5'
};

export default function FormField({
  label,
  icon: Icon,
  type = 'text',
  placeholder,
  registration,
  error,
  size = 'sm',
  spacing = 'space-y-1',
  rightSlot,
  errorClassName = 'text-xs text-red-500'
}) {
  return (
    <div className={spacing}>
      <label className="text-xs font-semibold text-slate-600 dark:text-slate-400">{label}</label>
      <div className="relative">
        <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
          <Icon className="h-4 w-4" />
        </span>
        <input
          type={type}
          {...registration}
          placeholder={placeholder}
          className={`w-full pl-9 ${rightSlot ? 'pr-10' : 'pr-4'} ${SIZES[size]} text-sm bg-white/70 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all`}
        />
        {rightSlot}
      </div>
      {error && <span className={errorClassName}>{error.message}</span>}
    </div>
  );
}

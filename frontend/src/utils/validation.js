export const emailRules = { required: 'Email is required' };

export const passwordRules = {
  required: 'Password is required',
  minLength: { value: 8, message: 'Minimum 8 characters' },
  validate: {
    hasUpper: (v) => /[A-Z]/.test(v) || 'Must contain at least one uppercase letter',
    hasLower: (v) => /[a-z]/.test(v) || 'Must contain at least one lowercase letter',
    hasNumber: (v) => /\d/.test(v) || 'Must contain at least one number',
    hasSpecial: (v) => /[@$!%*?&]/.test(v) || 'Must contain at least one special character (@$!%*?&)',
  }
};

export const confirmPasswordRules = (getPassword) => ({
  required: 'Please confirm password',
  validate: (value) => value === getPassword() || 'Passwords do not match'
});

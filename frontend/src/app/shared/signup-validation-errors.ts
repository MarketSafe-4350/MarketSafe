export const ValidationMessages = {
  firstName: {
    required: 'First name is required.',
    minlength: 'First name must be at least 2 characters.',
    maxlength: 'First name is too long.',
    pattern:
      'First name can only contain letters, spaces, hyphens, and apostrophes.',
  },

  lastName: {
    required: 'Last name is required.',
    minlength: 'Last name must be at least 2 characters.',
    maxlength: 'Last name is too long.',
    pattern:
      'Last name can only contain letters, spaces, hyphens, and apostrophes.',
  },

  email: {
    required: 'Email is required.',
    email: 'Please enter a valid email.',
    pattern: 'Must be a UManitoba email.',
  },

  password: {
    required: 'Password is required.',
    minlength: 'Password must be at least 8 characters.',
    pattern: 'Password must contain uppercase, lowercase, and number.',
  },
};

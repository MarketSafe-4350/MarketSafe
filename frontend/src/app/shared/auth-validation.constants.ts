// UManitoba email domains
export const UNIVERSITY_EMAIL_REGEX =
  /^[^@]+@(umanitoba\.ca|myumanitoba\.ca)$/i;

// password requirements:
// >= 8 chars
// at least 1 lowercase
// at least 1 uppercase
// at least 1 number
// no spaces
export const PASSWORD_REGEX =
  /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[^\s]{8,}$/;

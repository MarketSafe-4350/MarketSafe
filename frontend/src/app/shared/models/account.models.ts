/**
 *  Account model representing a user account in the system.
 *  This model includes basic account information and optional profile-related fields.
 */
export interface Account {
  id: number;
  email: string;
  fname: string;
  lname: string;
  verified: boolean;

  // optional profile-related fields
  ratingAvg?: number;
  ratingCount?: number;
}

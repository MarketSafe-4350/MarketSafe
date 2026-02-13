import { Routes } from '@angular/router';
import { SignupComponent } from './features/signup/signup.page';
import { ProfilePageComponent } from './features/profile-page/profile.page';
export const routes: Routes = [
  { path: 'signup', component: SignupComponent },
  { path: 'profile', component: ProfilePageComponent },
];

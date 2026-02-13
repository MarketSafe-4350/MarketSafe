import { Routes } from '@angular/router';
import { SignupComponent } from './features/signup/signup.page';
import { LandingComponent } from './features/landing/landing.component';
export const routes: Routes = [
  { path: '', component: LandingComponent },
  { path: 'signup', component: SignupComponent },
];

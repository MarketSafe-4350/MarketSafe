import { Routes } from '@angular/router';
import { SignupComponent } from './features/signup/signup.page';
import { ProfilePageComponent } from './features/profile-page/profile.page';
import { LandingComponent } from './features/landing/landing.component';
import { LoginComponent } from './features/login/login.component';
import { MainPageComponent } from './features/main-page/main-page.component';
import { MyListingsPageComponent } from './features/my-listings-page/my-listings-page.component';
import { SearchPageComponent } from './features/search-page/search-page.component';
import { VerifyEmailComponent } from './features/verify-email/verify-email.component';
import { AllOffersPageComponent } from './features/all-offers-page/all-offers-page.component';
import { authGuard } from './shared/auth.guard';

export const routes: Routes = [
  { path: '', component: LandingComponent },
  { path: 'signup', component: SignupComponent },
  { path: 'login', component: LoginComponent },
  { path: 'verify-email', component: VerifyEmailComponent },

  // Protected routes
  { path: 'profile', component: ProfilePageComponent, canActivate: [authGuard]},
  { path: 'profile/:sellerId', component: ProfilePageComponent, canActivate: [authGuard]},
  { path: 'main-page', component: MainPageComponent, canActivate: [authGuard]},
  { path: 'search', component: SearchPageComponent, canActivate: [authGuard]},
  { path: 'my-listings', component: MyListingsPageComponent, canActivate: [authGuard]},
  { path: 'offers', component: AllOffersPageComponent, canActivate: [authGuard]},
];

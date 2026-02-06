import { Routes } from '@angular/router';
import { SignupComponent } from './features/signup/signup.page';
import { FormFieldOverviewExample } from './features/test/test.page';
export const routes: Routes = [
  { path: 'signup', component: SignupComponent },
  { path: 'test', component: FormFieldOverviewExample },
];

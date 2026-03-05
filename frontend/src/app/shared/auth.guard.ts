import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

function hasToken(): boolean {
  return !!localStorage.getItem('access_token');
}

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);

  if (hasToken()) return true;

  router.navigate(['/login']);
  return false;
};
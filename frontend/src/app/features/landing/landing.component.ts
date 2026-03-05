import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { SignupComponent } from '../signup/signup.page';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    SignupComponent,
  ],
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.scss']
})
export class LandingComponent {

  private readonly router = inject(Router);

  showSignup(): void {
    this.router.navigate(['/signup']);
  }

  showLogin(): void {
    this.router.navigate(['/login']);
  }

}

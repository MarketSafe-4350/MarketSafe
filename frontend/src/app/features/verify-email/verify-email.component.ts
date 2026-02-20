import {
  ChangeDetectionStrategy,
  Component,
  signal,
  WritableSignal,
  inject,
  OnInit,
} from '@angular/core';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  standalone: true,
  selector: 'app-verify-email',
  templateUrl: './verify-email.component.html',
  styleUrls: ['./verify-email.component.scss'],
  imports: [
    CommonModule,
    RouterModule,
    MatCardModule,
    MatButtonModule,
    MatProgressSpinnerModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VerifyEmailComponent implements OnInit {
  loading: WritableSignal<boolean> = signal(true);
  success: WritableSignal<boolean> = signal(false);
  errorMessage: WritableSignal<string | null> = signal(null);

  private readonly route = inject(ActivatedRoute);
  readonly router = inject(Router);
  private readonly http = inject(HttpClient);

  ngOnInit(): void {
    this.verifyEmail();
  }

  verifyEmail(): void {
    // Extract the token from the query parameter
    this.route.queryParams.subscribe((params) => {
      const token = params['token'];

      if (!token) {
        this.loading.set(false);
        this.errorMessage.set('No verification token provided.');
        // Redirect to signup after a delay
        setTimeout(() => {
          this.router.navigate(['/signup']);
        }, 2000);
        return;
      }

      // Call the backend API to verify the email (GET request)
      const apiUrl = `http://localhost:8000/accounts/verify-email?token=${encodeURIComponent(token)}`;

      this.http.get<{ message?: string }>(apiUrl).subscribe({
        next: () => {
          this.loading.set(false);
          this.success.set(true);
          this.errorMessage.set(null);

          // Navigate to login after a delay
          setTimeout(() => {
            this.router.navigate(['/login']);
          }, 3000);
        },
        error: (err) => {
          this.loading.set(false);
          this.success.set(false);
          this.errorMessage.set(
            err.error?.error_message || 'Email verification failed. Please try again or contact support.'
          );
          
          // Redirect to signup after showing error
          setTimeout(() => {
            this.router.navigate(['/signup']);
          }, 3000);
        },
      });
    });
  }
}

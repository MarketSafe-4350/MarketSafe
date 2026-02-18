import {
  ChangeDetectionStrategy,
  Component,
  signal,
  WritableSignal,
  inject,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router, RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  Validators,
  ReactiveFormsModule,
} from '@angular/forms';
import { ValidationMessages } from '../../shared/signup-validation-errors';
import {
  UNIVERSITY_EMAIL_REGEX,
  PASSWORD_REGEX,
} from '../../shared/auth-validation.constants';


type Messages = Record<string, Record<string, string>>;

@Component({
  standalone: true,
  selector: 'app-signup-page',
  templateUrl: './signup.page.html',
  styleUrls: ['./signup.page.scss'],
  imports: [
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatIconModule,
    MatTooltipModule,
    ReactiveFormsModule,
    CommonModule,
    RouterModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SignupComponent {
  messages: Messages = ValidationMessages;

  hidePassword: WritableSignal<boolean> = signal(true);
  verificationLink: WritableSignal<string | null> = signal(null);
  loading: WritableSignal<boolean> = signal(false);
  error: WritableSignal<string | null> = signal(null);

  private readonly router = inject(Router);
  private readonly http = inject(HttpClient);


  // letters, spaces, hyphen, apostrophe
  private readonly nameRegex = /^[a-zA-Z'-\s]+$/;

  private readonly formBuilder = inject(FormBuilder);

  readonly form: FormGroup = this.createForm();

  toggleHide(event: MouseEvent, hideSignal: WritableSignal<boolean>): void {
    hideSignal.update((value) => !value);
    event.stopPropagation();
  }

  createForm(): FormGroup {
    return this.formBuilder.group({
      firstName: [
        '',
        [
          Validators.required,
          Validators.minLength(2),
          Validators.maxLength(50),
          Validators.pattern(this.nameRegex),
        ],
      ],
      lastName: [
        '',
        [
          Validators.required,
          Validators.minLength(2),
          Validators.maxLength(50),
          Validators.pattern(this.nameRegex),
        ],
      ],
      email: [
        '',
        [
          Validators.required,
          Validators.email,
          Validators.pattern(UNIVERSITY_EMAIL_REGEX),
        ],
      ],
      password: [
        '',
        [
          Validators.required,
          Validators.minLength(8),
          Validators.maxLength(128),
          Validators.pattern(PASSWORD_REGEX),
        ],
      ],
    });
  }

  goBack(): void {
    this.router.navigate(['/']);
  }


  markTouched(controlName: string): void {
    this.form.get(controlName)?.markAsTouched();
  }

  getErrorMessage(controlName: string): string {
    const control = this.form.get(controlName);
    if (!control || !control.errors) return '';

    const firstKey = Object.keys(control.errors)[0];
    return this.messages[controlName]?.[firstKey] ?? '';
  }

  onSubmit(): { firstName: string; lastName: string; email: string; password: string } | null {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return null;
    }

    this.loading.set(true);
    this.error.set(null);

    const payload = {
      firstName: this.form.value.firstName?.trim(),
      lastName: this.form.value.lastName?.trim(),
      email: this.form.value.email?.trim().toLowerCase(),
      password: this.form.value.password,
    };

    const formData = {
      fname: payload.firstName,
      lname: payload.lastName,
      email: payload.email,
      password: payload.password,
    };

    // Use the backend API URL - adjust based on your environment
    const apiUrl = 'http://localhost:8000/accounts'; // Change this for production

    this.http.post<any>(apiUrl, formData).subscribe({
      next: (response) => {
        this.loading.set(false);
        if (response.verification_link) {
          this.verificationLink.set(response.verification_link);
        }
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err.error?.error_message || 'Failed to create account. Please try again.');
      },
    });

    return payload;
  }

  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      console.log('Link copied to clipboard!');
    });
  }

  openVerificationLink(): void {
    const link = this.verificationLink();
    if (link) {
      window.open(link, '_blank');
    }
  }
}

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
import {
  FormBuilder,
  FormGroup,
  Validators,
  ReactiveFormsModule,
} from '@angular/forms';
import { ValidationMessages } from '../../shared/signup-validation-errors';

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
    ReactiveFormsModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SignupComponent {
  messages: Messages = ValidationMessages;

  hidePassword: WritableSignal<boolean> = signal(true);

  // umanitoba and myumanitoba email
  private readonly universityEmailRegex =
    /^[^@]+@(umanitoba\.ca|myumanitoba\.ca)$/i;

  // password requirements: >= 8 chars, 1 lower, 1 upper, 1 number (no spaces)
  private readonly passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[^\s]{8,}$/;

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
          Validators.pattern(this.universityEmailRegex),
        ],
      ],
      password: [
        '',
        [
          Validators.required,
          Validators.minLength(8),
          Validators.maxLength(128),
          Validators.pattern(this.passwordRegex),
        ],
      ],
    });
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

  onSubmit(): {
    firstName: string;
    lastName: string;
    email: string;
    password: string;
  } | null {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return null;
    }

    return {
      firstName: this.form.value.firstName?.trim(),
      lastName: this.form.value.lastName?.trim(),
      email: this.form.value.email?.trim().toLowerCase(),
      password: this.form.value.password,
    };
  }
}

import {
    ChangeDetectionStrategy,
    Component,
    WritableSignal,
    inject,
    signal,
} from '@angular/core';
import { Router } from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
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
import {
  UNIVERSITY_EMAIL_REGEX,
} from '../../shared/auth-validation.constants';


type Messages = Record<string, Record<string, string>>;

@Component({
    standalone: true,
    selector: 'app-login',
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.scss'],
    imports: [
        MatCardModule,
        MatButtonModule,
        MatFormFieldModule,
        MatInputModule,
        MatIconModule,
        ReactiveFormsModule,
    ],
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginComponent {
    messages: Messages = ValidationMessages;

    hidePassword: WritableSignal<boolean> = signal(true);

    private readonly router = inject(Router);
    private readonly formBuilder = inject(FormBuilder);


    readonly form: FormGroup = this.createForm();

    createForm(): FormGroup {
        return this.formBuilder.group({
            email: [
                '',
                [
                    Validators.required,
                    Validators.email,
                    Validators.pattern(UNIVERSITY_EMAIL_REGEX),
                ],
            ],
            password: ['', [Validators.required, Validators.minLength(8)]],
        });
    }

    goBack(): void {
        this.router.navigate(['/']);
    }

    toggleHide(event: MouseEvent, hideSignal: WritableSignal<boolean>): void {
        hideSignal.update((value) => !value);
        event.stopPropagation();
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

    onSubmit(): { email: string; password: string } | null {
        const emailCtrl = this.form.get('email');
        if (emailCtrl) {
            emailCtrl.setValue((emailCtrl.value ?? '').trim(), { emitEvent: false });
            emailCtrl.updateValueAndValidity({ emitEvent: false });
        }

        if (this.form.invalid) {
            this.form.markAllAsTouched();
            return null;
        }

        return {
            email: this.form.value.email?.trim().toLowerCase(),
            password: this.form.value.password,
        };
    }

}

import {
  ChangeDetectionStrategy,
  Component,
  signal,
  WritableSignal,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';

@Component({
  standalone: true,
  selector: 'signup-page',
  templateUrl: './signup.page.html',
  styleUrls: ['./signup.page.scss'],
  imports: [
    MatCardModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatIconModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SignupComponent {
  hidePassword: WritableSignal<boolean> = signal(true);
  hideConfirmPassword: WritableSignal<boolean> = signal(true);

  toggleHide(event: MouseEvent, hideSignal: WritableSignal<boolean>): void {
    hideSignal.update((value) => !value);
    event.stopPropagation();
  }
}

import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';

export interface CreateListingPayload {
  title: string;
  description: string;
  price: number;
  location: string;
  picture?: File | null;
}

@Component({
  selector: 'app-create-listing-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
  ],
  templateUrl: './create-listing.component.html',
  styleUrls: ['./create-listing.component.scss'],
})
export class CreateListingDialogComponent {
  private readonly fb = inject(FormBuilder);
  private readonly dialogRef = inject(MatDialogRef<CreateListingDialogComponent>);

  selectedFile: File | null = null;

  readonly form = this.fb.group({
    title: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(80)]],
    description: ['', [Validators.required, Validators.minLength(10), Validators.maxLength(1000)]],
    price: [null as number | null, [Validators.required, Validators.min(0)]],
    location: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(120)]],
  });

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.selectedFile = file;
  }

  cancel(): void {
    this.dialogRef.close(null);
  }

  create(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const payload: CreateListingPayload = {
      title: this.form.value.title!.trim(),
      description: this.form.value.description!.trim(),
      price: Number(this.form.value.price),
      location: this.form.value.location!.trim(),
      picture: this.selectedFile,
    };

    this.dialogRef.close(payload);
  }
}
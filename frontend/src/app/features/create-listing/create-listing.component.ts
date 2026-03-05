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
  readonly priceMax = 99_999_999.99;
  readonly locationMaxLength = 120;

  private readonly fb = inject(FormBuilder);
  private readonly dialogRef = inject(
    MatDialogRef<CreateListingDialogComponent>,
  );

  private readonly allowedImageTypes = [
    'image/jpeg',
    'image/png',
    'image/webp',
  ];
  private readonly allowedExtensions = ['.jpg', '.jpeg', '.png', '.webp'];

  selectedFile: File | null = null;

  readonly form = this.fb.group({
    title: [
      '',
      [Validators.required, Validators.minLength(2), Validators.maxLength(80)],
    ],
    description: [
      '',
      [
        Validators.required,
        Validators.minLength(10),
        Validators.maxLength(1000),
      ],
    ],
    price: [
      null as number | null,
      [Validators.required, Validators.min(0), Validators.max(this.priceMax)],
    ],
    location: [
      '',
      [
        Validators.required,
        Validators.minLength(2),
        Validators.maxLength(this.locationMaxLength),
      ],
    ],
    picture: [null as File | null],
  });

  onPriceInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const sanitized = this.sanitizePriceInput(input.value);

    if (input.value !== sanitized) {
      input.value = sanitized;
    }

    const numericValue = sanitized === '' ? null : Number(sanitized);
    this.form.get('price')?.setValue(numericValue, { emitEvent: false });
  }

  private sanitizePriceInput(rawValue: string): string {
    const cleaned = rawValue.replace(/[^\d.]/g, '');
    const [intPart = '', ...decimalParts] = cleaned.split('.');

    const limitedInt = intPart.slice(0, 8);
    const limitedDecimal = decimalParts.join('').slice(0, 2);
    const hasDecimalPoint = cleaned.includes('.');
    let normalized = hasDecimalPoint
      ? `${limitedInt}.${limitedDecimal}`
      : limitedInt;

    if (normalized.startsWith('.')) {
      normalized = `0${normalized}`;
    }

    const asNumber = Number(normalized);
    if (Number.isFinite(asNumber) && asNumber > this.priceMax) {
      return this.priceMax.toFixed(2);
    }

    return normalized;
  }

  private isValidImageFile(file: File): boolean {
    const fileName = file.name.toLowerCase();
    const extensionValid = this.allowedExtensions.some((ext) =>
      fileName.endsWith(ext),
    );
    const isValidMimeType = this.allowedImageTypes.includes(file.type);

    return extensionValid && isValidMimeType;
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;

    const pictureControl = this.form.get('picture');

    if (!file) {
      pictureControl?.reset(null);
      this.selectedFile = null;
      return;
    }

    if (!this.isValidImageFile(file)) {
      pictureControl?.setErrors({ invalidImage: true });
      pictureControl?.markAsTouched();
      pictureControl?.markAsDirty();

      input.value = '';
      this.selectedFile = null;
      return;
    }

    pictureControl?.setErrors(null);
    pictureControl?.setValue(file);
    pictureControl?.markAsTouched();
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

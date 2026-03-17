import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

export interface SendOfferPayload {
  offeredPrice: number;
  locationOffered: string;
}

@Component({
  selector: 'app-send-offer-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  templateUrl: './send-offer.component.html',
  styleUrls: ['./send-offer.component.scss'],
})
export class SendOfferDialogComponent {
  readonly priceMax = 99_999_999.99;
  readonly locationMaxLength = 120;

  private readonly fb = inject(FormBuilder);
  private readonly dialogRef = inject(MatDialogRef<SendOfferDialogComponent>);

  readonly form = this.fb.group({
    offeredPrice: [
      null as number | null,
      [Validators.required, Validators.min(0.01), Validators.max(this.priceMax)],
    ],
    locationOffered: [
      '',
      [
        Validators.required,
        Validators.minLength(2),
        Validators.maxLength(this.locationMaxLength),
      ],
    ],
  });

  onPriceInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const sanitized = this.sanitizePriceInput(input.value);

    if (input.value !== sanitized) {
      input.value = sanitized;
    }

    const numericValue = sanitized === '' ? null : Number(sanitized);
    this.form.get('offeredPrice')?.setValue(numericValue, { emitEvent: false });
  }

  cancel(): void {
    this.dialogRef.close(null);
  }

  send(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.dialogRef.close({
      offeredPrice: Number(this.form.value.offeredPrice),
      locationOffered: this.form.value.locationOffered!.trim(),
    } satisfies SendOfferPayload);
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
}

import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { Listing } from '../../shared/models/listing.models';
import { MatCardModule } from '@angular/material/card';

@Component({
  selector: 'app-listing-card',
  standalone: true,
  templateUrl: './listing-card.component.html',
  styleUrls: ['./listing-card.component.scss'],
  imports: [MatCardModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ListingCardComponent {
  @Input({ required: true }) listing: Listing | null = null;
  @Input() commentCount = 0;

  get title(): string {
    return this.listing?.title || 'Untitled Listing';
  }

  get imageUrl(): string {
    return this.listing?.imageUrl || '';
  }

  get price(): string {
    return this.listing
      ? `$${this.listing.price.toFixed(2)}`
      : 'Price Unavailable';
  }

  get description(): string {
    return this.listing?.description || 'No description provided.';
  }

  get location(): string {
    return this.listing?.location || 'Location Unavailable';
  }

  get createdAt(): string {
    if (!this.listing) return 'Date Unavailable';
    const date = new Date(this.listing.createdAt);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  get isSold(): boolean {
    return this.listing?.isSold ?? false;
  }

  get commentCountLabel(): string {
    return `${this.commentCount} comment${this.commentCount === 1 ? '' : 's'}`;
  }
}

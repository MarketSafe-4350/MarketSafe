import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin } from 'rxjs';
import { MatCardModule } from '@angular/material/card';
import { MatIcon } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
import { ListingsApiService } from '../../shared/services/listings-api.service';
import { Offer, OffersApiService } from '../../shared/services/offers-api.service';
import { Listing } from '../../shared/models/listing.models';

interface HeaderOfferPreview {
  id: number;
  listingId: number;
  listingTitle: string;
  offeredPrice: number;
  seen: boolean;
  createdDate: string | null;
}

@Component({
  selector: 'app-header',
  standalone: true,
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
  imports: [CommonModule, MatCardModule, MatIcon, MatMenuModule, MatButtonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HeaderComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly accountsApi = inject(AccountsApiService);
  private readonly offersApi = inject(OffersApiService);
  private readonly listingsApi = inject(ListingsApiService);

  readonly displayName = signal('Someone');
  readonly offers = signal<HeaderOfferPreview[]>([]);
  readonly unseenCount = signal(0);
  readonly isLoadingOffers = signal(false);
  readonly offersError = signal<string | null>(null);

  ngOnInit(): void {
    this.accountsApi.getMe().subscribe({
      next: (account) => {
        const fullName = `${account.fname} ${account.lname}`.trim();
        this.displayName.set(fullName || 'Someone');
      },
      error: (error) => {
        console.error('Failed to load current user for header:', error);
      },
    });

    this.loadOffers();
  }

  onLogout(): void {
    // Clear the authentication auth_token
    localStorage.removeItem('access_token');
    this.router.navigate(['/']);
  }

  goToProfile(): void {
    this.router.navigate(['/profile']);
  }

  goToOffersPage(): void {
    this.router.navigate(['/offers']);
  }

  onNotificationsOpened(): void {
    const unseenOffers = this.offers().filter((offer) => !offer.seen);
    if (unseenOffers.length === 0) {
      return;
    }

    forkJoin(unseenOffers.map((offer) => this.offersApi.markSeen(offer.id))).subscribe({
      next: () => {
        this.offers.update((offers) =>
          offers.map((offer) => ({
            ...offer,
            seen: true,
          })),
        );
        this.unseenCount.set(0);
      },
      error: (error) => {
        console.error('Failed to mark notification offers as seen:', error);
      },
    });
  }

  formatOfferDate(value: string | null): string {
    if (!value) {
      return 'Unknown time';
    }

    return new Date(value).toLocaleString();
  }

  private loadOffers(): void {
    this.isLoadingOffers.set(true);
    this.offersError.set(null);

    forkJoin({
      receivedOffers: this.offersApi.getReceived(),
      unseenOffers: this.offersApi.getReceivedUnseen(),
      myListings: this.listingsApi.getMine(),
    }).subscribe({
      next: ({ receivedOffers, unseenOffers, myListings }) => {
        this.offers.set(this.toOfferPreviews(receivedOffers, myListings));
        this.unseenCount.set(unseenOffers.length);
        this.isLoadingOffers.set(false);
      },
      error: (error) => {
        console.error('Failed to load header offers:', error);
        this.offersError.set('Failed to load offers.');
        this.isLoadingOffers.set(false);
      },
    });
  }

  private toOfferPreviews(
    offers: Offer[],
    myListings: Listing[],
  ): HeaderOfferPreview[] {
    const listingTitleById = new Map(
      myListings.map((listing) => [listing.id, listing.title]),
    );

    return [...offers]
      .sort((left, right) => {
        const leftDate = left.createdDate ? new Date(left.createdDate).getTime() : 0;
        const rightDate = right.createdDate ? new Date(right.createdDate).getTime() : 0;
        return rightDate - leftDate;
      })
      .slice(0, 3)
      .map((offer) => ({
        id: offer.id,
        listingId: offer.listingId,
        listingTitle:
          listingTitleById.get(offer.listingId) ?? `Listing #${offer.listingId}`,
        offeredPrice: offer.offeredPrice,
        seen: offer.seen,
        createdDate: offer.createdDate,
      }));
  }
}

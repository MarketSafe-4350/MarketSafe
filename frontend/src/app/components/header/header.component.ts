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
import { BuyerOfferNotificationsService } from '../../shared/services/buyer-offer-notifications.service';
import { Listing } from '../../shared/models/listing.models';

interface HeaderOfferPreview {
  id: number;
  listingId: number;
  listingTitle: string;
  offeredPrice: number;
  seen: boolean;
  createdDate: string | null;
  kind: 'received' | 'sent';
  accepted: boolean | null;
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
  private readonly buyerOfferNotifications = inject(BuyerOfferNotificationsService);
  private readonly currentUserId = this.getCurrentUserIdFromToken();

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
    const unseenOffers = this.offers().filter(
      (offer) => offer.kind === 'received' && !offer.seen,
    );
    const unseenBuyerResolutionIds = this.offers()
      .filter((offer) => offer.kind === 'sent' && !offer.seen)
      .map((offer) => offer.id);

    if (unseenBuyerResolutionIds.length > 0) {
      this.buyerOfferNotifications.markResolvedOffersSeen(
        unseenBuyerResolutionIds,
        this.currentUserId,
      );
    }

    if (unseenOffers.length === 0) {
      if (unseenBuyerResolutionIds.length > 0) {
        this.offers.update((offers) =>
          offers.map((offer) =>
            offer.kind === 'sent' ? { ...offer, seen: true } : offer,
          ),
        );
        this.unseenCount.set(0);
      }
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
      sentOffers: this.offersApi.getSent(),
      myListings: this.listingsApi.getMine(),
      allListings: this.listingsApi.getAll(),
    }).subscribe({
      next: ({
        receivedOffers,
        unseenOffers,
        sentOffers,
        myListings,
        allListings,
      }) => {
        const unseenBuyerResolutionIds = this.buyerOfferNotifications.syncResolvedOffers(
          sentOffers,
          this.currentUserId,
        );
        this.offers.set(
          this.toOfferPreviews(
            receivedOffers,
            sentOffers,
            myListings,
            allListings,
            unseenBuyerResolutionIds,
          ),
        );
        this.unseenCount.set(unseenOffers.length + unseenBuyerResolutionIds.size);
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
    receivedOffers: Offer[],
    sentOffers: Offer[],
    myListings: Listing[],
    allListings: Listing[],
    unseenBuyerResolutionIds: Set<number>,
  ): HeaderOfferPreview[] {
    const receivedListingTitleById = new Map(
      myListings.map((listing) => [listing.id, listing.title]),
    );
    const allListingTitleById = new Map(
      allListings.map((listing) => [listing.id, listing.title]),
    );

    const previews: HeaderOfferPreview[] = [
      ...receivedOffers.map((offer) => ({
        id: offer.id,
        listingId: offer.listingId,
        listingTitle:
          receivedListingTitleById.get(offer.listingId) ??
          `Listing #${offer.listingId}`,
        offeredPrice: offer.offeredPrice,
        seen: offer.seen,
        createdDate: offer.createdDate,
        kind: 'received' as const,
        accepted: offer.accepted,
      })),
      ...sentOffers
        .filter((offer) => offer.accepted !== null)
        .map((offer) => ({
          id: offer.id,
          listingId: offer.listingId,
          listingTitle:
            allListingTitleById.get(offer.listingId) ??
            `Listing #${offer.listingId}`,
          offeredPrice: offer.offeredPrice,
          seen: !unseenBuyerResolutionIds.has(offer.id),
          createdDate: offer.createdDate,
          kind: 'sent' as const,
          accepted: offer.accepted,
        })),
    ];

    return previews
      .sort((left, right) => {
        const leftDate = left.createdDate ? new Date(left.createdDate).getTime() : 0;
        const rightDate = right.createdDate ? new Date(right.createdDate).getTime() : 0;
        return rightDate - leftDate;
      })
      .slice(0, 3)
      .map((offer) => offer);
  }

  getNotificationSubtitle(offer: HeaderOfferPreview): string {
    if (offer.kind === 'sent') {
      return offer.accepted === true
        ? 'Seller accepted your offer'
        : 'Seller declined your offer';
    }

    return `New offer for $${offer.offeredPrice.toFixed(2)}`;
  }

  private getCurrentUserIdFromToken(): number | null {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return null;
    }

    const parts = token.split('.');
    if (parts.length < 2) {
      return null;
    }

    try {
      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=');
      const payload = JSON.parse(atob(padded)) as { sub?: string | number };
      const id = Number(payload.sub);
      return Number.isFinite(id) ? id : null;
    } catch {
      return null;
    }
  }
}

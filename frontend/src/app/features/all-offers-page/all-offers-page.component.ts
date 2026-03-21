import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

import { HeaderComponent } from '../../components/header/header.component';
import { LeftNavigationComponent } from '../left-navigation/left-navigation.component';
import { Account } from '../../shared/models/account.models';
import { Listing } from '../../shared/models/listing.models';
import { ListingsSidebarActionsBase } from '../../shared/helpers/listings-sidebar-actions.base';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
import { OffersApiService, Offer } from '../../shared/services/offers-api.service';

interface OfferViewModel {
  id: number;
  listingId: number;
  listingTitle: string;
  offeredPrice: number;
  locationOffered: string | null;
  senderId: number;
  buyerName: string;
  createdDate: string | null;
  seen: boolean;
  accepted: boolean | null;
  direction: 'received' | 'sent';
}

@Component({
  selector: 'app-all-offers-page',
  standalone: true,
  imports: [
    CommonModule,
    HeaderComponent,
    LeftNavigationComponent,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
  ],
  templateUrl: './all-offers-page.component.html',
  styleUrls: ['./all-offers-page.component.scss'],
})
export class AllOffersPageComponent
  extends ListingsSidebarActionsBase
  implements OnInit
{
  private readonly accountsApi = inject(AccountsApiService);
  private readonly offersApi = inject(OffersApiService);
  private readonly router = inject(Router);

  offers: OfferViewModel[] = [];
  receivedOffers: OfferViewModel[] = [];
  sentOffers: OfferViewModel[] = [];
  isLoading = false;
  private readonly resolvingOfferIds = new Set<number>();

  ngOnInit(): void {
    this.initializeSidebarListingActions();
    this.loadOffersPage();
  }

  openListing(listingId: number): void {
    void this.router.navigate(['/main-page'], {
      queryParams: { listingId },
    });
  }

  getStatusLabel(offer: OfferViewModel): string {
    if (offer.accepted === true) {
      return 'Accepted';
    }

    if (offer.accepted === false) {
      return 'Declined';
    }

    return 'Pending';
  }

  isResolvingOffer(offerId: number): boolean {
    return this.resolvingOfferIds.has(offerId);
  }

  canResolveOffer(offer: OfferViewModel): boolean {
    return offer.accepted === null && !this.isResolvingOffer(offer.id);
  }

  resolveOffer(offerId: number, accepted: boolean): void {
    if (this.resolvingOfferIds.has(offerId)) {
      return;
    }

    this.errorMessage = null;
    this.resolvingOfferIds.add(offerId);

    this.offersApi.resolve(offerId, accepted).subscribe({
      next: () => {
        this.receivedOffers = this.receivedOffers.map((offer) =>
          offer.id === offerId
            ? {
                ...offer,
                accepted,
              }
            : offer,
        );
        this.offers = [...this.receivedOffers, ...this.sentOffers];
        this.resolvingOfferIds.delete(offerId);
      },
      error: (error) => {
        console.error('Failed to resolve offer:', error);
        this.errorMessage = 'Failed to update offer status.';
        this.resolvingOfferIds.delete(offerId);
      },
    });
  }

  private loadOffersPage(): void {
    this.isLoading = true;
    this.errorMessage = null;

    forkJoin({
      listings: this.listingsApi.getMine(),
      allListings: this.listingsApi.getAll(),
      offers: this.offersApi.getReceived(),
      unseenOffers: this.offersApi.getReceivedUnseen(),
      sentOffers: this.offersApi.getSent(),
    }).subscribe({
      next: ({ listings, allListings, offers, unseenOffers, sentOffers }) => {
        this.listings = listings;
        this.loadOfferParties(offers, sentOffers, listings, allListings, unseenOffers);
      },
      error: (error) => {
        console.error('Failed to load offers page:', error);
        this.errorMessage = 'Failed to load offers.';
        this.isLoading = false;
      },
    });
  }

  private toOfferViewModels(
    offers: Offer[],
    listings: Listing[],
    buyerNameById: Map<number, string>,
    direction: 'received' | 'sent',
  ): OfferViewModel[] {
    const listingTitleById = new Map(
      listings.map((listing) => [listing.id, listing.title]),
    );

    return [...offers]
      .sort((left, right) => {
        const leftDate = left.createdDate
          ? new Date(left.createdDate).getTime()
          : 0;
        const rightDate = right.createdDate
          ? new Date(right.createdDate).getTime()
          : 0;
        return rightDate - leftDate;
      })
      .map((offer) => ({
        id: offer.id,
        listingId: offer.listingId,
        listingTitle:
          listingTitleById.get(offer.listingId) ??
          `Listing #${offer.listingId}`,
        offeredPrice: offer.offeredPrice,
        locationOffered: offer.locationOffered,
        senderId: offer.senderId,
        buyerName:
          buyerNameById.get(offer.senderId) ?? `User #${offer.senderId}`,
        createdDate: offer.createdDate,
        seen: offer.seen,
        accepted: offer.accepted,
        direction,
      }));
  }

  private loadOfferParties(
    receivedOffers: Offer[],
    sentOffers: Offer[],
    ownedListings: Listing[],
    allListings: Listing[],
    unseenOffers: Offer[],
  ): void {
    const uniqueSenderIds = [...new Set(receivedOffers.map((offer) => offer.senderId))];

    if (uniqueSenderIds.length === 0) {
      this.receivedOffers = this.toOfferViewModels(
        receivedOffers,
        ownedListings,
        new Map(),
        'received',
      );
      this.sentOffers = this.toOfferViewModels(
        sentOffers,
        allListings,
        new Map(),
        'sent',
      );
      this.offers = [...this.receivedOffers, ...this.sentOffers];
      this.isLoading = false;
      this.markOffersSeen(unseenOffers);
      return;
    }

    forkJoin(
      uniqueSenderIds.map((senderId) =>
        this.accountsApi.getById(senderId).pipe(
          catchError((error) => {
            console.error(`Failed to load buyer ${senderId}:`, error);
            return of(null);
          }),
        ),
      ),
    ).subscribe({
      next: (buyers) => {
        const buyerNameById = new Map<number, string>();
        buyers.forEach((buyer, index) => {
          const senderId = uniqueSenderIds[index];
          buyerNameById.set(senderId, this.toBuyerName(senderId, buyer));
        });

        this.receivedOffers = this.toOfferViewModels(
          receivedOffers,
          ownedListings,
          buyerNameById,
          'received',
        );
        this.sentOffers = this.toOfferViewModels(
          sentOffers,
          allListings,
          new Map(),
          'sent',
        );
        this.offers = [...this.receivedOffers, ...this.sentOffers];
        this.isLoading = false;
        this.markOffersSeen(unseenOffers);
      },
      error: (error) => {
        console.error('Failed to load buyer names:', error);
        this.receivedOffers = this.toOfferViewModels(
          receivedOffers,
          ownedListings,
          new Map(),
          'received',
        );
        this.sentOffers = this.toOfferViewModels(
          sentOffers,
          allListings,
          new Map(),
          'sent',
        );
        this.offers = [...this.receivedOffers, ...this.sentOffers];
        this.isLoading = false;
        this.markOffersSeen(unseenOffers);
      },
    });
  }

  private toBuyerName(senderId: number, account: Account | null): string {
    const fullName = `${account?.fname ?? ''} ${account?.lname ?? ''}`.trim();
    return fullName || `User #${senderId}`;
  }

  private markOffersSeen(unseenOffers: Offer[]): void {
    if (unseenOffers.length === 0) {
      return;
    }

    forkJoin(unseenOffers.map((offer) => this.offersApi.markSeen(offer.id))).subscribe({
      next: () => {
        this.offers = this.offers.map((offer) => ({
          ...offer,
          seen: true,
        }));
      },
      error: (error) => {
        console.error('Failed to mark offers as seen:', error);
      },
    });
  }
}

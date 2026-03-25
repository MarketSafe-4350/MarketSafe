import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
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
import { RatingsApiService } from '../../shared/services/ratings-api.service';
import { BuyerOfferNotificationsService } from '../../shared/services/buyer-offer-notifications.service';

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
  sellerId: number | null;
  sellerName: string;
  pendingRating: number | null;
  hasRatedSeller: boolean;
  isSubmittingRating: boolean;
  ratingMessage: string | null;
  ratingError: string | null;
  hasUnreadDecision: boolean;
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
  private readonly ratingsApi = inject(RatingsApiService);
  private readonly buyerOfferNotifications = inject(BuyerOfferNotificationsService);
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

  canRateSeller(offer: OfferViewModel): boolean {
    return (
      offer.direction === 'sent' &&
      offer.accepted === true &&
      !offer.hasRatedSeller &&
      !offer.isSubmittingRating
    );
  }

  setPendingRating(offerId: number, rating: number): void {
    this.sentOffers = this.sentOffers.map((offer) =>
      offer.id === offerId
        ? {
            ...offer,
            pendingRating: rating,
            ratingError: null,
            ratingMessage: null,
          }
        : offer,
    );
    this.offers = [...this.receivedOffers, ...this.sentOffers];
  }

  submitSellerRating(offer: OfferViewModel): void {
    if (!this.canRateSeller(offer) || offer.pendingRating === null) {
      this.sentOffers = this.sentOffers.map((item) =>
        item.id === offer.id
          ? { ...item, ratingError: 'Choose a star rating before submitting.' }
          : item,
      );
      this.offers = [...this.receivedOffers, ...this.sentOffers];
      return;
    }

    this.updateSentOffer(offer.id, {
      isSubmittingRating: true,
      ratingError: null,
      ratingMessage: null,
    });

    this.ratingsApi.create(offer.listingId, offer.pendingRating).subscribe({
      next: () => {
        this.updateSentOffer(offer.id, {
          hasRatedSeller: true,
          isSubmittingRating: false,
          ratingMessage: `You rated ${offer.sellerName}.`,
          ratingError: null,
        });
      },
      error: (error) => {
        this.updateSentOffer(offer.id, {
          isSubmittingRating: false,
          ratingError: this.toRatingErrorMessage(error),
        });
      },
    });
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
    partyNameById: Map<number, string>,
    direction: 'received' | 'sent',
    unreadSentOfferIds: Set<number>,
  ): OfferViewModel[] {
    const listingTitleById = new Map(
      listings.map((listing) => [listing.id, listing.title]),
    );
    const listingSellerIdById = new Map(
      listings.map((listing) => [listing.id, listing.sellerId ?? null]),
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
          direction === 'received'
            ? partyNameById.get(offer.senderId) ?? `User #${offer.senderId}`
            : '',
        createdDate: offer.createdDate,
        seen: offer.seen,
        accepted: offer.accepted,
        direction,
        sellerId: listingSellerIdById.get(offer.listingId) ?? null,
        sellerName:
          direction === 'sent'
            ? partyNameById.get(listingSellerIdById.get(offer.listingId) ?? -1) ??
              `Seller #${listingSellerIdById.get(offer.listingId) ?? offer.listingId}`
            : '',
        pendingRating: null,
        hasRatedSeller: false,
        isSubmittingRating: false,
        ratingMessage: null,
        ratingError: null,
        hasUnreadDecision:
          direction === 'sent' && unreadSentOfferIds.has(offer.id),
      }));
  }

  private loadOfferParties(
    receivedOffers: Offer[],
    sentOffers: Offer[],
    ownedListings: Listing[],
    allListings: Listing[],
    unseenOffers: Offer[],
  ): void {
    const unreadSentOfferIds = this.buyerOfferNotifications.syncResolvedOffers(
      sentOffers,
      this.currentUserId,
    );
    const uniquePartyIds = [
      ...new Set([
        ...receivedOffers.map((offer) => offer.senderId),
        ...sentOffers
          .map((offer) => allListings.find((listing) => listing.id === offer.listingId)?.sellerId)
          .filter((sellerId): sellerId is number => sellerId !== undefined),
      ]),
    ];

    if (uniquePartyIds.length === 0) {
      this.receivedOffers = this.toOfferViewModels(
        receivedOffers,
        ownedListings,
        new Map(),
        'received',
        unreadSentOfferIds,
      );
      this.sentOffers = this.toOfferViewModels(
        sentOffers,
        allListings,
        new Map(),
        'sent',
        unreadSentOfferIds,
      );
      this.offers = [...this.receivedOffers, ...this.sentOffers];
      this.isLoading = false;
      this.markOffersSeen(unseenOffers);
      this.markSentOfferDecisionsSeen();
      this.loadSentOfferRatings();
      return;
    }

    forkJoin(
      uniquePartyIds.map((accountId) =>
        this.accountsApi.getById(accountId).pipe(
          catchError((error) => {
            console.error(`Failed to load account ${accountId}:`, error);
            return of(null);
          }),
        ),
      ),
    ).subscribe({
      next: (accounts) => {
        const partyNameById = new Map<number, string>();
        accounts.forEach((account, index) => {
          const accountId = uniquePartyIds[index];
          partyNameById.set(accountId, this.toBuyerName(accountId, account));
        });

        this.receivedOffers = this.toOfferViewModels(
          receivedOffers,
          ownedListings,
          partyNameById,
          'received',
          unreadSentOfferIds,
        );
        this.sentOffers = this.toOfferViewModels(
          sentOffers,
          allListings,
          partyNameById,
          'sent',
          unreadSentOfferIds,
        );
        this.offers = [...this.receivedOffers, ...this.sentOffers];
        this.isLoading = false;
        this.markOffersSeen(unseenOffers);
        this.markSentOfferDecisionsSeen();
        this.loadSentOfferRatings();
      },
      error: (error) => {
        console.error('Failed to load buyer names:', error);
        this.receivedOffers = this.toOfferViewModels(
          receivedOffers,
          ownedListings,
          new Map(),
          'received',
          unreadSentOfferIds,
        );
        this.sentOffers = this.toOfferViewModels(
          sentOffers,
          allListings,
          new Map(),
          'sent',
          unreadSentOfferIds,
        );
        this.offers = [...this.receivedOffers, ...this.sentOffers];
        this.isLoading = false;
        this.markOffersSeen(unseenOffers);
        this.markSentOfferDecisionsSeen();
        this.loadSentOfferRatings();
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

  private markSentOfferDecisionsSeen(): void {
    const unreadDecisionIds = this.sentOffers
      .filter((offer) => offer.hasUnreadDecision)
      .map((offer) => offer.id);

    if (unreadDecisionIds.length === 0) {
      return;
    }

    this.buyerOfferNotifications.markResolvedOffersSeen(
      unreadDecisionIds,
      this.currentUserId,
    );
    this.sentOffers = this.sentOffers.map((offer) => ({
      ...offer,
      hasUnreadDecision: false,
    }));
    this.offers = [...this.receivedOffers, ...this.sentOffers];
  }

  private loadSentOfferRatings(): void {
    const acceptedSentOffers = this.sentOffers.filter((offer) => offer.accepted === true);
    if (acceptedSentOffers.length === 0) {
      return;
    }

    forkJoin(
      acceptedSentOffers.map((offer) =>
        this.ratingsApi.getByListingId(offer.listingId).pipe(
          catchError((error) => {
            console.error(`Failed to load rating for listing ${offer.listingId}:`, error);
            return of(null);
          }),
        ),
      ),
    ).subscribe({
      next: (ratings) => {
        acceptedSentOffers.forEach((offer, index) => {
          const rating = ratings[index];
          if (rating) {
            this.updateSentOffer(offer.id, {
              hasRatedSeller: true,
              pendingRating: rating.transactionRating,
              ratingMessage: 'You already rated this seller.',
            });
          }
        });
      },
      error: (error) => {
        console.error('Failed to load sent offer ratings:', error);
      },
    });
  }

  private updateSentOffer(
    offerId: number,
    changes: Partial<OfferViewModel>,
  ): void {
    this.sentOffers = this.sentOffers.map((offer) =>
      offer.id === offerId ? { ...offer, ...changes } : offer,
    );
    this.offers = [...this.receivedOffers, ...this.sentOffers];
  }

  private toRatingErrorMessage(error: unknown): string {
    if (error instanceof HttpErrorResponse) {
      if (error.status === 400 || error.status === 422) {
        return 'Choose a rating between 1 and 5 stars.';
      }

      if (error.status === 403 || error.status === 409) {
        return 'This seller was already rated for this listing.';
      }
    }

    return 'Failed to submit rating.';
  }
}

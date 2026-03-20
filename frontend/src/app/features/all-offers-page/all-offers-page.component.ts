import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin } from 'rxjs';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

import { HeaderComponent } from '../../components/header/header.component';
import { LeftNavigationComponent } from '../left-navigation/left-navigation.component';
import { Listing } from '../../shared/models/listing.models';
import { ListingsSidebarActionsBase } from '../../shared/helpers/listings-sidebar-actions.base';
import { OffersApiService, Offer } from '../../shared/services/offers-api.service';

interface OfferViewModel {
  id: number;
  listingId: number;
  listingTitle: string;
  offeredPrice: number;
  locationOffered: string | null;
  senderId: number;
  createdDate: string | null;
  seen: boolean;
  accepted: boolean | null;
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
  private readonly offersApi = inject(OffersApiService);
  private readonly router = inject(Router);

  offers: OfferViewModel[] = [];
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
        this.offers = this.offers.map((offer) =>
          offer.id === offerId
            ? {
                ...offer,
                accepted,
              }
            : offer,
        );
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
      offers: this.offersApi.getReceived(),
      unseenOffers: this.offersApi.getReceivedUnseen(),
    }).subscribe({
      next: ({ listings, offers, unseenOffers }) => {
        this.listings = listings;
        this.offers = this.toOfferViewModels(offers, listings);
        this.isLoading = false;
        this.markOffersSeen(unseenOffers);
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
        createdDate: offer.createdDate,
        seen: offer.seen,
        accepted: offer.accepted,
      }));
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

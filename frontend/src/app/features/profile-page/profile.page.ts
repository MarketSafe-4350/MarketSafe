import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { forkJoin } from 'rxjs';
import { ActivatedRoute } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';

import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';

import { Account } from '../../shared/models/account.models';
import { Listing } from '../../shared/models/listing.models';

import { RatingComponent } from '../../components/rating/rating.component';
import { ListingCardComponent } from '../../components/listing-card/listing-card.component';
import { HeaderComponent } from '../../components/header/header.component';
import { LeftNavigationComponent } from '../left-navigation/left-navigation.component';

import { AccountsApiService } from '../../shared/services/accounts-api.service';
import { ListingsSidebarActionsBase } from '../../shared/helpers/listings-sidebar-actions.base';
import { OffersApiService } from '../../shared/services/offers-api.service';
import {
  SendOfferDialogComponent,
  SendOfferPayload,
} from '../send-offer/send-offer.component';
@Component({
  standalone: true,
  selector: 'app-profile-page',
  templateUrl: './profile.page.html',
  styleUrls: ['./profile.page.scss'],
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatDividerModule,
    MatChipsModule,
    RatingComponent,
    ListingCardComponent,
    HeaderComponent,
    LeftNavigationComponent,
  ],
})
export class ProfilePageComponent
  extends ListingsSidebarActionsBase
  implements OnInit
{
  private readonly accountsApi = inject(AccountsApiService);
  private readonly offersApi = inject(OffersApiService);
  private readonly dialog = inject(MatDialog);
  private readonly route = inject(ActivatedRoute);
  readonly stars = [0, 1, 2, 3, 4];

  account: Account | null = null;
  profileListings: Listing[] = [];
  viewedSellerId: number | null = null;
  offerFeedbackMessage: string | null = null;
  private readonly blockedOfferListingIds = new Set<number>();

  ngOnInit(): void {
    this.initializeSidebarListingActions();
    this.route.paramMap.subscribe((params) => {
      const sellerIdParam = params.get('sellerId');
      const sellerId = sellerIdParam === null ? Number.NaN : Number(sellerIdParam);
      const isOwnProfileRoute =
        Number.isFinite(sellerId) && this.currentUserId !== null && sellerId === this.currentUserId;

      this.viewedSellerId =
        Number.isFinite(sellerId) && !isOwnProfileRoute ? sellerId : null;
      this.loadProfile();
    });
  }

  private loadProfile(): void {
    this.errorMessage = null;

    if (this.isSellerProfile) {
      forkJoin({
        sidebarListings: this.listingsApi.getMine(),
        account: this.accountsApi.getById(this.viewedSellerId as number),
        profileListings: this.listingsApi.getBySeller(this.viewedSellerId as number),
        sentOffers: this.offersApi.getSent(),
      }).subscribe({
        next: ({ sidebarListings, account, profileListings, sentOffers }) => {
          this.account = account;
          this.listings = sidebarListings;
          this.profileListings = this.getActiveListings(profileListings);
          this.replaceBlockedOfferListingIds(sentOffers);
        },
        error: (err) => {
          console.error('Failed to load seller profile:', err);
          this.errorMessage = 'Failed to load seller profile.';
        },
      });

      return;
    }

    forkJoin({
      account: this.accountsApi.getMe(),
      listings: this.listingsApi.getMine(),
    }).subscribe({
      next: ({ account, listings }) => {
        this.account = account;
        this.listings = listings;
        this.profileListings = this.getActiveListings(listings);
      },
      error: (err) => {
        console.error('Failed to load profile:', err);
        this.errorMessage = 'Failed to load profile.';
      },
    });
  }

  // getters
  get fullName(): string {
    return this.account ? `${this.account.fname} ${this.account.lname}` : '—';
  }

  get firstName(): string {
    return this.account?.fname ?? '—';
  }

  get lastName(): string {
    return this.account?.lname ?? '—';
  }

  get isVerified(): boolean {
    return this.account?.verified ?? false;
  }

  get isSellerProfile(): boolean {
    return this.viewedSellerId !== null;
  }

  get pageTitle(): string {
    return this.isSellerProfile ? 'Seller Profile' : 'My Profile';
  }

  get ratingTitle(): string {
    return this.isSellerProfile ? 'Seller Rating' : 'My Rating';
  }

  get listingsTitle(): string {
    return this.isSellerProfile ? 'Seller Listings' : 'My Listings';
  }

  get ratingAvg(): number {
    return this.account?.ratingAvg ?? 0;
  }

  get ratingCount(): number {
    if (this.account?.ratingCount !== undefined) {
      return this.account.ratingCount;
    }

    const ratingAvg = this.account?.ratingAvg ?? 0;
    const ratingSum = this.account?.ratingSum ?? 0;

    if (ratingAvg <= 0 || ratingSum <= 0) {
      return 0;
    }

    return Math.max(0, Math.round(ratingSum / ratingAvg));
  }

  canSendOffer(listing: Listing): boolean {
    return (
      this.isSellerProfile &&
      this.currentUserId !== null &&
      listing.sellerId !== this.currentUserId &&
      !listing.isSold &&
      !this.hasBlockingOffer(listing.id)
    );
  }

  getOfferButtonLabel(listingId: number): string {
    return this.hasBlockingOffer(listingId) ? 'Offer Sent' : 'Send Offer';
  }

  openSendOfferDialog(listing: Listing): void {
    if (!this.canSendOffer(listing)) {
      return;
    }

    const ref = this.dialog.open(SendOfferDialogComponent, {
      width: '460px',
      maxWidth: '92vw',
    });

    ref.afterClosed().subscribe((payload: SendOfferPayload | null) => {
      if (!payload) {
        return;
      }

      this.offersApi
        .create({
          listingId: listing.id,
          offeredPrice: payload.offeredPrice,
          locationOffered: payload.locationOffered,
        })
        .subscribe({
          next: () => {
            this.blockedOfferListingIds.add(listing.id);
            this.offerFeedbackMessage = `Offer sent for ${listing.title}.`;
          },
          error: (error) => {
            console.error('Failed to send offer:', error);
            if (this.isDuplicateOfferError(error)) {
              this.blockedOfferListingIds.add(listing.id);
              this.offerFeedbackMessage = `You already sent an offer for ${listing.title}.`;
              return;
            }
            this.offerFeedbackMessage = 'Failed to send offer.';
          },
        });
    });
  }

  private getActiveListings(listings: Listing[]): Listing[] {
    return listings.filter((listing) => !listing.isSold);
  }

  private hasBlockingOffer(listingId: number): boolean {
    return this.blockedOfferListingIds.has(listingId);
  }

  private replaceBlockedOfferListingIds(
    sentOffers: Array<{ listingId: number; accepted: boolean | null }>,
  ): void {
    this.blockedOfferListingIds.clear();
    for (const offer of sentOffers) {
      if (offer.accepted !== false) {
        this.blockedOfferListingIds.add(offer.listingId);
      }
    }
  }

  private isDuplicateOfferError(error: unknown): boolean {
    return error instanceof HttpErrorResponse && error.status === 409;
  }
}

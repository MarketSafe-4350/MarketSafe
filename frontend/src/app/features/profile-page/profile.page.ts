import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin } from 'rxjs';
import { ActivatedRoute } from '@angular/router';

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
  private readonly route = inject(ActivatedRoute);
  readonly stars = [0, 1, 2, 3, 4];

  account: Account | null = null;
  profileListings: Listing[] = [];
  viewedSellerId: number | null = null;

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
      }).subscribe({
        next: ({ sidebarListings, account, profileListings }) => {
          this.account = account;
          this.listings = sidebarListings;
          this.profileListings = this.getActiveListings(profileListings);
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

  private getActiveListings(listings: Listing[]): Listing[] {
    return listings.filter((listing) => !listing.isSold);
  }
}

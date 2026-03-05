import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin } from 'rxjs';

import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';

import { Account } from '../../shared/models/account.models';

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
  readonly stars = [0, 1, 2, 3, 4];

  account: Account | null = null;

  ngOnInit(): void {
    this.initializeSidebarListingActions();
    this.loadProfile();
  }

  private loadProfile(): void {
    forkJoin({
      account: this.accountsApi.getMe(),
      listings: this.listingsApi.getMine(),
    }).subscribe({
      next: ({ account, listings }) => {
        this.account = account;
        this.listings = listings;
        this.errorMessage = null;
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

  get ratingAvg(): number {
    return this.account?.ratingAvg ?? 0;
  }

  get ratingCount(): number {
    return this.account?.ratingCount ?? 0;
  }
}

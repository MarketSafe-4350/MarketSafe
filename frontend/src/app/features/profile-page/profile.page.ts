import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { forkJoin } from 'rxjs';

import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';

import { Account } from '../../shared/models/account.models';
import { Listing } from '../../shared/models/listing.models';

import { RatingComponent } from '../../components/rating/rating.component';
import { ListingCardComponent } from '../../components/listing-card/listing-card.component';

import { HttpClient } from '@angular/common/http';
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
  ],
})
export class ProfilePageComponent implements OnInit {
  private readonly http = inject(HttpClient);
  readonly stars = [0, 1, 2, 3, 4];

  account: Account | null = null;
  listings: Listing[] = [];

  errorMessage: string | null = null;

  ngOnInit(): void {
    this.loadProfile();
  }

  /**
   * Loads profile data
   * TODO: Replace mock data with API call.
   */
  private loadProfile(): void {
    forkJoin({
      account: this.http.get<Account>('assets/mocks/profile-mock.json'),
      listings: this.http.get<Listing[]>('assets/mocks/listing-mock.json'),
    }).subscribe({
      next: ({ account, listings }) => {
        this.account = account;
        this.listings = listings;
        this.errorMessage = null;
      },
      error: (err) => {
        console.error('Failed to load mock files:', err);
        this.errorMessage = 'Failed to load mock data.';
      },
    });
  }

  // getters
  get fullName(): string {
    return this.account ? `${this.account.fname} ${this.account.lname}` : '—';
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

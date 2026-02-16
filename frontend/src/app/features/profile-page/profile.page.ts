import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';

import { Account } from '../../shared/models/account.models';
import { Listing } from '../../shared/models/listing.models';

import { RatingComponent } from '../../components/rating/rating.component';
import { ListingCardComponent } from '../../components/listing-card/listing-card.component';

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
  readonly stars = [0, 1, 2, 3, 4];

  account: Account | null = null;
  listings: Listing[] = [];

  isLoading = false;
  errorMessage: string | null = null;

  ngOnInit(): void {
    this.loadProfile();
  }

  /**
   * Loads profile data
   * TODO: Replace mock data with API call.
   */
  private loadProfile(): void {
    // mock data (temporary)
    const mockResponse: { account: Account; listings: Listing[] } = {
      account: {
        id: 1,
        email: 'test@myumanitoba.ca',
        fname: 'First',
        lname: 'Last',
        verified: true,
        ratingAvg: 4.5,
        ratingCount: 271,
      },
      listings: [
        {
          id: 101,
          title: 'Calculus Textbook',
          description: 'Good condition.',
          imageUrl: 'assets/images/computer.png',
          price: 45,
          location: 'University of Manitoba',
          createdAt: new Date().toISOString(),
          isSold: false,
        },
        {
          id: 102,
          title: 'Dell Monitor',
          description: 'Works perfectly.',
          imageUrl: 'assets/images/computer.png',
          price: 120,
          location: 'Fort Garry',
          createdAt: new Date().toISOString(),
          isSold: true,
        },
        {
          id: 103,
          title: 'Dell Monitor',
          description: 'Works perfectly.',
          imageUrl: 'assets/images/computer.png',
          price: 120,
          location: 'Fort Garry',
          createdAt: new Date().toISOString(),
          isSold: true,
        },
        {
          id: 104,
          title: 'Dell Monitor',
          description: 'Works perfectly.',
          imageUrl: 'assets/images/computer.png',
          price: 120,
          location: 'Fort Garry',
          createdAt: new Date().toISOString(),
          isSold: true,
        },
        {
          id: 105,
          title: 'Dell Monitor',
          description: 'Works perfectly.',
          imageUrl: 'assets/images/computer.png',
          price: 120,
          location: 'Fort Garry',
          createdAt: new Date().toISOString(),
          isSold: true,
        },
        {
          id: 106,
          title: 'Dell Monitor',
          description: 'Works perfectly.',
          imageUrl: 'assets/images/computer.png',
          price: 120,
          location: 'Fort Garry',
          createdAt: new Date().toISOString(),
          isSold: true,
        },
        {
          id: 106,
          title: 'Dell Monitor',
          description: 'Works perfectly.',
          imageUrl: 'assets/images/computer.png',
          price: 120,
          location: 'Fort Garry',
          createdAt: new Date().toISOString(),
          isSold: true,
        },
        {
          id: 106,
          title: 'Dell Monitor',
          description: 'Works perfectly.',
          imageUrl: 'assets/images/computer.png',
          price: 120,
          location: 'Fort Garry',
          createdAt: new Date().toISOString(),
          isSold: true,
        },
        {
          id: 106,
          title: 'Dell Monitor',
          description: 'Works perfectly.',
          imageUrl: 'assets/images/computer.png',
          price: 120,
          location: 'Fort Garry',
          createdAt: new Date().toISOString(),
          isSold: true,
        },
        {
          id: 106,
          title: 'Dell Monitor',
          description: 'Works perfectly.',
          imageUrl: 'assets/images/computer.png',
          price: 120,
          location: 'Fort Garry',
          createdAt: new Date().toISOString(),
          isSold: true,
        },
      ],
    };

    this.account = mockResponse.account;
    this.listings = mockResponse.listings;

    this.isLoading = false;
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

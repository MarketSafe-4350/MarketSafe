import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { HeaderComponent } from '../../components/header/header.component';
import { LeftNavigationComponent } from '../left-navigation/left-navigation.component';
import { ListingCardComponent } from '../../components/listing-card/listing-card.component';
import { ListingsSidebarActionsBase } from '../../shared/helpers/listings-sidebar-actions.base';

@Component({
  selector: 'app-my-listings-page',
  standalone: true,
  imports: [
    CommonModule,
    HeaderComponent,
    LeftNavigationComponent,
    ListingCardComponent,
    MatButtonModule,
    MatIconModule,
  ],
  templateUrl: './my-listings-page.component.html',
  styleUrls: ['./my-listings-page.component.scss'],
})
export class MyListingsPageComponent
  extends ListingsSidebarActionsBase
  implements OnInit
{
  isLoading = false;

  ngOnInit(): void {
    this.initializeSidebarListingActions();
    this.loadMyListings();
  }

  private loadMyListings(): void {
    this.isLoading = true;
    this.errorMessage = null;

    this.listingsApi.getMine().subscribe({
      next: (listings) => {
        this.listings = listings;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load my listings:', error);
        this.errorMessage = 'Failed to load your listings.';
        this.isLoading = false;
      },
    });
  }
}

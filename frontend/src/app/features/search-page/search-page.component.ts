import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';

import { HeaderComponent } from '../../components/header/header.component';
import { ListingCardComponent } from '../../components/listing-card/listing-card.component';
import { LeftNavigationComponent } from '../left-navigation/left-navigation.component';
import { ListingsSidebarActionsBase } from '../../shared/helpers/listings-sidebar-actions.base';
import { Listing } from '../../shared/models/listing.models';

@Component({
  selector: 'app-search-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    HeaderComponent,
    LeftNavigationComponent,
    ListingCardComponent,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
  ],
  templateUrl: './search-page.component.html',
  styleUrls: ['./search-page.component.scss'],
})
export class SearchPageComponent extends ListingsSidebarActionsBase implements OnInit {
  private readonly router = inject(Router);
  searchQuery = '';
  searchResults: Listing[] = [];
  isLoading = false;
  hasSearched = false;
  searchErrorMessage: string | null = null;

  ngOnInit(): void {
    this.initializeSidebarListingActions();
    this.loadSidebarListings();
  }

  get hasSearchQuery(): boolean {
    return this.searchQuery.trim().length > 0;
  }

  onSubmitSearch(): void {
    const query = this.searchQuery.trim();
    if (!query) {
      this.searchResults = [];
      this.hasSearched = false;
      this.searchErrorMessage = null;
      return;
    }

    this.isLoading = true;
    this.hasSearched = true;
    this.searchErrorMessage = null;

    this.listingsApi.search(query).subscribe({
      next: (results) => {
        this.searchResults = results;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to search listings:', error);
        this.searchErrorMessage = 'Failed to search listings.';
        this.searchResults = [];
        this.isLoading = false;
      },
    });
  }

  openListingInMarketplace(listingId: number): void {
    void this.router.navigate(['/main-page'], {
      queryParams: { listingId },
    });
  }

  protected override getSidebarSourceListings(): Listing[] {
    return this.listings;
  }

  private loadSidebarListings(): void {
    this.listingsApi.getMine().subscribe({
      next: (listings) => {
        this.listings = listings.filter((listing) => this.canDelete(listing));
      },
      error: (error) => {
        console.error('Failed to load sidebar listings:', error);
      },
    });
  }
}

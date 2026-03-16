import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import { HeaderComponent } from '../../components/header/header.component';
import { ListingCardComponent } from '../../components/listing-card/listing-card.component';
import { LeftNavigationComponent } from '../left-navigation/left-navigation.component';
import { ListingsSidebarActionsBase } from '../../shared/helpers/listings-sidebar-actions.base';
import { Listing } from '../../shared/models/listing.models';
import { OffersApiService } from '../../shared/services/offers-api.service';
import {
  SendOfferDialogComponent,
  SendOfferPayload,
} from '../send-offer/send-offer.component';

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
    MatSelectModule,
  ],
  templateUrl: './search-page.component.html',
  styleUrls: ['./search-page.component.scss'],
})
export class SearchPageComponent extends ListingsSidebarActionsBase implements OnInit {
  private readonly router = inject(Router);
  private readonly dialog = inject(MatDialog);
  private readonly offersApi = inject(OffersApiService);
  searchQuery = '';
  searchResults: Listing[] = [];
  isLoading = false;
  hasSearched = false;
  searchErrorMessage: string | null = null;
  offerFeedbackMessage: string | null = null;
  selectedSortOption: 'date' | 'price' | 'title' = 'date';
  sortDirection: 'asc' | 'desc' = 'asc';

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
    this.offerFeedbackMessage = null;

    this.listingsApi.search(query).subscribe({
      next: (results) => {
        this.searchResults = results;
        this.sortResults(); 
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

  openSellerProfile(sellerId: number | undefined): void {
    if (!this.canViewSellerProfile(sellerId)) {
      return;
    }

    void this.router.navigate(['/profile', sellerId]);
  }

  canViewSellerProfile(sellerId: number | undefined): boolean {
    return (
      sellerId !== undefined &&
      this.currentUserId !== null &&
      sellerId !== this.currentUserId
    );
  }

  canSendOffer(listing: Listing): boolean {
    return this.canViewSellerProfile(listing.sellerId) && !listing.isSold;
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
            this.offerFeedbackMessage = `Offer sent for ${listing.title}.`;
          },
          error: (error) => {
            console.error('Failed to send offer:', error);
            this.offerFeedbackMessage = 'Failed to send offer.';
          },
        });
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

  sortResults(): void {
    if (this.selectedSortOption === 'date') {
      this.searchResults.sort((a, b) =>
        this.sortDirection === 'asc'
          ? new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
          : new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
      );
    } else if (this.selectedSortOption === 'price') {
      this.searchResults.sort((a, b) =>
        this.sortDirection === 'asc' ? a.price - b.price : b.price - a.price,
      );
    } else if (this.selectedSortOption === 'title') {
      this.searchResults.sort((a, b) =>
        this.sortDirection === 'asc'
          ? a.title.localeCompare(b.title)
          : b.title.localeCompare(a.title),
      );
    }
  }

  changeSortType(sortType: 'date' | 'price' | 'title'): void {
    this.selectedSortOption = sortType;
    this.sortResults();
  }

  toggleSortDirection(): void {
    this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    this.sortResults();
  }
}

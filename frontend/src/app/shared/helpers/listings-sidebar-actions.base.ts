import { inject } from '@angular/core';

import { CreateListingPayload } from '../../features/create-listing/create-listing.component';
import { SidebarListing } from '../../features/left-navigation/left-navigation.component';
import { Listing } from '../models/listing.models';
import { ListingsApiService } from '../services/listings-api.service';

export abstract class ListingsSidebarActionsBase {
  protected readonly listingsApi = inject(ListingsApiService);

  listings: Listing[] = [];
  currentUserId: number | null = null;
  errorMessage: string | null = null;
  deletingIds = new Set<number>();

  get sidebarListings(): SidebarListing[] {
    return this.getSidebarSourceListings().map((listing) => ({
      id: listing.id,
      title: listing.title,
      imageUrl: listing.imageUrl,
      comments: 0,
    }));
  }

  onCreateListing(payload: CreateListingPayload): void {
    this.beforeListingMutation();

    this.listingsApi
      .create({
        title: payload.title,
        description: payload.description,
        price: payload.price,
        location: payload.location,
        imageUrl: null,
        picture: payload.picture ?? null,
      })
      .subscribe({
        next: (createdListing) => {
          this.listings = [createdListing, ...this.listings];
        },
        error: (error) => {
          console.error('Failed to create listing:', error);
          this.applyErrorMessage(this.createListingErrorMessage);
        },
      });
  }

  onDeleteListing(listingId: number): void {
    const listing = this.listings.find((item) => item.id === listingId);
    if (!listing || !this.canDelete(listing)) {
      this.applyErrorMessage(this.unauthorizedDeleteErrorMessage);
      return;
    }

    if (this.deletingIds.has(listingId)) return;

    this.beforeListingMutation();
    this.deletingIds.add(listingId);

    this.listingsApi.delete(listingId).subscribe({
      next: () => {
        this.listings = this.listings.filter((item) => item.id !== listingId);
        this.deletingIds.delete(listingId);
      },
      error: (error) => {
        console.error('Failed to delete listing:', error);
        this.applyErrorMessage(this.deleteListingErrorMessage);
        this.deletingIds.delete(listingId);
      },
    });
  }

  isDeleting(listingId: number): boolean {
    return this.deletingIds.has(listingId);
  }

  canDelete(listing: Listing): boolean {
    return (
      this.currentUserId !== null &&
      listing.sellerId !== undefined &&
      listing.sellerId === this.currentUserId
    );
  }

  protected initializeSidebarListingActions(): void {
    this.currentUserId = this.getCurrentUserIdFromToken();
  }

  protected getSidebarSourceListings(): Listing[] {
    return this.listings;
  }

  protected beforeListingMutation(): void {
    this.errorMessage = null;
  }

  protected applyErrorMessage(message: string | null): void {
    if (message !== null) {
      this.errorMessage = message;
    }
  }

  protected get createListingErrorMessage(): string | null {
    return 'Failed to create listing.';
  }

  protected get deleteListingErrorMessage(): string | null {
    return 'Failed to delete listing.';
  }

  protected get unauthorizedDeleteErrorMessage(): string | null {
    return 'You can only delete your own listings.';
  }

  private getCurrentUserIdFromToken(): number | null {
    const token = localStorage.getItem('access_token');
    if (!token) return null;

    const parts = token.split('.');
    if (parts.length < 2) return null;

    try {
      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=');
      const payload = JSON.parse(atob(padded)) as { sub?: string | number };
      const id = Number(payload.sub);
      return Number.isFinite(id) ? id : null;
    } catch {
      return null;
    }
  }
}

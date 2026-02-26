import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { HeaderComponent } from '../../components/header/header.component';
import { LeftNavigationComponent } from '../left-navigation/left-navigation.component';
import { ListingCardComponent } from '../../components/listing-card/listing-card.component';
import { Listing } from '../../shared/models/listing.models';
import { ListingComment } from '../../shared/models/comment.models';
import { ListingsSidebarActionsBase } from '../../shared/helpers/listings-sidebar-actions.base';
import { AccountsApiService } from '../../shared/services/accounts-api.service';

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
  private readonly accountsApi = inject(AccountsApiService);
  readonly maxCommentLength = 500;
  isLoading = false;
  selectedListingId: number | null = null;
  currentCommentAuthorLabel = 'You';
  private nextLocalCommentId = 1;
  private readonly commentsByListingId = new Map<number, ListingComment[]>();
  private readonly commentDrafts = new Map<number, string>();
  private readonly commentErrors = new Map<number, string>();

  ngOnInit(): void {
    this.initializeSidebarListingActions();
    this.currentCommentAuthorLabel = this.resolveCurrentCommentAuthorLabel();
    this.loadCommentAuthorLabel();
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

  protected override getCommentCountForSidebarListing(listing: Listing): number {
    return this.getComments(listing.id).length;
  }

  onListingClick(listing: Listing): void {
    if (listing.isSold) return;
    const listingId = listing.id;
    this.selectedListingId = this.selectedListingId === listingId ? null : listingId;
    this.clearCommentError(listingId);
  }

  onListingKeydown(event: KeyboardEvent, listing: Listing): void {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    this.onListingClick(listing);
  }

  isCommentPanelOpen(listingId: number): boolean {
    return this.selectedListingId === listingId;
  }

  getComments(listingId: number): ListingComment[] {
    return this.commentsByListingId.get(listingId) ?? [];
  }

  getCommentDraft(listingId: number): string {
    return this.commentDrafts.get(listingId) ?? '';
  }

  setCommentDraft(listingId: number, value: string): void {
    this.commentDrafts.set(listingId, value);
    this.clearCommentError(listingId);
  }

  getCommentError(listingId: number): string | null {
    return this.commentErrors.get(listingId) ?? null;
  }

  getRemainingCharacters(listingId: number): number {
    return this.maxCommentLength - this.getCommentDraft(listingId).length;
  }

  submitComment(listing: Listing): void {
    const draft = this.getCommentDraft(listing.id);
    const normalized = draft.trim();

    if (!this.currentUserId) {
      this.commentErrors.set(listing.id, 'You must be signed in to comment.');
      return;
    }

    if (!normalized) {
      this.commentErrors.set(listing.id, 'Comment cannot be empty.');
      return;
    }

    if (normalized.length > this.maxCommentLength) {
      this.commentErrors.set(
        listing.id,
        `Comment must be ${this.maxCommentLength} characters or fewer.`,
      );
      return;
    }

    const comments = this.getComments(listing.id);
    const newComment: ListingComment = {
      id: this.nextLocalCommentId++,
      listingId: listing.id,
      authorId: this.currentUserId,
      authorLabel: this.currentCommentAuthorLabel,
      body: normalized,
      createdAt: new Date().toISOString(),
    };

    this.commentsByListingId.set(listing.id, [...comments, newComment]);
    this.commentDrafts.set(listing.id, '');
    this.clearCommentError(listing.id);
  }

  isCommentSubmitDisabled(listingId: number): boolean {
    const draft = this.getCommentDraft(listingId);
    const normalizedLength = draft.trim().length;
    return (
      !this.currentUserId ||
      normalizedLength === 0 ||
      normalizedLength > this.maxCommentLength
    );
  }

  isListingDisabled(listing: Listing): boolean {
    return listing.isSold;
  }

  formatCommentTimestamp(value: string): string {
    return new Date(value).toLocaleString();
  }

  private clearCommentError(listingId: number): void {
    this.commentErrors.delete(listingId);
  }

  private loadCommentAuthorLabel(): void {
    this.accountsApi.getMe().subscribe({
      next: (account) => {
        const fullName = `${account.fname ?? ''} ${account.lname ?? ''}`.trim();
        if (fullName) {
          this.currentCommentAuthorLabel = fullName;
          return;
        }

        const emailPrefix = account.email?.split('@')[0]?.trim();
        if (emailPrefix) {
          this.currentCommentAuthorLabel = emailPrefix;
        }
      },
      error: () => {
        // Keep token/id fallback label.
      },
    });
  }

  private resolveCurrentCommentAuthorLabel(): string {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return this.currentUserId ? `User #${this.currentUserId}` : 'You';
    }

    const parts = token.split('.');
    if (parts.length < 2) {
      return this.currentUserId ? `User #${this.currentUserId}` : 'You';
    }

    try {
      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=');
      const payload = JSON.parse(atob(padded)) as {
        username?: string;
        preferred_username?: string;
        name?: string;
        email?: string;
      };

      const rawLabel =
        payload.username ??
        payload.preferred_username ??
        payload.name ??
        payload.email?.split('@')[0];

      const label = rawLabel?.trim();
      if (label) return label;
    } catch {
      // Fall through to id-based fallback.
    }

    return this.currentUserId ? `User #${this.currentUserId}` : 'You';
  }
}

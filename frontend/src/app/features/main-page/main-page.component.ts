import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ActivatedRoute } from '@angular/router';

import { HeaderComponent } from '../../components/header/header.component';
import { LeftNavigationComponent } from '../left-navigation/left-navigation.component';
import { ListingCardComponent } from '../../components/listing-card/listing-card.component';
import { Listing } from '../../shared/models/listing.models';
import { ListingComment } from '../../shared/models/comment.models';
import { ListingsSidebarActionsBase } from '../../shared/helpers/listings-sidebar-actions.base';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
import { CommentApiService } from '../../shared/services/comments-api.service';
@Component({
  selector: 'app-main-page',
  standalone: true,
  imports: [
    CommonModule,
    HeaderComponent,
    LeftNavigationComponent,
    ListingCardComponent,
    MatButtonModule,
    MatIconModule,
  ],
  templateUrl: './main-page.component.html',
  styleUrls: ['./main-page.component.scss'],
})
export class MainPageComponent
  extends ListingsSidebarActionsBase
  implements OnInit
{
  private readonly accountsApi = inject(AccountsApiService);
  private readonly commentsApi = inject(CommentApiService);
  readonly maxCommentLength = 500;
  isLoading = false;
  selectedListingId: number | null = null;
  highlightedListingId: number | null = null;
  currentCommentAuthorLabel = 'You';
  private nextLocalCommentId = 1;
  private pendingListingIdToFocus: number | null = null;
  private readonly commentsByListingId = new Map<number, ListingComment[]>();
  private readonly commentDrafts = new Map<number, string>();
  private readonly commentErrors = new Map<number, string>();

  ngOnInit(): void {
    this.initializeSidebarListingActions();
    const listingIdParam = this.route.snapshot.queryParamMap.get('listingId');
    const listingId = Number(listingIdParam);
    this.pendingListingIdToFocus = Number.isFinite(listingId)
      ? listingId
      : null;
    this.currentCommentAuthorLabel = this.resolveCurrentCommentAuthorLabel();
    this.loadCommentAuthorLabel();
    this.loadListings();
  }

  private loadListings(): void {
    this.isLoading = true;
    this.errorMessage = null;

    this.listingsApi.getAll().subscribe({
      next: (listings) => {
        this.listings = listings;
        this.preloadCommentsForListings(listings);
        this.isLoading = false;
        this.focusRequestedListing();
      },
      error: (error) => {
        console.error('Failed to load listings:', error);
        this.errorMessage = 'Failed to load listings.';
        this.isLoading = false;
      },
    });
  }

  private preloadCommentsForListings(listings: Listing[]): void {
    for (const listing of listings) {
      this.loadComments(listing.id);
    }
  }

  private loadComments(listingId: number): void {
    if (this.commentsByListingId.has(listingId)) return;

    this.commentsApi.getComment(listingId).subscribe({
      next: (comments) => {
        this.commentsByListingId.set(listingId, comments);
      },
      error: (err) => {
        console.error('Failed to load comments', err);
        this.commentErrors.set(listingId, 'Failed to load comments.');
      },
    });
  }

  protected override getSidebarSourceListings(): Listing[] {
    return this.listings.filter((listing) => this.canDelete(listing));
  }

  protected override getCommentCountForSidebarListing(
    listing: Listing,
  ): number {
    return this.getComments(listing.id).length;
  }

  onListingClick(listing: Listing): void {
    if (listing.isSold) return;
    const listingId = listing.id;

    const willOpen = this.selectedListingId !== listingId;
    this.selectedListingId = willOpen ? listingId : null;

    this.clearCommentError(listingId);

    if (willOpen) {
      this.loadComments(listingId);
    }
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
    const listingId = listing.id;
    const draft = this.getCommentDraft(listingId);
    const normalized = draft.trim();

    if (!this.currentUserId) {
      this.commentErrors.set(listingId, 'You must be signed in to comment.');
      return;
    }

    if (!normalized) {
      this.commentErrors.set(listingId, 'Comment cannot be empty.');
      return;
    }

    if (normalized.length > this.maxCommentLength) {
      this.commentErrors.set(
        listingId,
        `Comment must be ${this.maxCommentLength} characters or fewer.`,
      );
      return;
    }

    this.commentsApi.create({ body: normalized }, listingId).subscribe({
      next: (created) => {
        const existing = this.getComments(listingId);
        this.commentsByListingId.set(listingId, [...existing, created]);

        this.commentDrafts.set(listingId, '');
        this.clearCommentError(listingId);
      },
      error: (err) => {
        console.error('Failed to create comment', err);
        this.commentErrors.set(listingId, 'Failed to post comment.');
      },
    });
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

  private focusRequestedListing(): void {
    if (this.pendingListingIdToFocus === null) return;

    const listingId = this.pendingListingIdToFocus;
    const targetExists = this.listings.some(
      (listing) => listing.id === listingId,
    );
    if (!targetExists) {
      this.pendingListingIdToFocus = null;
      return;
    }

    this.highlightedListingId = listingId;
    this.pendingListingIdToFocus = null;

    setTimeout(() => {
      const target = document.getElementById(`listing-${listingId}`);
      target?.scrollIntoView({ behavior: 'smooth', block: 'center' });

      setTimeout(() => {
        if (this.highlightedListingId === listingId) {
          this.highlightedListingId = null;
        }
      }, 2200);
    }, 0);
  }
}

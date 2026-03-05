import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatDividerModule } from '@angular/material/divider';
import { MatButtonModule } from '@angular/material/button';
import { MatBadgeModule } from '@angular/material/badge';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { CreateListingDialogComponent, CreateListingPayload } from '../create-listing/create-listing.component';

export interface SidebarListing {
  id: number;
  title: string;
  comments?: number;
  imageUrl?: string;
}

@Component({
  selector: 'app-left-navigation',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatIconModule,
    MatListModule,
    MatDividerModule,
    MatButtonModule,
    MatBadgeModule,
    MatDialogModule, 
  ],
  templateUrl: './left-navigation.component.html',
  styleUrls: ['./left-navigation.component.scss'],
})
export class LeftNavigationComponent {
  private readonly dialog = inject(MatDialog);

  @Input() listingsCount = 0;

  @Input() listings: SidebarListing[] = [];
  @Output() createListing = new EventEmitter<CreateListingPayload>();
  @Output() deleteListing = new EventEmitter<number>();

  openCreateListing(): void {
    const ref = this.dialog.open(CreateListingDialogComponent, {
      width: '640px',
      maxWidth: '92vw',
      autoFocus: false,
    });

    ref.afterClosed().subscribe((result: CreateListingPayload | null) => {
      if (!result) return;
      this.createListing.emit(result);
    });
  }

  onDeleteListing(event: MouseEvent, listingId: number): void {
    event.stopPropagation();
    this.deleteListing.emit(listingId);
  }
}

import { Component, Input, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatDividerModule } from '@angular/material/divider';
import { MatButtonModule } from '@angular/material/button';
import { MatBadgeModule } from '@angular/material/badge';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { CreateListingDialogComponent, CreateListingPayload } from '../create-listing/create-listing.component';

type Listing = {
  title: string;
  comments: number;
  imageUrl?: string;
};

@Component({
  selector: 'left-navigation',
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

  @Input() listingsCount = 19;

  @Input() listings: Listing[] = [
    { title: 'Table', comments: 50, imageUrl: 'assets/table.png' },
    { title: 'Brand new couch', comments: 0, imageUrl: 'assets/couch.png' },
  ];

  openCreateListing(): void {
    const ref = this.dialog.open(CreateListingDialogComponent, {
      width: '640px',
      maxWidth: '92vw',
      autoFocus: false,
    });

    ref.afterClosed().subscribe((result: CreateListingPayload | null) => {
      if (!result) return;
      console.log('Create listing payload:', result);

      // Coming up
      // this.listings = [{ title: result.title, comments: 0 }, ...this.listings];
      // this.listingsCount++;
    });
  }
}
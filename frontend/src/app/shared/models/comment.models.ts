export interface ListingComment {
  id: number;
  listingId: number;
  authorId: number;
  authorLabel: string;
  body: string;
  createdAt: string;
}

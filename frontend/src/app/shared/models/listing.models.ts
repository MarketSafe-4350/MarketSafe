/**
 * Listing model representing an item listed for sale in the marketplace.
 * This model includes details about the listing such as title, description, price, and location.
 */
export interface Listing {
  id: number;
  title: string;
  description: string;
  imageUrl: string;
  price: number;
  location: string;
  createdAt: string;
  isSold: boolean;
}

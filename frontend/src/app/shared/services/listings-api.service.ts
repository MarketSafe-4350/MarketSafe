import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { Listing } from '../models/listing.models';
import { API_URLS, APP_URLS } from '../app-urls';

interface ListingApiResponse {
  id: number | null;
  seller_id: number;
  title: string;
  description: string;
  price: number;
  image_url: string | null;
  location: string | null;
  created_at: string | null;
  is_sold: boolean;
}

export interface CreateListingRequest {
  title: string;
  description: string;
  price: number;
  location: string;
  imageUrl?: string | null;
  picture?: File | null;
}

@Injectable({ providedIn: 'root' })
export class ListingsApiService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = API_URLS.listings;
  private readonly backendBaseUrl = APP_URLS.backendBaseUrl;

  getAll(): Observable<Listing[]> {
    return this.http
      .get<ListingApiResponse[]>(this.apiUrl, {
        headers: this.authHeaders(false),
      })
      .pipe(map((items) => items.map((item) => this.toListing(item))));
  }

  getMine(): Observable<Listing[]> {
    return this.http
      .get<ListingApiResponse[]>(`${this.apiUrl}/me`, {
        headers: this.authHeaders(false),
      })
      .pipe(map((items) => items.map((item) => this.toListing(item))));
  }

  create(payload: CreateListingRequest): Observable<Listing> {
    if (payload.picture) {
      const formData = new FormData();
      formData.append('title', payload.title);
      formData.append('description', payload.description);
      formData.append('price', String(payload.price));
      formData.append('location', payload.location);
      formData.append('image', payload.picture);

      return this.http
        .post<ListingApiResponse>(`${this.apiUrl}/upload`, formData, {
          headers: this.authHeaders(false),
        })
        .pipe(map((item) => this.toListing(item)));
    }

    return this.http
      .post<ListingApiResponse>(
        this.apiUrl,
        {
          title: payload.title,
          description: payload.description,
          price: payload.price,
          location: payload.location,
          image_url: payload.imageUrl ?? null,
        },
        { headers: this.authHeaders(true) }
      )
      .pipe(map((item) => this.toListing(item)));
  }

  delete(listingId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${listingId}`, {
      headers: this.authHeaders(false),
    });
  }

  private authHeaders(includeJsonContentType: boolean): HttpHeaders {
    const token = localStorage.getItem('access_token');
    const headers: Record<string, string> = {
      Accept: 'application/json',
    };

    if (includeJsonContentType) {
      headers['Content-Type'] = 'application/json';
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return new HttpHeaders(headers);
  }

  private toListing(item: ListingApiResponse): Listing {
    return {
      id: item.id ?? 0,
      sellerId: item.seller_id,
      title: item.title,
      description: item.description,
      imageUrl: this.toPublicImageUrl(item.image_url),
      price: item.price,
      location: item.location ?? 'Unknown',
      createdAt: item.created_at ?? new Date().toISOString(),
      isSold: item.is_sold,
    };
  }

  private toPublicImageUrl(imageUrl: string | null): string {
    if (!imageUrl) return '';
    if (/^https?:\/\//i.test(imageUrl)) return imageUrl;

    const normalizedPath = imageUrl.startsWith('/') ? imageUrl : `/${imageUrl}`;
    return `${this.backendBaseUrl}${normalizedPath}`;
  }
}

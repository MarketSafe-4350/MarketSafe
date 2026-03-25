import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { API_URLS } from '../app-urls';

interface RatingApiResponse {
  id?: number | null;
  listing_id: number;
  rater_id: number;
  transaction_rating: number;
}

export interface Rating {
  id: number;
  listingId: number;
  raterId: number;
  transactionRating: number;
}

@Injectable({ providedIn: 'root' })
export class RatingsApiService {
  private readonly http = inject(HttpClient);

  create(listingId: number, transactionRating: number): Observable<Rating> {
    return this.http
      .post<RatingApiResponse>(
        `${API_URLS.listings}/${listingId}/ratings`,
        { transaction_rating: transactionRating },
        { headers: this.authHeaders(true) },
      )
      .pipe(map((rating) => this.toRating(rating)));
  }

  getByListingId(listingId: number): Observable<Rating | null> {
    return this.http
      .get<RatingApiResponse | null>(`${API_URLS.listings}/${listingId}/ratings`, {
        headers: this.authHeaders(false),
      })
      .pipe(map((rating) => (rating ? this.toRating(rating) : null)));
  }

  private toRating(rating: RatingApiResponse): Rating {
    return {
      id: rating.id ?? 0,
      listingId: rating.listing_id,
      raterId: rating.rater_id,
      transactionRating: rating.transaction_rating,
    };
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
}

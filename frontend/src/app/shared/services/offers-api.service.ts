import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_URLS } from '../app-urls';

export interface CreateOfferRequest {
  listingId: number;
  offeredPrice: number;
  locationOffered: string;
}

interface CreateOfferApiRequest {
  listing_id: number;
  offered_price: number;
  location_offered: string;
  accepted: boolean;
}

@Injectable({ providedIn: 'root' })
export class OffersApiService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = API_URLS.offers;

  create(payload: CreateOfferRequest): Observable<unknown> {
    const body: CreateOfferApiRequest = {
      listing_id: payload.listingId,
      offered_price: payload.offeredPrice,
      location_offered: payload.locationOffered,
      accepted: false,
    };

    return this.http.post(this.apiUrl, body, {
      headers: this.authHeaders(),
    });
  }

  private authHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    const headers: Record<string, string> = {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return new HttpHeaders(headers);
  }
}

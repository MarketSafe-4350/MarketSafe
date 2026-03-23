import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { API_URLS } from '../app-urls';

export interface CreateOfferRequest {
  listingId: number;
  offeredPrice: number;
  locationOffered: string;
}

interface CreateOfferApiRequest {
  offered_price: number;
  location_offered: string;
}

interface OfferApiResponse {
  id?: number | null;
  listing_id: number;
  sender_id: number;
  offered_price: number;
  location_offered?: string | null;
  seen: boolean;
  accepted?: boolean | null;
  created_date?: string | null;
}

export interface Offer {
  id: number;
  listingId: number;
  senderId: number;
  offeredPrice: number;
  locationOffered: string | null;
  seen: boolean;
  accepted: boolean | null;
  createdDate: string | null;
}

@Injectable({ providedIn: 'root' })
export class OffersApiService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = API_URLS.offers;

  create(payload: CreateOfferRequest): Observable<unknown> {
    const body: CreateOfferApiRequest = {
      offered_price: payload.offeredPrice,
      location_offered: payload.locationOffered,
    };

    return this.http.post(
      `${API_URLS.listings}/${payload.listingId}/offer`,
      body,
      {
        headers: this.authHeaders(),
      },
    );
  }

  getReceived(): Observable<Offer[]> {
    return this.http
      .get<OfferApiResponse[]>(`${API_URLS.accounts}/offers/received`, {
        headers: this.authHeaders(),
      })
      .pipe(map((offers) => offers.map((offer) => this.toOffer(offer))));
  }

  getSent(): Observable<Offer[]> {
    return this.http
      .get<OfferApiResponse[]>(`${API_URLS.accounts}/offers/sent`, {
        headers: this.authHeaders(),
      })
      .pipe(map((offers) => offers.map((offer) => this.toOffer(offer))));
  }

  getReceivedUnseen(): Observable<Offer[]> {
    return this.http
      .get<OfferApiResponse[]>(`${API_URLS.accounts}/offers/received/unseen`, {
        headers: this.authHeaders(),
      })
      .pipe(map((offers) => offers.map((offer) => this.toOffer(offer))));
  }

  markSeen(offerId: number): Observable<unknown> {
    return this.http.patch(`${this.apiUrl}/${offerId}/seen`, null, {
      headers: this.authHeaders(),
    });
  }

  resolve(offerId: number, accepted: boolean): Observable<unknown> {
    return this.http.post(`${this.apiUrl}/${offerId}/resolve`, null, {
      headers: this.authHeaders(),
      params: { accepted },
    });
  }

  private toOffer(offer: OfferApiResponse): Offer {
    return {
      id: offer.id ?? 0,
      listingId: offer.listing_id,
      senderId: offer.sender_id,
      offeredPrice: offer.offered_price,
      locationOffered: offer.location_offered ?? null,
      seen: offer.seen,
      accepted: offer.accepted ?? null,
      createdDate: offer.created_date ?? null,
    };
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

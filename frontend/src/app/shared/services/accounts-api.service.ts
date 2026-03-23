import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { Account } from '../models/account.models';
import { API_URLS } from '../app-urls';

interface AccountApiResponse {
  id?: number | null;
  email: string;
  fname: string;
  lname: string;
  verified?: boolean;
  average_rating_received?: number | null;
  sum_of_ratings_received?: number | null;
}

@Injectable({ providedIn: 'root' })
export class AccountsApiService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = API_URLS.accounts;

  getMe(): Observable<Account> {
    return this.http
      .get<AccountApiResponse>(`${this.apiUrl}/me`, {
        headers: this.authHeaders(),
      })
      .pipe(map((account) => this.toAccount(account)));
  }

  getById(accountId: number): Observable<Account> {
    return this.http
      .get<AccountApiResponse>(`${this.apiUrl}/id/${accountId}`, {
        headers: this.authHeaders(),
      })
      .pipe(map((account) => this.toAccount(account)));
  }

  private authHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    const headers: Record<string, string> = {
      Accept: 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return new HttpHeaders(headers);
  }

  private toAccount(account: AccountApiResponse): Account {
    const ratingAvg = account.average_rating_received ?? 0;
    const ratingSum = account.sum_of_ratings_received ?? 0;

    return {
      id: account.id ?? 0,
      email: account.email,
      fname: account.fname,
      lname: account.lname,
      verified: account.verified ?? false,
      ratingAvg,
      ratingSum,
      ratingCount: this.toRatingCount(ratingAvg, ratingSum),
    };
  }

  private toRatingCount(ratingAvg: number, ratingSum: number): number {
    if (ratingAvg <= 0 || ratingSum <= 0) {
      return 0;
    }

    return Math.max(0, Math.round(ratingSum / ratingAvg));
  }
}

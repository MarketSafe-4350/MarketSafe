import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { Account } from '../models/account.models';
import { API_URLS } from '../app-urls';

interface AccountMeResponse {
  email: string;
  fname: string;
  lname: string;
}

@Injectable({ providedIn: 'root' })
export class AccountsApiService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = API_URLS.accounts;

  getMe(): Observable<Account> {
    return this.http
      .get<AccountMeResponse>(`${this.apiUrl}/me`, {
        headers: this.authHeaders(),
      })
      .pipe(
        map((account) => ({
          id: 0,
          email: account.email,
          fname: account.fname,
          lname: account.lname,
          verified: false,
        }))
      );
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
}

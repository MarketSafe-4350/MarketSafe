import { HttpClient, HttpHeaders } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { API_URLS } from '../app-urls';
import { map, Observable } from 'rxjs';
import { ListingComment } from '../models/comment.models';

interface CommentApiResponse {
  id: number | null;
  listing_id: number;
  author_id: number;
  author_name: string;
  body: string;
  created_date: string | null;
}

export interface CreateCommentRequest {
  body: string;
}

@Injectable({ providedIn: 'root' })
export class CommentApiService {
  private readonly http = inject(HttpClient);
  private readonly listingApiUrl = API_URLS.listings;

  getComment(listingId: number): Observable<ListingComment[]> {
    return this.http
      .get<CommentApiResponse[]>(
        `${this.listingApiUrl}/${listingId}/comments`,
        {
          headers: this.authHeaders(false),
        },
      )
      .pipe(map((items) => items.map((item) => this.toComment(item))));
  }

  create(
    payload: CreateCommentRequest,
    listingId: number,
  ): Observable<ListingComment> {
    return this.http
      .post<CommentApiResponse>(
        `${this.listingApiUrl}/${listingId}/comments`,
        {
          body: payload.body,
        },
        { headers: this.authHeaders(true) },
      )
      .pipe(map((item) => this.toComment(item)));
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

  private toComment(item: CommentApiResponse): ListingComment {
    return {
      id: item.id ?? 0,
      listingId: item.listing_id,
      authorId: item.author_id,
      authorLabel: item.author_name,
      body: item.body,
      createdAt: item.created_date ?? new Date().toISOString(),
    };
  }
}

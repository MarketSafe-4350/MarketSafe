import { TestBed } from '@angular/core/testing';
import {
  HttpClientTestingModule,
  HttpTestingController,
} from '@angular/common/http/testing';

import { AccountsApiService } from './accounts-api.service';
import { Account } from '../models/account.models';

describe('AccountsApiService', () => {
  let service: AccountsApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [AccountsApiService],
    });

    service = TestBed.inject(AccountsApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('getMe_ShouldMapRatingAverageAndDerivedRatingCount', () => {
    let result: Account | undefined;

    service.getMe().subscribe((account) => {
      result = account;
    });

    const req = httpMock.expectOne('http://localhost:8000/accounts/me');
    expect(req.request.method).toBe('GET');

    req.flush({
      id: 7,
      email: 'seller@umanitoba.ca',
      fname: 'Seller',
      lname: 'User',
      verified: true,
      average_rating_received: 4,
      sum_of_ratings_received: 20,
      rating_count: 5,
    });

    expect(result).toEqual({
      id: 7,
      email: 'seller@umanitoba.ca',
      fname: 'Seller',
      lname: 'User',
      verified: true,
      ratingAvg: 4,
      ratingSum: 20,
      ratingCount: 5,
    });
  });

  it('getById_ShouldRequestSellerAccountById', () => {
    let result: Account | undefined;

    service.getById(42).subscribe((account) => {
      result = account;
    });

    const req = httpMock.expectOne('http://localhost:8000/accounts/id/42');
    expect(req.request.method).toBe('GET');

    req.flush({
      id: 42,
      email: 'seller2@umanitoba.ca',
      fname: 'Taylor',
      lname: 'Smith',
      average_rating_received: null,
      sum_of_ratings_received: 0,
    });

    expect(result?.id).toBe(42);
    expect(result?.ratingAvg).toBe(0);
    expect(result?.ratingSum).toBe(0);
    expect(result?.ratingCount).toBe(0);
  });
});

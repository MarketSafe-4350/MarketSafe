import { TestBed } from '@angular/core/testing';
import {
  HttpClientTestingModule,
  HttpTestingController,
} from '@angular/common/http/testing';

import { RatingsApiService, Rating } from './ratings-api.service';

describe('RatingsApiService', () => {
  let service: RatingsApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [RatingsApiService],
    });

    service = TestBed.inject(RatingsApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('create_ShouldPostTransactionRatingAndMapResponse', () => {
    let result: Rating | undefined;

    service.create(15, 4).subscribe((rating) => {
      result = rating;
    });

    const req = httpMock.expectOne('http://localhost:8000/listings/15/ratings');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ transaction_rating: 4 });

    req.flush({
      id: 8,
      listing_id: 15,
      rater_id: 3,
      transaction_rating: 4,
    });

    expect(result).toEqual({
      id: 8,
      listingId: 15,
      raterId: 3,
      transactionRating: 4,
    });
  });

  it('getByListingId_ShouldReturnNullWhenListingHasNoRating', () => {
    let result: Rating | null | undefined;

    service.getByListingId(22).subscribe((rating) => {
      result = rating;
    });

    const req = httpMock.expectOne('http://localhost:8000/listings/22/ratings');
    expect(req.request.method).toBe('GET');
    req.flush(null);

    expect(result).toBeNull();
  });
});

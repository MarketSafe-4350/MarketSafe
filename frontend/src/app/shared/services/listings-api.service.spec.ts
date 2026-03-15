import { TestBed } from '@angular/core/testing';
import {
  HttpClientTestingModule,
  HttpTestingController,
} from '@angular/common/http/testing';

import { ListingsApiService } from './listings-api.service';
import { Listing } from '../models/listing.models';

describe('ListingsApiService', () => {
  let service: ListingsApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ListingsApiService],
    });

    service = TestBed.inject(ListingsApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('getAll_ShouldMapRelativeUploadImageUrlToBackendHost', () => {
    let result: Listing[] = [];

    service.getAll().subscribe((listings) => {
      result = listings;
    });

    const req = httpMock.expectOne('http://localhost:8000/listings');
    expect(req.request.method).toBe('GET');
    req.flush([
      {
        id: 1,
        seller_id: 5,
        title: 'Desk',
        description: 'Wood desk',
        price: 25,
        image_url: '/uploads/listings/test.jpg',
        location: 'Winnipeg',
        created_at: '2026-02-24T12:00:00Z',
        is_sold: false,
      },
    ]);

    expect(result.length).toBe(1);
    expect(result[0].imageUrl).toBe('http://localhost:8000/uploads/listings/test.jpg');
  });

  it('getAll_ShouldPreserveAbsoluteImageUrl', () => {
    let result: Listing[] = [];

    service.getAll().subscribe((listings) => {
      result = listings;
    });

    const req = httpMock.expectOne('http://localhost:8000/listings');
    req.flush([
      {
        id: 2,
        seller_id: 7,
        title: 'Lamp',
        description: 'Desk lamp',
        price: 10,
        image_url: 'https://cdn.example.com/lamp.png',
        location: 'Winnipeg',
        created_at: '2026-02-24T12:00:00Z',
        is_sold: false,
      },
    ]);

    expect(result[0].imageUrl).toBe('https://cdn.example.com/lamp.png');
  });

  it('create_WithPicture_ShouldPostToUploadEndpoint', () => {
    const file = new File(['img'], 'photo.png', { type: 'image/png' });

    service
      .create({
        title: 'Chair',
        description: 'Nice chair',
        price: 20,
        location: 'Campus',
        picture: file,
      })
      .subscribe();

    const req = httpMock.expectOne('http://localhost:8000/listings/upload');
    expect(req.request.method).toBe('POST');
    expect(req.request.body instanceof FormData).toBeTrue();

    req.flush({
      id: 10,
      seller_id: 1,
      title: 'Chair',
      description: 'Nice chair',
      price: 20,
      image_url: '/uploads/listings/photo.png',
      location: 'Campus',
      created_at: '2026-02-24T12:00:00Z',
      is_sold: false,
    });
  });

  it('create_WithoutPicture_ShouldPostJsonToListingsEndpoint', () => {
    service
      .create({
        title: 'Book',
        description: 'Textbook',
        price: 15,
        location: 'UofM',
      })
      .subscribe();

    const req = httpMock.expectOne('http://localhost:8000/listings');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      title: 'Book',
      description: 'Textbook',
      price: 15,
      location: 'UofM',
      image_url: null,
    });

    req.flush({
      id: 11,
      seller_id: 1,
      title: 'Book',
      description: 'Textbook',
      price: 15,
      image_url: null,
      location: 'UofM',
      created_at: '2026-02-24T12:00:00Z',
      is_sold: false,
    });
  });

  it('search_ShouldSendQueryParamAndMapResults', () => {
    let result: Listing[] = [];

    service.search('gaming laptop').subscribe((listings) => {
      result = listings;
    });

    const req = httpMock.expectOne(
      (request) =>
        request.url === 'http://localhost:8000/listings/search' &&
        request.params.get('q') === 'gaming laptop'
    );

    expect(req.request.method).toBe('GET');

    req.flush([
      {
        id: 42,
        seller_id: 9,
        title: 'Gaming Laptop',
        description: 'RTX 4060',
        price: 900,
        image_url: null,
        location: 'Winnipeg',
        created_at: '2026-02-25T12:00:00Z',
        is_sold: false,
      },
    ]);

    expect(result.length).toBe(1);
    expect(result[0].title).toBe('Gaming Laptop');
  });

  it('getBySeller_ShouldFetchSellerListings', () => {
    let result: Listing[] = [];

    service.getBySeller(9).subscribe((listings) => {
      result = listings;
    });

    const req = httpMock.expectOne('http://localhost:8000/listings/seller/9');
    expect(req.request.method).toBe('GET');

    req.flush([
      {
        id: 100,
        seller_id: 9,
        title: 'Monitor',
        description: '27 inch',
        price: 120,
        image_url: null,
        location: 'Winnipeg',
        created_at: '2026-02-25T12:00:00Z',
        is_sold: false,
      },
    ]);

    expect(result.length).toBe(1);
    expect(result[0].sellerId).toBe(9);
  });
});

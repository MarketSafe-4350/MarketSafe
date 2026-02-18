import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ProfilePageComponent } from './profile.page';
import {
  HttpClientTestingModule,
  HttpTestingController,
} from '@angular/common/http/testing';

import { Account } from '../../shared/models/account.models';
import { Listing } from '../../shared/models/listing.models';

describe('ProfilePageComponent', () => {
  let profilePageComponent: ProfilePageComponent;
  let fixture: ComponentFixture<ProfilePageComponent>;
  let httpMock: HttpTestingController;

  const mockAccount: Account = {
    id: 1,
    email: 'test@myumanitoba.ca',
    fname: 'First',
    lname: 'Last',
    verified: true,
    ratingAvg: 4.5,
    ratingCount: 271,
  };

  const mockListings: Listing[] = [
    {
      id: 101,
      title: 'Calculus Textbook',
      description: 'Good condition.',
      imageUrl: 'assets/images/computer.png',
      price: 45,
      location: 'University of Manitoba',
      createdAt: new Date('2025-12-31').toISOString(),
      isSold: false,
    },
    {
      id: 102,
      title: 'Dell Monitor',
      description: 'Works perfectly.',
      imageUrl: 'assets/images/computer.png',
      price: 120,
      location: 'Fort Garry',
      createdAt: new Date('2026-01-01').toISOString(),
      isSold: true,
    },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProfilePageComponent, HttpClientTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(ProfilePageComponent);
    profilePageComponent = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    expect(profilePageComponent).toBeTruthy();
  });

  it('ngOnInit_ShouldLoadProfileAndSetAccountAndListings', () => {
    fixture.detectChanges();

    const accountReq = httpMock.expectOne('assets/mocks/profile-mock.json');
    expect(accountReq.request.method).toBe('GET');
    accountReq.flush(mockAccount);

    const listingsReq = httpMock.expectOne('assets/mocks/listing-mock.json');
    expect(listingsReq.request.method).toBe('GET');
    listingsReq.flush(mockListings);

    expect(profilePageComponent.account).toEqual(mockAccount);
    expect(profilePageComponent.listings).toEqual(mockListings);
    expect(profilePageComponent.errorMessage).toBeNull();

    expect(profilePageComponent.fullName).toBe('First Last');
    expect(profilePageComponent.isVerified).toBeTrue();
    expect(profilePageComponent.ratingAvg).toBe(4.5);
    expect(profilePageComponent.ratingCount).toBe(271);
  });
});

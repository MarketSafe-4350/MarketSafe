import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { RouterTestingModule } from '@angular/router/testing';
import { ProfilePageComponent } from './profile.page';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
import { ListingsApiService } from '../../shared/services/listings-api.service';

import { Account } from '../../shared/models/account.models';
import { Listing } from '../../shared/models/listing.models';

describe('ProfilePageComponent', () => {
  let profilePageComponent: ProfilePageComponent;
  let fixture: ComponentFixture<ProfilePageComponent>;
  let accountsApiSpy: jasmine.SpyObj<AccountsApiService>;
  let listingsApiSpy: jasmine.SpyObj<ListingsApiService>;

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
      sellerId: 1,
      title: 'Calculus Textbook',
      description: 'Good condition.',
      imageUrl: 'assets/images/computer.png',
      price: 45,
      location: 'University of Manitoba',
      createdAt: new Date('2025-12-31').toISOString(),
      isSold: false,
    },
  ];

  beforeEach(async () => {
    accountsApiSpy = jasmine.createSpyObj<AccountsApiService>('AccountsApiService', ['getMe']);
    accountsApiSpy.getMe.and.returnValue(of(mockAccount));
    listingsApiSpy = jasmine.createSpyObj<ListingsApiService>('ListingsApiService', [
      'getMine',
      'create',
      'delete',
    ]);
    listingsApiSpy.getMine.and.returnValue(of(mockListings));

    await TestBed.configureTestingModule({
      imports: [ProfilePageComponent, RouterTestingModule],
      providers: [
        { provide: AccountsApiService, useValue: accountsApiSpy },
        { provide: ListingsApiService, useValue: listingsApiSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ProfilePageComponent);
    profilePageComponent = fixture.componentInstance;
  });

  it('should create', () => {
    expect(profilePageComponent).toBeTruthy();
  });

  it('ngOnInit_ShouldLoadProfileAndSetAccount', () => {
    fixture.detectChanges();

    expect(profilePageComponent.account).toEqual(mockAccount);
    expect(profilePageComponent.listings).toEqual(mockListings);
    expect(profilePageComponent.errorMessage).toBeNull();

    expect(profilePageComponent.fullName).toBe('First Last');
    expect(profilePageComponent.firstName).toBe('First');
    expect(profilePageComponent.lastName).toBe('Last');
    expect(profilePageComponent.isVerified).toBeTrue();
    expect(profilePageComponent.ratingAvg).toBe(4.5);
    expect(profilePageComponent.ratingCount).toBe(271);
  });

  it('template_ShouldRenderLeftNavigationSidebar', () => {
    fixture.detectChanges();

    const sidebar = fixture.nativeElement.querySelector('app-left-navigation');
    expect(sidebar).toBeTruthy();
  });

  it('sidebarListings_ShouldReflectLoadedMyListings', () => {
    fixture.detectChanges();

    expect(profilePageComponent.sidebarListings.length).toBe(1);
    expect(profilePageComponent.sidebarListings[0].title).toBe('Calculus Textbook');
  });
});

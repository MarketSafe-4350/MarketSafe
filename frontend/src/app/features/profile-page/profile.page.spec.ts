import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Observable, of } from 'rxjs';
import { RouterTestingModule } from '@angular/router/testing';
import { ActivatedRoute, ParamMap, convertToParamMap } from '@angular/router';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { ProfilePageComponent } from './profile.page';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
import { ListingsApiService } from '../../shared/services/listings-api.service';
import { Offer, OffersApiService } from '../../shared/services/offers-api.service';

import { Account } from '../../shared/models/account.models';
import { Listing } from '../../shared/models/listing.models';
import { SendOfferDialogComponent } from '../send-offer/send-offer.component';

describe('ProfilePageComponent', () => {
  let profilePageComponent: ProfilePageComponent;
  let fixture: ComponentFixture<ProfilePageComponent>;
  let accountsApiSpy: jasmine.SpyObj<AccountsApiService>;
  let listingsApiSpy: jasmine.SpyObj<ListingsApiService>;
  let offersApiSpy: jasmine.SpyObj<OffersApiService>;
  let matDialogSpy: jasmine.SpyObj<MatDialog>;
  let dialogRefSpy: jasmine.SpyObj<MatDialogRef<SendOfferDialogComponent>>;
  let activatedRouteStub: {
    paramMap: Observable<ParamMap>;
  };

  const mockAccount: Account = {
    id: 1,
    email: 'test@myumanitoba.ca',
    fname: 'First',
    lname: 'Last',
    verified: true,
    ratingAvg: 4.5,
    ratingCount: 271,
    ratingSum: 1220,
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
    localStorage.clear();
    const payload = btoa(JSON.stringify({ sub: '123' }));
    localStorage.setItem('access_token', `x.${payload}.y`);

    accountsApiSpy = jasmine.createSpyObj<AccountsApiService>('AccountsApiService', [
      'getMe',
      'getById',
    ]);
    accountsApiSpy.getMe.and.returnValue(of(mockAccount));
    accountsApiSpy.getById.and.returnValue(of(mockAccount));
    listingsApiSpy = jasmine.createSpyObj<ListingsApiService>('ListingsApiService', [
      'getMine',
      'getAll',
      'getBySeller',
      'create',
      'delete',
    ]);
    listingsApiSpy.getMine.and.returnValue(of(mockListings));
    listingsApiSpy.getAll.and.returnValue(of(mockListings));
    listingsApiSpy.getBySeller.and.returnValue(of(mockListings));
    offersApiSpy = jasmine.createSpyObj<OffersApiService>('OffersApiService', [
      'create',
      'getSent',
      'getReceived',
      'getReceivedUnseen',
      'markSeen',
    ]);
    offersApiSpy.create.and.returnValue(of({}));
    offersApiSpy.getSent.and.returnValue(of([]));
    offersApiSpy.getReceived.and.returnValue(of([]));
    offersApiSpy.getReceivedUnseen.and.returnValue(of([]));
    offersApiSpy.markSeen.and.returnValue(of({}));
    matDialogSpy = jasmine.createSpyObj<MatDialog>('MatDialog', ['open']);
    dialogRefSpy = jasmine.createSpyObj<MatDialogRef<SendOfferDialogComponent>>(
      'MatDialogRef',
      ['afterClosed'],
    );
    dialogRefSpy.afterClosed.and.returnValue(of(null));
    matDialogSpy.open.and.returnValue(dialogRefSpy);
    activatedRouteStub = {
      paramMap: of(convertToParamMap({})),
    };

    await TestBed.configureTestingModule({
      imports: [ProfilePageComponent, RouterTestingModule],
      providers: [
        { provide: AccountsApiService, useValue: accountsApiSpy },
        { provide: ListingsApiService, useValue: listingsApiSpy },
        { provide: OffersApiService, useValue: offersApiSpy },
        { provide: MatDialog, useValue: matDialogSpy },
        { provide: ActivatedRoute, useValue: activatedRouteStub },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ProfilePageComponent);
    profilePageComponent = fixture.componentInstance;
  });

  afterEach(() => {
    localStorage.clear();
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

  it('sellerRoute_ShouldLoadSellerAccountAndListings', () => {
    activatedRouteStub.paramMap = of(convertToParamMap({ sellerId: '9' }));

    fixture = TestBed.createComponent(ProfilePageComponent);
    profilePageComponent = fixture.componentInstance;
    fixture.detectChanges();

    expect(accountsApiSpy.getById).toHaveBeenCalledWith(9);
    expect(listingsApiSpy.getBySeller).toHaveBeenCalledWith(9);
    expect(listingsApiSpy.getMine).toHaveBeenCalled();
    expect(profilePageComponent.pageTitle).toBe('Seller Profile');
    expect(profilePageComponent.listingsTitle).toBe('Seller Listings');
  });

  it('ownSellerRoute_ShouldFallBackToRegularProfile', () => {
    localStorage.clear();
    const payload = btoa(JSON.stringify({ sub: '9' }));
    localStorage.setItem('access_token', `x.${payload}.y`);
    activatedRouteStub.paramMap = of(convertToParamMap({ sellerId: '9' }));

    fixture = TestBed.createComponent(ProfilePageComponent);
    profilePageComponent = fixture.componentInstance;
    fixture.detectChanges();

    expect(accountsApiSpy.getById).not.toHaveBeenCalled();
    expect(listingsApiSpy.getBySeller).not.toHaveBeenCalled();
    expect(accountsApiSpy.getMe).toHaveBeenCalled();
    expect(profilePageComponent.pageTitle).toBe('My Profile');
  });

  it('canSendOffer_ShouldOnlyBeTrueOnOtherSellerProfile', () => {
    activatedRouteStub.paramMap = of(convertToParamMap({ sellerId: '9' }));

    fixture = TestBed.createComponent(ProfilePageComponent);
    profilePageComponent = fixture.componentInstance;
    fixture.detectChanges();

    expect(profilePageComponent.canSendOffer(mockListings[0])).toBeTrue();
    expect(
      profilePageComponent.canSendOffer({ ...mockListings[0], sellerId: 123 }),
    ).toBeFalse();
    expect(
      profilePageComponent.canSendOffer({ ...mockListings[0], isSold: true }),
    ).toBeFalse();
  });

  it('canSendOffer_DeclinedSentOffer_ShouldStillBeTrue', () => {
    const declinedOffer: Offer = {
      id: 33,
      listingId: mockListings[0].id,
      senderId: 123,
      offeredPrice: 40,
      locationOffered: 'Campus',
      seen: true,
      accepted: false,
      createdDate: new Date().toISOString(),
    };
    offersApiSpy.getSent.and.returnValue(of([declinedOffer]));
    activatedRouteStub.paramMap = of(convertToParamMap({ sellerId: '9' }));

    fixture = TestBed.createComponent(ProfilePageComponent);
    profilePageComponent = fixture.componentInstance;
    fixture.detectChanges();

    expect(profilePageComponent.canSendOffer(mockListings[0])).toBeTrue();
    expect(profilePageComponent.getOfferButtonLabel(mockListings[0].id)).toBe(
      'Send Offer',
    );
  });
});

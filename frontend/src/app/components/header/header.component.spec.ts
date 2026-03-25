import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { HeaderComponent } from './header.component';
import { Router } from '@angular/router';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
import { ListingsApiService } from '../../shared/services/listings-api.service';
import { OffersApiService } from '../../shared/services/offers-api.service';
import { BuyerOfferNotificationsService } from '../../shared/services/buyer-offer-notifications.service';

describe('HeaderComponent', () => {
  let headerComponent: HeaderComponent;
  let fixture: ComponentFixture<HeaderComponent>;
  let routerSpy: jasmine.SpyObj<Router>;
  let accountsApiSpy: jasmine.SpyObj<AccountsApiService>;
  let listingsApiSpy: jasmine.SpyObj<ListingsApiService>;
  let offersApiSpy: jasmine.SpyObj<OffersApiService>;
  let buyerOfferNotificationsSpy: jasmine.SpyObj<BuyerOfferNotificationsService>;

  beforeEach(async () => {
    localStorage.clear();
    const payload = btoa(JSON.stringify({ sub: '7' }));
    localStorage.setItem('access_token', `x.${payload}.y`);

    routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    accountsApiSpy = jasmine.createSpyObj<AccountsApiService>('AccountsApiService', ['getMe']);
    listingsApiSpy = jasmine.createSpyObj<ListingsApiService>(
      'ListingsApiService',
      ['getMine', 'getAll'],
    );
    offersApiSpy = jasmine.createSpyObj<OffersApiService>(
      'OffersApiService',
      ['getReceived', 'getReceivedUnseen', 'getSent', 'markSeen'],
    );
    buyerOfferNotificationsSpy = jasmine.createSpyObj<BuyerOfferNotificationsService>(
      'BuyerOfferNotificationsService',
      ['syncResolvedOffers', 'markResolvedOffersSeen'],
    );
    accountsApiSpy.getMe.and.returnValue(
      of({
        id: 7,
        email: 'test@example.com',
        fname: 'Test',
        lname: 'User',
        verified: false,
      })
    );
    listingsApiSpy.getMine.and.returnValue(of([]));
    listingsApiSpy.getAll.and.returnValue(of([]));
    offersApiSpy.getReceived.and.returnValue(of([]));
    offersApiSpy.getReceivedUnseen.and.returnValue(of([]));
    offersApiSpy.getSent.and.returnValue(of([]));
    offersApiSpy.markSeen.and.returnValue(of({}));
    buyerOfferNotificationsSpy.syncResolvedOffers.and.returnValue(new Set<number>());

    await TestBed.configureTestingModule({
      imports: [HeaderComponent],
      providers: [
        provideNoopAnimations(),
        { provide: Router, useValue: routerSpy },
        { provide: AccountsApiService, useValue: accountsApiSpy },
        { provide: ListingsApiService, useValue: listingsApiSpy },
        { provide: OffersApiService, useValue: offersApiSpy },
        { provide: BuyerOfferNotificationsService, useValue: buyerOfferNotificationsSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HeaderComponent);
    headerComponent = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(headerComponent).toBeTruthy();
  });

  it('should load display name from account api', () => {
    expect(headerComponent.displayName()).toBe('Test User');
  });

  describe('Navigation behaviour', () => {
    it('onLogout_ShouldNavigateToRoot', () => {
      headerComponent.onLogout();
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/']);
    });

    it('goToProfile_ShouldNavigateToProfile', () => {
      headerComponent.goToProfile();
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/profile']);
    });
    
    it('onLogout_ShouldRemoveAccessToken', () => {
      localStorage.setItem('access_token', 'fakeToken');
      headerComponent.onLogout();
      expect(localStorage.getItem('access_token')).toBeNull();
    });
  });

  it('ngOnInit_ShouldCombineSellerAndBuyerUnreadCounts', () => {
    offersApiSpy.getReceivedUnseen.and.returnValue(
      of([
        {
          id: 1,
          listingId: 10,
          senderId: 50,
          offeredPrice: 20,
          locationOffered: 'Campus',
          seen: false,
          accepted: null,
          createdDate: '2026-03-24T12:00:00Z',
        },
      ]),
    );
    buyerOfferNotificationsSpy.syncResolvedOffers.and.returnValue(new Set([99]));

    fixture = TestBed.createComponent(HeaderComponent);
    headerComponent = fixture.componentInstance;
    fixture.detectChanges();

    expect(headerComponent.unseenCount()).toBe(2);
    expect(buyerOfferNotificationsSpy.syncResolvedOffers).toHaveBeenCalledWith([], 7);
  });

  it('onNotificationsOpened_ShouldMarkBuyerResolutionsSeen', () => {
    buyerOfferNotificationsSpy.syncResolvedOffers.and.returnValue(new Set([5]));
    offersApiSpy.getSent.and.returnValue(
      of([
        {
          id: 5,
          listingId: 3,
          senderId: 7,
          offeredPrice: 30,
          locationOffered: 'Campus',
          seen: true,
          accepted: true,
          createdDate: '2026-03-24T12:00:00Z',
        },
      ]),
    );

    fixture = TestBed.createComponent(HeaderComponent);
    headerComponent = fixture.componentInstance;
    fixture.detectChanges();

    headerComponent.onNotificationsOpened();

    expect(buyerOfferNotificationsSpy.markResolvedOffersSeen).toHaveBeenCalledWith([5], 7);
  });
});

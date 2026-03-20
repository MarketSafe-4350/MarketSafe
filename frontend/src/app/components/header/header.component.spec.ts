import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { HeaderComponent } from './header.component';
import { Router } from '@angular/router';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
import { ListingsApiService } from '../../shared/services/listings-api.service';
import { OffersApiService } from '../../shared/services/offers-api.service';
describe('HeaderComponent', () => {
  let headerComponent: HeaderComponent;
  let fixture: ComponentFixture<HeaderComponent>;
  let routerSpy: jasmine.SpyObj<Router>;
  let accountsApiSpy: jasmine.SpyObj<AccountsApiService>;
  let listingsApiSpy: jasmine.SpyObj<ListingsApiService>;
  let offersApiSpy: jasmine.SpyObj<OffersApiService>;

  beforeEach(async () => {
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    accountsApiSpy = jasmine.createSpyObj<AccountsApiService>('AccountsApiService', ['getMe']);
    listingsApiSpy = jasmine.createSpyObj<ListingsApiService>(
      'ListingsApiService',
      ['getMine'],
    );
    offersApiSpy = jasmine.createSpyObj<OffersApiService>(
      'OffersApiService',
      ['getReceived', 'getReceivedUnseen', 'markSeen'],
    );
    accountsApiSpy.getMe.and.returnValue(
      of({
        id: 0,
        email: 'test@example.com',
        fname: 'Test',
        lname: 'User',
        verified: false,
      })
    );
    listingsApiSpy.getMine.and.returnValue(of([]));
    offersApiSpy.getReceived.and.returnValue(of([]));
    offersApiSpy.getReceivedUnseen.and.returnValue(of([]));
    offersApiSpy.markSeen.and.returnValue(of({}));

    await TestBed.configureTestingModule({
      imports: [HeaderComponent],
      providers: [
        provideNoopAnimations(),
        { provide: Router, useValue: routerSpy },
        { provide: AccountsApiService, useValue: accountsApiSpy },
        { provide: ListingsApiService, useValue: listingsApiSpy },
        { provide: OffersApiService, useValue: offersApiSpy },
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
});

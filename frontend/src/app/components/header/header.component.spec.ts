import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { HeaderComponent } from './header.component';
import { Router } from '@angular/router';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
describe('HeaderComponent', () => {
  let headerComponent: HeaderComponent;
  let fixture: ComponentFixture<HeaderComponent>;
  let routerSpy: jasmine.SpyObj<Router>;
  let accountsApiSpy: jasmine.SpyObj<AccountsApiService>;

  beforeEach(async () => {
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    accountsApiSpy = jasmine.createSpyObj<AccountsApiService>('AccountsApiService', ['getMe']);
    accountsApiSpy.getMe.and.returnValue(
      of({
        id: 0,
        email: 'test@example.com',
        fname: 'Test',
        lname: 'User',
        verified: false,
      })
    );

    await TestBed.configureTestingModule({
      imports: [HeaderComponent],
      providers: [
        provideNoopAnimations(),
        { provide: Router, useValue: routerSpy },
        { provide: AccountsApiService, useValue: accountsApiSpy },
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
  });
});

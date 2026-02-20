import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { VerifyEmailComponent } from './verify-email.component';
import { BehaviorSubject } from 'rxjs';

describe('VerifyEmailComponent', () => {
  let component: VerifyEmailComponent;
  let fixture: ComponentFixture<VerifyEmailComponent>;
  let httpMock: HttpTestingController;
  let routerMock: jasmine.SpyObj<Router>;
  let activatedRouteMock: { queryParams: BehaviorSubject<Record<string, string>> };

  beforeEach(async () => {
    routerMock = jasmine.createSpyObj('Router', ['navigate']);
    activatedRouteMock = {
      queryParams: new BehaviorSubject<Record<string, string>>({ token: 'test-token-123' }),
    };

    await TestBed.configureTestingModule({
      imports: [VerifyEmailComponent, HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: routerMock },
        { provide: ActivatedRoute, useValue: activatedRouteMock },
      ],
    }).compileComponents();

    httpMock = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(VerifyEmailComponent);
    component = fixture.componentInstance;
    // Prevent automatic verifyEmail() execution during fixture.detectChanges()
    // We'll call the original method manually in tests that need it.
    const originalVerify = component.verifyEmail.bind(component);
    spyOn(component, 'verifyEmail').and.callFake(() => {
      // Prevent auto-execution
    });
    // expose original for tests
    (component as { __origVerify?: () => void }).__origVerify = originalVerify;
  });

  afterEach(() => {
    httpMock.verify();
  });

  // -------------------------
  // Initialization Tests
  // -------------------------
  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('ngOnInit_ShouldCallVerifyEmail', () => {
    component.ngOnInit();
    expect(component.verifyEmail).toHaveBeenCalled();
  });

  // -------------------------
  // Email Verification Success Tests
  // -------------------------
  it('verifyEmail_ValidToken_ShouldSetSuccessTrue', () => {
    (component as { __origVerify?: () => void }).__origVerify?.();

    const req = httpMock.expectOne(
      req => req.url.includes('/accounts/verify-email') && req.method === 'GET'
    );

    expect(component.loading()).toBe(true);

    req.flush({
      email: 'test@umanitoba.ca',
      fname: 'John',
      lname: 'Doe',
      verified: true,
      message: 'Email verified successfully!',
    });

    expect(component.loading()).toBe(false);
    expect(component.success()).toBe(true);
    expect(component.errorMessage()).toBeNull();
  });

  it('verifyEmail_SuccessResponse_ShouldRedirectToLoginAfterDelay', fakeAsync(() => {
    (component as { __origVerify?: () => void }).__origVerify?.();

    const req = httpMock.expectOne(
      req => req.url.includes('/accounts/verify-email') && req.method === 'GET'
    );

    req.flush({
      email: 'test@umanitoba.ca',
      fname: 'John',
      lname: 'Doe',
      verified: true,
      message: 'Email verified successfully!',
    });

    expect(routerMock.navigate).not.toHaveBeenCalled();

    tick(3000);

    expect(routerMock.navigate).toHaveBeenCalledWith(['/login']);
  }));

  // -------------------------
  // Email Verification Failure Tests
  // -------------------------
  it('verifyEmail_InvalidToken_ShouldSetErrorMessage', () => {
    (component as { __origVerify?: () => void }).__origVerify?.();

    const req = httpMock.expectOne(
      req => req.url.includes('/accounts/verify-email') && req.method === 'GET'
    );

    req.flush(
      { error_message: 'Invalid or expired verification token' },
      { status: 404, statusText: 'Not Found' }
    );

    expect(component.loading()).toBe(false);
    expect(component.success()).toBe(false);
    expect(component.errorMessage()).toBe('Invalid or expired verification token');
  });

  it('verifyEmail_TokenExpired_ShouldShowExpiredMessage', () => {
    (component as { __origVerify?: () => void }).__origVerify?.();

    const req = httpMock.expectOne(
      req => req.url.includes('/accounts/verify-email') && req.method === 'GET'
    );

    req.flush(
      { error_message: 'This verification token has expired' },
      { status: 400, statusText: 'Bad Request' }
    );

    expect(component.errorMessage()).toBe('This verification token has expired');
  });

  it('verifyEmail_ErrorResponse_ShouldRedirectToSignupAfterDelay', fakeAsync(() => {
    (component as { __origVerify?: () => void }).__origVerify?.();

    const req = httpMock.expectOne(
      req => req.url.includes('/accounts/verify-email') && req.method === 'GET'
    );

    req.flush(
      { error_message: 'Verification failed' },
      { status: 400, statusText: 'Bad Request' }
    );

    expect(routerMock.navigate).not.toHaveBeenCalled();

    tick(3000);

    expect(routerMock.navigate).toHaveBeenCalledWith(['/signup']);
  }));

  it('verifyEmail_NoToken_ShouldRedirectToSignup', fakeAsync(() => {
    activatedRouteMock.queryParams = new BehaviorSubject<Record<string, string>>({});

    (component as { __origVerify?: () => void }).__origVerify?.(); // Trigger verifyEmail

    expect(component.loading()).toBe(false);
    expect(component.errorMessage()).toBe('No verification token provided.');

    tick(2000);

    expect(routerMock.navigate).toHaveBeenCalledWith(['/signup']);
  }));

  // -------------------------
  // UI State Tests
  // -------------------------
  it('loading_ShouldShowSpinner', () => {
    component.loading.set(true);
    fixture.detectChanges();
    const spinner = fixture.nativeElement.querySelector('mat-spinner');
    expect(spinner).toBeTruthy();
  });

  it('success_ShouldShowSuccessIcon', () => {
    component.loading.set(false);
    component.success.set(true);
    fixture.detectChanges();
    const successIcon = fixture.nativeElement.querySelector('.success-icon');
    expect(successIcon).toBeTruthy();
    expect(successIcon.textContent).toContain('✓');
  });

  it('error_ShouldShowErrorIcon', () => {
    component.loading.set(false);
    component.errorMessage.set('Test error');
    fixture.detectChanges();
    const errorIcon = fixture.nativeElement.querySelector('.error-icon');
    expect(errorIcon).toBeTruthy();
    expect(errorIcon.textContent).toContain('✕');
  });

  // -------------------------
  // Button Navigation Tests
  // -------------------------
  it('success_GoToLoginButton_ShouldNavigateToLogin', () => {
    component.loading.set(false);
    component.success.set(true);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button[color="primary"]');
    button.click();

    expect(routerMock.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('error_BackToSignUpButton_ShouldNavigateToSignup', () => {
    component.loading.set(false);
    component.errorMessage.set('Test error');
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button:not([color="primary"])');
    button.click();

    expect(routerMock.navigate).toHaveBeenCalledWith(['/signup']);
  });
});

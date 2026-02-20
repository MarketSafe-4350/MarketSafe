import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SignupComponent } from './signup.page';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';

describe('SignupComponent', () => {
  let fixture: ComponentFixture<SignupComponent>;
  let signupComponent: SignupComponent;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SignupComponent, HttpClientTestingModule, RouterTestingModule],
      providers: [provideNoopAnimations()],
    }).compileComponents();

    fixture = TestBed.createComponent(SignupComponent);
    signupComponent = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => {
    httpMock.verify();
  });

  // -------------------------
  // createForm() unit tests
  // -------------------------
  it('createForm_FirstNameEmpty_ShouldBeInvalid', () => {
    const control = signupComponent.form.get('firstName')!;
    control.setValue('');
    expect(control.hasError('required')).toBeTrue();
    expect(control.invalid).toBeTrue();
  });

  it('createForm_EmailWrongDomain_ShouldBeInvalid', () => {
    const control = signupComponent.form.get('email')!;
    control.setValue('test@gmail.com');
    expect(control.hasError('pattern')).toBeTrue();
    expect(control.invalid).toBeTrue();
  });

  it('createForm_EmailUniversityDomainUmanitoba_ShouldBeValid', () => {
    const control = signupComponent.form.get('email')!;
    control.setValue('abc@umanitoba.ca');
    expect(control.valid).toBeTrue();
  });

  it('createForm_EmailUniversityDomainMyumanitoba_ShouldBeValid', () => {
    const control = signupComponent.form.get('email')!;
    control.setValue('abc@myumanitoba.ca');
    expect(control.valid).toBeTrue();
  });

  it('createForm_PasswordWeak_ShouldBeInvalid', () => {
    const control = signupComponent.form.get('password')!;
    control.setValue('password');
    expect(control.hasError('pattern')).toBeTrue();
    expect(control.invalid).toBeTrue();
  });

  it('createForm_PasswordStrong_ShouldBeValid', () => {
    const control = signupComponent.form.get('password')!;
    control.setValue('Password1');
    expect(control.valid).toBeTrue();
  });

  // -------------------------
  // onSubmit() unit tests
  // -------------------------
  it('onSubmit_EmptyForm_ShouldMarkAllAsTouched', () => {
    signupComponent.form.patchValue({
      firstName: '',
      lastName: '',
      email: '',
      password: '',
    });

    spyOn(signupComponent.form, 'markAllAsTouched');
    signupComponent.onSubmit();

    expect(signupComponent.form.markAllAsTouched).toHaveBeenCalled();
  });

  it('onSubmit_FormValid_ShouldSetLoadingTrue', () => {
    signupComponent.form.setValue({
      firstName: 'TestFirst',
      lastName: 'TestLast',
      email: 'test@umanitoba.ca',
      password: 'Password1!',
    });

    signupComponent.onSubmit();

    expect(signupComponent.loading()).toBe(true);

    // flush pending request to avoid leaking open requests
    const req = httpMock.expectOne('http://localhost:8000/accounts');
    req.flush({ verification_link: 'http://localhost:4200/verify-email?token=test' });
  });

  it('onSubmit_FormValid_ShouldMakeHttpPostRequest', () => {
    signupComponent.form.setValue({
      firstName: 'TestFirst',
      lastName: 'TestLast',
      email: 'TEST@UMANITOBA.CA',
      password: 'Password1!',
    });

    signupComponent.onSubmit();

    const req = httpMock.expectOne('http://localhost:8000/accounts');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      fname: 'TestFirst',
      lname: 'TestLast',
      email: 'test@umanitoba.ca',
      password: 'Password1!',
    });

    req.flush({ verification_link: 'http://localhost:4200/verify-email?token=test-token' });
  });

  it('onSubmit_SuccessResponse_ShouldSetVerificationLink', () => {
    signupComponent.form.setValue({
      firstName: 'John',
      lastName: 'Doe',
      email: 'john@umanitoba.ca',
      password: 'Password1!',
    });

    signupComponent.onSubmit();

    const req = httpMock.expectOne('http://localhost:8000/accounts');
    const mockLink = 'http://localhost:4200/verify-email?token=abc123';
    req.flush({ verification_link: mockLink });

    expect(signupComponent.verificationLink()).toBe(mockLink);
    expect(signupComponent.loading()).toBe(false);
  });

  it('onSubmit_ErrorResponse_ShouldSetErrorMessage', () => {
    signupComponent.form.setValue({
      firstName: 'John',
      lastName: 'Doe',
      email: 'john@umanitoba.ca',
      password: 'Password1!',
    });

    signupComponent.onSubmit();

    const req = httpMock.expectOne('http://localhost:8000/accounts');
    req.flush(
      { error_message: 'Email already exists' },
      { status: 409, statusText: 'Conflict' }
    );

    expect(signupComponent.error()).toBe('Email already exists');
    expect(signupComponent.loading()).toBe(false);
  });

  it('onSubmit_BadResponse_ShouldShowDefaultError', () => {
    signupComponent.form.setValue({
      firstName: 'John',
      lastName: 'Doe',
      email: 'john@umanitoba.ca',
      password: 'Password1!',
    });

    signupComponent.onSubmit();

    const req = httpMock.expectOne('http://localhost:8000/accounts');
    req.error(new ErrorEvent('Network error'));

    expect(signupComponent.error()).toContain('Failed to create account');
    expect(signupComponent.loading()).toBe(false);
  });

  // -------------------------
  // copyToClipboard() tests
  // -------------------------
  it('copyToClipboard_ShouldCallNavigatorClipboard', () => {
    spyOn(navigator.clipboard, 'writeText').and.returnValue(Promise.resolve());
    signupComponent.copyToClipboard('test-link');
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('test-link');
  });

  // -------------------------
  // openVerificationLink() tests
  // -------------------------
  it('openVerificationLink_ShouldOpenLinkInNewWindow', () => {
    spyOn(window, 'open');
    signupComponent.verificationLink.set('http://example.com/verify?token=123');
    signupComponent.openVerificationLink();
    expect(window.open).toHaveBeenCalledWith('http://example.com/verify?token=123', '_blank');
  });

  it('openVerificationLink_NoLink_ShouldNotOpen', () => {
    spyOn(window, 'open');
    signupComponent.verificationLink.set(null);
    signupComponent.openVerificationLink();
    expect(window.open).not.toHaveBeenCalled();
  });
});

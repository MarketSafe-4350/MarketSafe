import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { Router } from '@angular/router';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { LoginComponent } from './login.component';

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let component: LoginComponent;
  let httpMock: HttpTestingController;

  const routerSpy = jasmine.createSpyObj<Router>('Router', ['navigate']);

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoginComponent, HttpClientTestingModule],
      providers: [provideNoopAnimations(), { provide: Router, useValue: routerSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);

    routerSpy.navigate.calls.reset();
    localStorage.clear();

    fixture.detectChanges();
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('onSubmit_InvalidForm_ShouldNotSendRequest', () => {
    component.form.setValue({ email: '', password: '' });

    component.onSubmit();

    httpMock.expectNone('http://localhost:8000/accounts/login');
    expect(routerSpy.navigate).not.toHaveBeenCalled();
  });

  it('onSubmit_ValidForm_ShouldPOSTFormUrlEncoded_AndNavigateOnSuccess', () => {
    component.form.setValue({
      email: '  TEST@UMANITOBA.CA  ',
      password: 'Password1',
    });

    component.onSubmit();

    const req = httpMock.expectOne('http://localhost:8000/accounts/login');
    expect(req.request.method).toBe('POST');

    // Content-Type header
    expect(req.request.headers.get('Content-Type')).toBe('application/x-www-form-urlencoded');

    // Body should be urlencoded with normalized username
    expect(req.request.body).toContain('username=test%40umanitoba.ca');
    expect(req.request.body).toContain('password=Password1');

    // Respond with token
    req.flush({ access_token: 'token123', token_type: 'bearer' });

    expect(localStorage.getItem('access_token')).toBe('token123');
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/main-page']);
    expect(component.isLoading()).toBeFalse();
    expect(component.errorMessage()).toBe('');
  });

  it('onSubmit_RequestFails_ShouldSetErrorMessage_AndNotNavigate', () => {
    component.form.setValue({
      email: 'test@umanitoba.ca',
      password: 'Password1',
    });

    component.onSubmit();

    const req = httpMock.expectOne('http://localhost:8000/accounts/login');
    req.flush(
      { message: 'Unauthorized' },
      { status: 401, statusText: 'Unauthorized' }
    );

    expect(routerSpy.navigate).not.toHaveBeenCalled();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(component.isLoading()).toBeFalse();
    expect(component.errorMessage()).toBe('Login failed. Please check your credentials.');
  });
});
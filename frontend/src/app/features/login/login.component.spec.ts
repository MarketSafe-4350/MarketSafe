import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { LoginComponent } from './login.component';

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let loginComponent: LoginComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [provideNoopAnimations()],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    loginComponent = fixture.componentInstance;
    fixture.detectChanges();
  });

  // -------------------------
  // createForm() unit tests
  // -------------------------
  it('createForm_EmailEmpty_ShouldBeInvalid', () => {
    const control = loginComponent.form.get('email')!;
    control.setValue('');
    expect(control.hasError('required')).toBeTrue();
    expect(control.invalid).toBeTrue();
  });

  it('createForm_EmailWrongDomain_ShouldBeInvalid', () => {
    const control = loginComponent.form.get('email')!;
    control.setValue('test@gmail.com');
    expect(control.hasError('pattern')).toBeTrue();
    expect(control.invalid).toBeTrue();
  });

  it('createForm_EmailUniversityDomainUmanitoba_ShouldBeValid', () => {
    const control = loginComponent.form.get('email')!;
    control.setValue('abc@umanitoba.ca');
    expect(control.valid).toBeTrue();
  });

  it('createForm_EmailUniversityDomainMyumanitoba_ShouldBeValid', () => {
    const control = loginComponent.form.get('email')!;
    control.setValue('abc@myumanitoba.ca');
    expect(control.valid).toBeTrue();
  });

  it('createForm_PasswordEmpty_ShouldBeInvalid', () => {
    const control = loginComponent.form.get('password')!;
    control.setValue('');
    expect(control.hasError('required')).toBeTrue();
    expect(control.invalid).toBeTrue();
  });

  it('createForm_PasswordTooShort_ShouldBeInvalid', () => {
    const control = loginComponent.form.get('password')!;
    control.setValue('Pass1'); // < 8
    expect(control.hasError('minlength')).toBeTrue();
    expect(control.invalid).toBeTrue();
  });

  it('createForm_PasswordMinLength_ShouldBeValid', () => {
    const control = loginComponent.form.get('password')!;
    control.setValue('Password1'); // >= 8
    expect(control.valid).toBeTrue();
  });

  // -------------------------
  // onSubmit() unit tests
  // -------------------------
  it('onSubmit_EmptyForm_ShouldReturnNull', () => {
    const result = loginComponent.onSubmit();
    expect(result).toBeNull();
  });

  it('onSubmit_FormValid_ShouldReturnPayloadNormalized', () => {
    loginComponent.form.setValue({
      email: '  TEST@UMANITOBA.CA  ',
      password: 'Password1',
    });

    const result = loginComponent.onSubmit();

    expect(result).toEqual({
      email: 'test@umanitoba.ca',
      password: 'Password1',
    });
  });

  it('onSubmit_InvalidEmailDomain_ShouldReturnNull', () => {
    loginComponent.form.setValue({
      email: 'test@gmail.com',
      password: 'Password1',
    });

    const result = loginComponent.onSubmit();
    expect(result).toBeNull();
  });
});

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SignupComponent } from './signup.page';
import { provideNoopAnimations } from '@angular/platform-browser/animations';

describe('SignupComponent', () => {
  let fixture: ComponentFixture<SignupComponent>;
  let signupComponent: SignupComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SignupComponent],
      providers: [provideNoopAnimations()],
    }).compileComponents();

    fixture = TestBed.createComponent(SignupComponent);
    signupComponent = fixture.componentInstance;
    fixture.detectChanges();
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

  it('createForm_EmailUniversityDomain_ShouldBeValid', () => {
    const control = signupComponent.form.get('email')!;
    control.setValue('abc@umanitoba.ca');
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
  it('onSubmit_EmptyForm_ShouldReturnNull', () => {
    const result = signupComponent.onSubmit();
    expect(result).toBeNull();
  });

  it('onSubmit_FormValid_ShouldReturnPayloadNormalized', () => {
    signupComponent.form.setValue({
      firstName: 'TestFirst',
      lastName: 'TestLast',
      email: 'TEST@UMANITOBA.CA',
      password: 'Password1',
    });

    const result = signupComponent.onSubmit();

    expect(result).toEqual({
      firstName: 'TestFirst',
      lastName: 'TestLast',
      email: 'test@umanitoba.ca',
      password: 'Password1',
    });
  });
});

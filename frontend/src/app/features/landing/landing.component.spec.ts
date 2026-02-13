import { ComponentFixture, TestBed } from '@angular/core/testing';
import { LandingComponent } from './landing.component';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { Router } from '@angular/router';

describe('LandingComponent', () => {
  let fixture: ComponentFixture<LandingComponent>;
  let landingComponent: LandingComponent;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    await TestBed.configureTestingModule({
      imports: [LandingComponent],
      providers: [
        provideNoopAnimations(),
        { provide: Router, useValue: routerSpy }
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LandingComponent);
    landingComponent = fixture.componentInstance;
    fixture.detectChanges();
  });

  // -------------------------
  // Creation
  // -------------------------
  it('should create', () => {
    expect(landingComponent).toBeTruthy();
  });

  // -------------------------
  // Navigation logic tests
  // -------------------------
  it('showSignup_ShouldNavigateToSignup', () => {
    landingComponent.showSignup();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/signup']);
  });

});

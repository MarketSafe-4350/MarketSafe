import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HeaderComponent } from './header.component';
import { Router } from '@angular/router';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
describe('HeaderComponent', () => {
  let headerComponent: HeaderComponent;
  let fixture: ComponentFixture<HeaderComponent>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    await TestBed.configureTestingModule({
      imports: [HeaderComponent],
      providers: [
        provideNoopAnimations(),
        { provide: Router, useValue: routerSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HeaderComponent);
    headerComponent = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(headerComponent).toBeTruthy();
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

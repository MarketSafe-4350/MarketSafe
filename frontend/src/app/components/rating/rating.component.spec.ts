import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RatingComponent } from './rating.component';
import { provideNoopAnimations } from '@angular/platform-browser/animations';

describe('RatingComponent', () => {
  let fixture: ComponentFixture<RatingComponent>;
  let ratingComponent: RatingComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RatingComponent],
      providers: [provideNoopAnimations()],
    }).compileComponents();

    fixture = TestBed.createComponent(RatingComponent);
    ratingComponent = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(ratingComponent).toBeTruthy();
  });

  describe('default model', () => {
    it('model_DefaultModel_ShouldBeDefault', () => {
      expect(ratingComponent.model.stars).toEqual([
        'star_border',
        'star_border',
        'star_border',
        'star_border',
        'star_border',
      ]);
      expect(ratingComponent.model.ratingAvg).toBe('-');
      expect(ratingComponent.model.reviewCount).toBe('(0 review(s))');
    });
  });

  describe('ngOnChanges behaviour', () => {
    it('model_Average3ReviewCount5_ShouldBeCorrect', () => {
      ratingComponent.average = 3;
      ratingComponent.reviewCount = 5;
      ratingComponent.ngOnChanges();
      expect(ratingComponent.model.stars).toEqual([
        'star',
        'star',
        'star',
        'star_border',
        'star_border',
      ]);
      expect(ratingComponent.model.ratingAvg).toBe('3.0');
      expect(ratingComponent.model.reviewCount).toBe('(5 review(s))');
    });

    it('model_ZeroAverage_ShouldBeCorrect', () => {
      ratingComponent.average = 0;
      ratingComponent.reviewCount = 0;
      ratingComponent.ngOnChanges();
      expect(ratingComponent.model.stars).toEqual([
        'star_border',
        'star_border',
        'star_border',
        'star_border',
        'star_border',
      ]);
      expect(ratingComponent.model.ratingAvg).toBe('0.0');
      expect(ratingComponent.model.reviewCount).toBe('(0 review(s))');
    });

    it('model_HalfStarAverage_ShouldBeCorrect', () => {
      ratingComponent.average = 2.5;
      ratingComponent.reviewCount = 10;
      ratingComponent.ngOnChanges();

      expect(ratingComponent.model.stars).toEqual([
        'star',
        'star',
        'star_half',
        'star_border',
        'star_border',
      ]);
      expect(ratingComponent.model.ratingAvg).toBe('2.5');
      expect(ratingComponent.model.reviewCount).toBe('(10 review(s))');
    });

    it('model_NullAverageAndReviewCount_ShouldBeDefault', () => {
      ratingComponent.average = null;
      ratingComponent.reviewCount = null;
      ratingComponent.ngOnChanges();

      expect(ratingComponent.model.stars).toEqual([
        'star_border',
        'star_border',
        'star_border',
        'star_border',
        'star_border',
      ]);
      expect(ratingComponent.model.ratingAvg).toBe('0.0');
      expect(ratingComponent.model.reviewCount).toBe('(0 review(s))');
    });
  });
});

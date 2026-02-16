import {
  ChangeDetectionStrategy,
  Component,
  Input,
  OnChanges,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

export interface RatingModel {
  stars: string[];
  ratingAvg: string;
  reviewCount: string;
}

@Component({
  standalone: true,
  selector: 'app-rating',
  templateUrl: './rating.component.html',
  styleUrls: ['./rating.component.scss'],
  imports: [MatIconModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RatingComponent implements OnChanges {
  @Input() average: number | null | undefined = null;
  @Input() reviewCount: number | null | undefined = null;

  model: RatingModel = {
    stars: [
      'star_border',
      'star_border',
      'star_border',
      'star_border',
      'star_border',
    ],
    ratingAvg: '-',
    reviewCount: '(0 reviews)',
  };

  ngOnChanges(): void {
    const average = this.average ?? 0;
    const reviews = this.reviewCount ?? 0;
    this.model = this.buildRatingModel(average, reviews);
  }

  private buildRatingModel(average: number, reviews: number): RatingModel {
    const starsIcons: string[] = [];

    for (let i = 0; i < 5; i++) {
      if (average >= i + 1) starsIcons.push('star');
      else if (average >= i + 0.5) starsIcons.push('star_half');
      else starsIcons.push('star_border');
    }
    return {
      stars: starsIcons,
      ratingAvg: average ? average.toFixed(1) : '-',
      reviewCount: `(${reviews} review(s))`,
    };
  }
}

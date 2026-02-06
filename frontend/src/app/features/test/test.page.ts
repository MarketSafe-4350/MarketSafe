import { ChangeDetectionStrategy, Component } from '@angular/core';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';

/** @title Simple form field */
@Component({
  standalone: true,
  selector: 'test',
  templateUrl: './test.page.html',
  styleUrl: './test.page.scss',
  imports: [MatFormFieldModule, MatInputModule, MatSelectModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormFieldOverviewExample {}

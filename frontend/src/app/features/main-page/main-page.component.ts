import { Component } from '@angular/core';
import { HeaderComponent } from '../../components/header/header.component';
import { LeftNavigationComponent } from '../left-navigation/left-navigation.component';

@Component({
  selector: 'main-page',
  standalone: true,
  imports: [HeaderComponent, LeftNavigationComponent],
  templateUrl: './main-page.component.html',
  styleUrls: ['./main-page.component.scss'],
})
export class MainPageComponent {}


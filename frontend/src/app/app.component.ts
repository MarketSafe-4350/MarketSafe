import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent {
  message = '';

  constructor(private http: HttpClient) {}

  callHelloApi(): void {
    this.http.get<{ hello: string }>('/api/hello').subscribe({
      next: (res) => (this.message = res.hello),
      error: () => (this.message = 'Error calling backend'),
    });
  }

  callHealthApi(): void {
    this.http.get<{ status: string }>('/api/health').subscribe({
      next: (res) => (this.message = res.status),
      error: () => (this.message = 'Error calling backend'),
    });
  }
}

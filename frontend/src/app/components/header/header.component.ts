import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIcon } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
@Component({
  selector: 'app-header',
  standalone: true,
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
  imports: [MatCardModule, MatIcon, MatMenuModule, MatButtonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HeaderComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly accountsApi = inject(AccountsApiService);

  readonly displayName = signal('Someone');

  ngOnInit(): void {
    this.accountsApi.getMe().subscribe({
      next: (account) => {
        const fullName = `${account.fname} ${account.lname}`.trim();
        this.displayName.set(fullName || 'Someone');
      },
      error: (error) => {
        console.error('Failed to load current user for header:', error);
      },
    });
  }

  onLogout(): void {
    // Clear the authentication auth_token
    localStorage.removeItem('access_token');
    this.router.navigate(['/']);
  }

  goToProfile(): void {
    this.router.navigate(['/profile']);
  }
}

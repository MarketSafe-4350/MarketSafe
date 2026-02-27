import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { of } from 'rxjs';

import { MatDialog } from '@angular/material/dialog';

import { SearchPageComponent } from './search-page.component';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
import { ListingsApiService } from '../../shared/services/listings-api.service';
import { Listing } from '../../shared/models/listing.models';

@Component({ template: '' })
class DummyRouteComponent {}

describe('SearchPageComponent', () => {
  let fixture: ComponentFixture<SearchPageComponent>;
  let component: SearchPageComponent;
  let listingsApiSpy: jasmine.SpyObj<ListingsApiService>;
  let accountsApiSpy: jasmine.SpyObj<AccountsApiService>;
  let router: Router;
  let matDialogSpy: jasmine.SpyObj<MatDialog>;

  const searchResult: Listing = {
    id: 25,
    sellerId: 500,
    title: 'Gaming Laptop',
    description: 'RTX model',
    imageUrl: '',
    price: 999,
    location: 'Winnipeg',
    createdAt: new Date('2026-02-25').toISOString(),
    isSold: false,
  };

  beforeEach(async () => {
    localStorage.clear();
    const payload = btoa(JSON.stringify({ sub: '123' }));
    localStorage.setItem('access_token', `x.${payload}.y`);

    listingsApiSpy = jasmine.createSpyObj<ListingsApiService>('ListingsApiService', [
      'getMine',
      'search',
      'create',
      'delete',
    ]);
    listingsApiSpy.getMine.and.returnValue(of([]));
    listingsApiSpy.search.and.returnValue(of([searchResult]));

    matDialogSpy = jasmine.createSpyObj<MatDialog>('MatDialog', ['open']);
    accountsApiSpy = jasmine.createSpyObj<AccountsApiService>('AccountsApiService', ['getMe']);
    accountsApiSpy.getMe.and.returnValue(
      of({
        id: 123,
        email: 'test@example.com',
        fname: 'Test',
        lname: 'User',
        verified: true,
      })
    );

    await TestBed.configureTestingModule({
      imports: [
        SearchPageComponent,
        RouterTestingModule.withRoutes([
          { path: 'main-page', component: DummyRouteComponent },
          { path: 'search', component: DummyRouteComponent },
          { path: 'profile', component: DummyRouteComponent },
          { path: 'my-listings', component: DummyRouteComponent },
        ]),
      ],
      declarations: [DummyRouteComponent],
      providers: [
        provideNoopAnimations(),
        { provide: ListingsApiService, useValue: listingsApiSpy },
        { provide: AccountsApiService, useValue: accountsApiSpy },
      ],
    })
      .overrideComponent(SearchPageComponent, {
        add: {
          providers: [{ provide: MatDialog, useValue: matDialogSpy }],
        },
      })
      .compileComponents();

    fixture = TestBed.createComponent(SearchPageComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('onSubmitSearch_ShouldRenderResults', () => {
    fixture.detectChanges();
    component.searchQuery = 'gaming laptop';

    component.onSubmitSearch();
    fixture.detectChanges();

    expect(listingsApiSpy.search).toHaveBeenCalledWith('gaming laptop');
    const resultButtons = fixture.nativeElement.querySelectorAll('.result-card-button');
    expect(resultButtons.length).toBe(1);
  });

  it('resultClick_ShouldNavigateToMainPageWithListingId', async () => {
    fixture.detectChanges();
    component.searchQuery = 'gaming laptop';
    component.onSubmitSearch();
    fixture.detectChanges();

    const navigateSpy = spyOn(router, 'navigate').and.resolveTo(true);
    const button: HTMLButtonElement | null =
      fixture.nativeElement.querySelector('.result-card-button');

    expect(button).toBeTruthy();
    button?.click();

    expect(navigateSpy).toHaveBeenCalledWith(['/main-page'], {
      queryParams: { listingId: searchResult.id },
    });
  });
});

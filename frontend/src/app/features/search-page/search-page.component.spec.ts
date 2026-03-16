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

  it('sellerProfileClick_ShouldNavigateToSellerProfile', () => {
    fixture.detectChanges();
    component.searchQuery = 'gaming laptop';
    component.onSubmitSearch();
    fixture.detectChanges();

    const navigateSpy = spyOn(router, 'navigate').and.resolveTo(true);
    const button: HTMLButtonElement | null =
      fixture.nativeElement.querySelector('.seller-profile-btn');

    expect(button).toBeTruthy();
    button?.click();

    expect(navigateSpy).toHaveBeenCalledWith(['/profile', searchResult.sellerId]);
  });

  it('canViewSellerProfile_ShouldBeFalseForCurrentUser', () => {
    fixture.detectChanges();

    expect(component.canViewSellerProfile(123)).toBeFalse();
    expect(component.canViewSellerProfile(searchResult.sellerId)).toBeTrue();
  });

  it('changeSortType_ShouldUpdateSortOptionAndCallSortResults', () => {
    spyOn(component, 'sortResults');
    component.changeSortType('price');
    expect(component.selectedSortOption).toBe('price');
    expect(component.sortResults).toHaveBeenCalled();
  });

  it('toggleSortDirection_ShouldToggleSortDirectionAndCallSortResults', () => {
    spyOn(component, 'sortResults');

    component.toggleSortDirection();
    expect(component.sortDirection).toBe('desc');
    expect(component.sortResults).toHaveBeenCalled();

    component.toggleSortDirection();
    expect(component.sortDirection).toBe('asc');
    expect(component.sortResults).toHaveBeenCalled();
  });

  it('sortResults_ShouldSortByDateAscending', () => {
    const listings: Listing[] = [
      { ...searchResult, createdAt: new Date('2026-01-01').toISOString() },
      { ...searchResult, createdAt: new Date('2026-02-25').toISOString() },
    ];

    component.searchResults = listings;
    component.selectedSortOption = 'date';
    component.sortDirection = 'asc';
    component.sortResults();

    expect(component.searchResults[0].createdAt).toBe(new Date('2026-01-01').toISOString());
    expect(component.searchResults[1].createdAt).toBe(new Date('2026-02-25').toISOString());
  });

  it('sortResults_ShouldSortByDateDescending', () => {
    const listings: Listing[] = [
      { ...searchResult, createdAt: new Date('2026-01-01').toISOString() },
      { ...searchResult, createdAt: new Date('2026-02-25').toISOString() },
    ];

    component.searchResults = listings;
    component.selectedSortOption = 'date';
    component.sortDirection = 'desc';
    component.sortResults();

    expect(component.searchResults[0].createdAt).toBe(new Date('2026-02-25').toISOString());
    expect(component.searchResults[1].createdAt).toBe(new Date('2026-01-01').toISOString());
  });

  it('sortResults_ShouldSortByPriceAscending', () => {
    const listings: Listing[] = [
      { ...searchResult, price: 1000 },
      { ...searchResult, price: 500 },
    ];

    component.searchResults = listings;
    component.selectedSortOption = 'price';
    component.sortDirection = 'asc';
    component.sortResults();

    expect(component.searchResults[0].price).toBe(500);
    expect(component.searchResults[1].price).toBe(1000);
  });

  it('sortResults_ShouldSortByPriceDescending', () => {
    const listings: Listing[] = [
      { ...searchResult, price: 1000 },
      { ...searchResult, price: 500 },
    ];

    component.searchResults = listings;
    component.selectedSortOption = 'price';
    component.sortDirection = 'desc';
    component.sortResults();

    expect(component.searchResults[0].price).toBe(1000);
    expect(component.searchResults[1].price).toBe(500);
  });

  it('sortResults_ShouldSortByTitleAscending', () => {
    const listings: Listing[] = [
      { ...searchResult, title: 'B' },
      { ...searchResult, title: 'A' },
    ];

    component.searchResults = listings;
    component.selectedSortOption = 'title';
    component.sortDirection = 'asc';
    component.sortResults();

    expect(component.searchResults[0].title).toBe('A');
    expect(component.searchResults[1].title).toBe('B');
  });

  it('sortResults_ShouldSortByTitleDescending', () => {
    const listings: Listing[] = [
      { ...searchResult, title: 'B' },
      { ...searchResult, title: 'A' },
    ];

    component.searchResults = listings;
    component.selectedSortOption = 'title';
    component.sortDirection = 'desc';
    component.sortResults();

    expect(component.searchResults[0].title).toBe('B');
    expect(component.searchResults[1].title).toBe('A');
  });
});

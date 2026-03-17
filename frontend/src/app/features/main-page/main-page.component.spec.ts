import { ComponentFixture, TestBed } from '@angular/core/testing';
import { fakeAsync, tick } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { of } from 'rxjs';
import { ActivatedRoute, Router, convertToParamMap } from '@angular/router';

import { MatDialog, MatDialogRef } from '@angular/material/dialog';

import { MainPageComponent } from './main-page.component';
import { ListingsApiService } from '../../shared/services/listings-api.service';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
import { Listing } from '../../shared/models/listing.models';
import { CommentApiService } from '../../shared/services/comments-api.service';
import { OffersApiService } from '../../shared/services/offers-api.service';
import { SendOfferDialogComponent } from '../send-offer/send-offer.component';

describe('MainPageComponent', () => {
  let fixture: ComponentFixture<MainPageComponent>;
  let component: MainPageComponent;
  let listingsApiSpy: jasmine.SpyObj<ListingsApiService>;
  let accountsApiSpy: jasmine.SpyObj<AccountsApiService>;
  let matDialogSpy: jasmine.SpyObj<MatDialog>;
  let commentApiSpy: jasmine.SpyObj<CommentApiService>;
  let offersApiSpy: jasmine.SpyObj<OffersApiService>;
  let dialogRefSpy: jasmine.SpyObj<MatDialogRef<SendOfferDialogComponent>>;
  let activatedRouteStub: {
    snapshot: { queryParamMap: ReturnType<typeof convertToParamMap> };
  };

  const ownedListing: Listing = {
    id: 1,
    sellerId: 123,
    title: 'Owned Listing',
    description: 'Mine',
    imageUrl: '',
    price: 10,
    location: 'Winnipeg',
    createdAt: new Date('2026-02-24').toISOString(),
    isSold: false,
  };

  const otherListing: Listing = {
    id: 2,
    sellerId: 999,
    title: 'Other Listing',
    description: 'Not mine',
    imageUrl: '',
    price: 12,
    location: 'Winnipeg',
    createdAt: new Date('2026-02-24').toISOString(),
    isSold: false,
  };

  beforeEach(async () => {
    localStorage.clear();
    const payload = btoa(JSON.stringify({ sub: '123' }));
    localStorage.setItem('access_token', `x.${payload}.y`);

    listingsApiSpy = jasmine.createSpyObj<ListingsApiService>(
      'ListingsApiService',
      ['getAll', 'getMine', 'create', 'delete'],
    );
    listingsApiSpy.getAll.and.returnValue(of([ownedListing, otherListing]));

    accountsApiSpy = jasmine.createSpyObj<AccountsApiService>(
      'AccountsApiService',
      ['getMe'],
    );
    accountsApiSpy.getMe.and.returnValue(
      of({
        id: 0,
        email: 'test@example.com',
        fname: 'Test',
        lname: 'User',
        verified: false,
      }),
    );

    matDialogSpy = jasmine.createSpyObj<MatDialog>('MatDialog', ['open']);
    activatedRouteStub = {
      snapshot: {
        queryParamMap: convertToParamMap({}),
      },
    };

    commentApiSpy = jasmine.createSpyObj<CommentApiService>(
      'CommentApiService',
      ['getComment', 'create'],
    );

    commentApiSpy.getComment.and.returnValue(of([]));
    commentApiSpy.create.and.returnValue(
      of({
        id: 1,
        listingId: ownedListing.id,
        authorId: 123,
        authorLabel: 'Test User',
        body: 'Great listing',
        createdAt: new Date().toISOString(),
      }),
    );

    offersApiSpy = jasmine.createSpyObj<OffersApiService>('OffersApiService', [
      'create',
    ]);
    offersApiSpy.create.and.returnValue(of({}));

    dialogRefSpy = jasmine.createSpyObj<MatDialogRef<SendOfferDialogComponent>>(
      'MatDialogRef',
      ['afterClosed'],
    );
    dialogRefSpy.afterClosed.and.returnValue(of(null));
    matDialogSpy.open.and.returnValue(dialogRefSpy);

    await TestBed.configureTestingModule({
      imports: [MainPageComponent, RouterTestingModule],
      providers: [
        provideNoopAnimations(),
        { provide: ListingsApiService, useValue: listingsApiSpy },
        { provide: AccountsApiService, useValue: accountsApiSpy },
        { provide: CommentApiService, useValue: commentApiSpy },
        { provide: OffersApiService, useValue: offersApiSpy },
        { provide: ActivatedRoute, useValue: activatedRouteStub },
      ],
    })
      .overrideComponent(MainPageComponent, {
        add: {
          providers: [{ provide: MatDialog, useValue: matDialogSpy }],
        },
      })
      .compileComponents();

    fixture = TestBed.createComponent(MainPageComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('ngOnInit_ShouldLoadAllListings', () => {
    fixture.detectChanges();

    expect(listingsApiSpy.getAll).toHaveBeenCalled();
    expect(component.listings.length).toBe(2);
    expect(component.isLoading).toBeFalse();
  });

  it('sidebarListings_ShouldOnlyIncludeOwnedListings', () => {
    fixture.detectChanges();

    expect(component.sidebarListings.length).toBe(1);
    expect(component.sidebarListings[0].id).toBe(ownedListing.id);
    expect(component.sidebarListings[0].title).toBe(ownedListing.title);
  });

  it('template_ShouldShowDeleteButtonOnlyForOwnedListingsInFeed', () => {
    fixture.detectChanges();

    const deleteButtons =
      fixture.nativeElement.querySelectorAll('button.delete-btn');
    expect(deleteButtons.length).toBe(1);
  });

  it('openSellerProfile_ShouldNavigateToSellerProfileRoute', async () => {
    fixture.detectChanges();

    const router = TestBed.inject(Router);
    const navigateSpy = spyOn(router, 'navigate').and.resolveTo(true);

    component.openSellerProfile(otherListing);

    expect(navigateSpy).toHaveBeenCalledWith(['/profile', otherListing.sellerId]);
  });

  it('canViewSellerProfile_ShouldBeFalseForOwnedListing', () => {
    fixture.detectChanges();

    expect(component.canViewSellerProfile(ownedListing)).toBeFalse();
    expect(component.canViewSellerProfile(otherListing)).toBeTrue();
  });

  it('canSendOffer_ShouldOnlyBeTrueForOtherActiveListing', () => {
    fixture.detectChanges();

    expect(component.canSendOffer(ownedListing)).toBeFalse();
    expect(component.canSendOffer({ ...otherListing, isSold: true })).toBeFalse();
    expect(component.canSendOffer(otherListing)).toBeTrue();
  });

  it('submitComment_WhitespaceOnly_ShouldSetErrorAndNotCreateComment', () => {
    fixture.detectChanges();

    component.setCommentDraft(ownedListing.id, '   ');
    component.submitComment(ownedListing);

    expect(component.getComments(ownedListing.id).length).toBe(0);
    expect(component.getCommentError(ownedListing.id)).toBe(
      'Comment cannot be empty.',
    );
  });

  it('submitComment_ValidComment_ShouldTrimStoreAndUpdateSidebarCount', () => {
    fixture.detectChanges();

    component.setCommentDraft(ownedListing.id, '  Great listing  ');
    component.submitComment(ownedListing);

    const comments = component.getComments(ownedListing.id);
    expect(comments.length).toBe(1);
    expect(comments[0].body).toBe('Great listing');
    expect(comments[0].authorLabel).toBe('Test User');
    expect(component.sidebarListings[0].comments).toBe(1);
  });

  it('onListingClick_SoldListing_ShouldNotOpenCommentPanel', () => {
    fixture.detectChanges();

    const soldListing: Listing = { ...ownedListing, id: 77, isSold: true };
    component.onListingClick(soldListing);

    expect(component.isCommentPanelOpen(soldListing.id)).toBeFalse();
  });

  it('template_ShouldShowUpdatedCommentCountOnListingCardBeforePanelOpens', () => {
    fixture.detectChanges();

    component.setCommentDraft(ownedListing.id, 'First');
    component.submitComment(ownedListing);
    fixture.detectChanges();

    const commentCountTexts = Array.from(
      fixture.nativeElement.querySelectorAll(
        '.comment-count',
      ) as NodeListOf<HTMLElement>,
    ).map((element) => element.textContent?.trim());

    expect(commentCountTexts).toContain('1 comment');
  });

  it('ngOnInit_WithListingIdQueryParam_ShouldScrollAndHighlightListing', fakeAsync(() => {
    activatedRouteStub.snapshot.queryParamMap = convertToParamMap({
      listingId: String(otherListing.id),
    });

    const scrollIntoView = jasmine.createSpy('scrollIntoView');
    spyOn(document, 'getElementById').and.returnValue({
      scrollIntoView,
    } as unknown as HTMLElement);

    fixture = TestBed.createComponent(MainPageComponent);
    component = fixture.componentInstance;

    fixture.detectChanges();

    tick(0);
    expect(component.highlightedListingId).toBe(otherListing.id);
    expect(document.getElementById).toHaveBeenCalledWith(
      `listing-${otherListing.id}`,
    );
    expect(scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'center',
    });

    tick(2200);
    expect(component.highlightedListingId).toBeNull();
  }));
});

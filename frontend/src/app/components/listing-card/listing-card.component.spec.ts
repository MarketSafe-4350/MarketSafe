import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ListingCardComponent } from './listing-card.component';
import { provideNoopAnimations } from '@angular/platform-browser/animations';

describe('ListingCardComponent', () => {
  let fixture: ComponentFixture<ListingCardComponent>;
  let listingCardComponent: ListingCardComponent;

  const mockListing = {
    id: 1,
    title: 'Test Listing',
    description: 'This is a test listing.',
    price: 99.99,
    location: 'Winnipeg',
    imageUrl: '/assets/images/comoputer.png',
    createdAt: new Date('2024-01-01').toISOString(),
    isSold: false,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ListingCardComponent],
      providers: [provideNoopAnimations()],
    }).compileComponents();

    fixture = TestBed.createComponent(ListingCardComponent);
    listingCardComponent = fixture.componentInstance;
    fixture.detectChanges();
  });

  describe('when listing is null', () => {
    beforeEach(() => {
      listingCardComponent.listing = null;
    });

    it('getTitle_ListingNull_ShouldBeUntitledListing', () => {
      expect(listingCardComponent.title).toBe('Untitled Listing');
    });

    it('getPrice_ListingNull_ShouldBePriceUnavailable', () => {
      expect(listingCardComponent.price).toBe('Price Unavailable');
    });

    it('getLocation_ListingNull_ShouldBeLocationUnavailable', () => {
      expect(listingCardComponent.location).toBe('Location Unavailable');
    });

    it('getCreatedAt_ListingNull_ShouldBeDateUnavailable', () => {
      expect(listingCardComponent.createdAt).toBe('Date Unavailable');
    });

    it('getIsSold_ListingNull_ShouldBeFalse', () => {
      expect(listingCardComponent.isSold).toBe(false);
    });
  });

  describe('when listing is provided', () => {
    beforeEach(() => {
      listingCardComponent.listing = mockListing;
      fixture.detectChanges();
    });

    it('getTitle_ListingProvided_ShouldBeExpectedTitle', () => {
      expect(listingCardComponent.title).toBe(mockListing.title);
    });

    it('getPrice_ListingProvided_ShouldBeExpectedPrice', () => {
      expect(listingCardComponent.price).toBe(`$${mockListing.price}`);
    });

    it('getDescription_ListingProvided_ShouldBeExpectedDescription', () => {
      expect(listingCardComponent.description).toBe(mockListing.description);
    });

    it('getLocation_ListingProvided_ShouldBeExpectedLocation', () => {
      expect(listingCardComponent.location).toBe(mockListing.location);
    });

    it('getCreatedAt_ListingProvided_ShouldBeExpectedDate', () => {
      const expectedDate = new Date(mockListing.createdAt).toLocaleDateString(
        undefined,
        {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
        },
      );

      expect(listingCardComponent.createdAt).toBe(expectedDate);
    });

    it('getIsSold_ListingProvided_ShouldBeExpectedIsSold', () => {
      expect(listingCardComponent.isSold).toBe(mockListing.isSold);
    });

    it('getCommentCountLabel_SingularAndPlural_ShouldMatchCount', () => {
      listingCardComponent.commentCount = 1;
      expect(listingCardComponent.commentCountLabel).toBe('1 comment');

      listingCardComponent.commentCount = 2;
      expect(listingCardComponent.commentCountLabel).toBe('2 comments');
    });

    it('template_ShouldRenderCommentCount', () => {
      fixture.componentRef.setInput('commentCount', 3);
      fixture.detectChanges();

      const commentCount = fixture.nativeElement.querySelector('.comment-count');
      expect(commentCount?.textContent?.trim()).toBe('3 comments');
    });

    it('template_ShouldRenderSellerProfileButtonWhenEnabled', () => {
      fixture.componentRef.setInput('showSellerProfileButton', true);
      fixture.detectChanges();

      const sellerProfileButton =
        fixture.nativeElement.querySelector('.seller-profile-btn');
      expect(sellerProfileButton?.textContent?.trim()).toBe(
        'View Seller Profile',
      );
    });

    it('sellerProfileClick_ShouldEmitWhenButtonClicked', () => {
      fixture.componentRef.setInput('showSellerProfileButton', true);
      fixture.detectChanges();

      const emitSpy = spyOn(listingCardComponent.sellerProfileClick, 'emit');
      const sellerProfileButton: HTMLButtonElement | null =
        fixture.nativeElement.querySelector('.seller-profile-btn');

      sellerProfileButton?.click();

      expect(emitSpy).toHaveBeenCalled();
    });
  });
});

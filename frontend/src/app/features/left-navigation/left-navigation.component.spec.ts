import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Component } from '@angular/core';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';
import { Router } from '@angular/router';

import { MatDialog, MatDialogRef } from '@angular/material/dialog';

import { LeftNavigationComponent } from './left-navigation.component';
import {
  CreateListingDialogComponent,
  CreateListingPayload,
} from '../create-listing/create-listing.component';

@Component({ template: '' })
class DummyRouteComponent {}

describe('LeftNavigationComponent', () => {
  let fixture: ComponentFixture<LeftNavigationComponent>;
  let component: LeftNavigationComponent;
  let router: Router;

  const dialogRefSpy = jasmine.createSpyObj<MatDialogRef<CreateListingDialogComponent>>(
    'MatDialogRef',
    ['afterClosed']
  );

  const matDialogSpy = jasmine.createSpyObj<MatDialog>('MatDialog', ['open']);

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [DummyRouteComponent],
      imports: [
        LeftNavigationComponent,
        RouterTestingModule.withRoutes([
          { path: 'main-page', component: DummyRouteComponent },
          { path: 'profile', component: DummyRouteComponent },
          { path: 'search', component: DummyRouteComponent },
          { path: 'my-listings', component: DummyRouteComponent },
        ]),
      ],
      providers: [provideNoopAnimations()],
    })
      .overrideComponent(LeftNavigationComponent, {
        set: {
          providers: [{ provide: MatDialog, useValue: matDialogSpy }],
        },
      })
      .compileComponents();

    fixture = TestBed.createComponent(LeftNavigationComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);

    matDialogSpy.open.calls.reset();
    dialogRefSpy.afterClosed.calls.reset();

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('defaultInputs_ShouldHaveDefaults', () => {
    expect(component.listingsCount).toBe(0);
    expect(component.listings).toEqual([]);
  });

  it('openCreateListing_ShouldOpenDialogWithCorrectConfig', () => {
    dialogRefSpy.afterClosed.and.returnValue(of(null));
    matDialogSpy.open.and.returnValue(dialogRefSpy);

    component.openCreateListing();

    expect(matDialogSpy.open).toHaveBeenCalledWith(CreateListingDialogComponent, {
      width: '640px',
      maxWidth: '92vw',
      autoFocus: false,
    });
  });

  it('openCreateListing_AfterClosedNull_ShouldNotEmit', () => {
    spyOn(component.createListing, 'emit');
    dialogRefSpy.afterClosed.and.returnValue(of(null));
    matDialogSpy.open.and.returnValue(dialogRefSpy);

    component.openCreateListing();

    expect(component.createListing.emit).not.toHaveBeenCalled();
  });

  it('openCreateListing_AfterClosedPayload_ShouldEmitPayload', () => {
    spyOn(component.createListing, 'emit');
    const payload: CreateListingPayload = {
      title: 'Table',
      description: 'Nice table',
      price: 100,
      location: 'Winnipeg',
      picture: null,
    };

    dialogRefSpy.afterClosed.and.returnValue(of(payload));
    matDialogSpy.open.and.returnValue(dialogRefSpy);

    component.openCreateListing();

    expect(component.createListing.emit).toHaveBeenCalledWith(payload);
  });

  it('onDeleteListing_ShouldEmitListingId', () => {
    spyOn(component.deleteListing, 'emit');
    const event = new MouseEvent('click');
    spyOn(event, 'stopPropagation');

    component.onDeleteListing(event, 123);

    expect(event.stopPropagation).toHaveBeenCalled();
    expect(component.deleteListing.emit).toHaveBeenCalledWith(123);
  });

  it('profileLink_ShouldBeActive_WhenCurrentRouteIsProfile', async () => {
    await router.navigateByUrl('/profile');
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const anchors = Array.from(
      fixture.nativeElement.querySelectorAll('a.mat-mdc-list-item')
    ) as HTMLAnchorElement[];
    const profileLink = anchors.find((anchor) =>
      anchor.textContent?.includes('Profile')
    );

    expect(profileLink).toBeTruthy();
    expect(profileLink?.classList.contains('active')).toBeTrue();
  });

  it('seeAllButton_ShouldNavigateToMyListings', async () => {
    const button: HTMLButtonElement | null =
      fixture.nativeElement.querySelector('.see-all-btn');

    expect(button).toBeTruthy();

    button?.click();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(router.url).toBe('/my-listings');
  });
});

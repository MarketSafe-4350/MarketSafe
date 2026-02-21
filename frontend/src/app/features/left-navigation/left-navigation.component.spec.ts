import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { MatDialog } from '@angular/material/dialog';

import { LeftNavigationComponent } from './left-navigation.component';
import {
  CreateListingDialogComponent,
  CreateListingPayload,
} from '../create-listing/create-listing.component';

describe('LeftNavigationComponent', () => {
  let fixture: ComponentFixture<LeftNavigationComponent>;
  let component: LeftNavigationComponent;

  const dialogRefSpy = {
    afterClosed: jasmine.createSpy('afterClosed'),
  };

  const matDialogSpy = jasmine.createSpyObj<MatDialog>('MatDialog', ['open']);

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LeftNavigationComponent, RouterTestingModule],
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

    matDialogSpy.open.calls.reset();
    dialogRefSpy.afterClosed.calls.reset();

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('defaultInputs_ShouldHaveDefaults', () => {
    expect(component.listingsCount).toBe(19);
    expect(component.listings.length).toBeGreaterThan(0);
  });

  it('openCreateListing_ShouldOpenDialogWithCorrectConfig', () => {
    dialogRefSpy.afterClosed.and.returnValue(of(null));
    matDialogSpy.open.and.returnValue(dialogRefSpy as any);

    component.openCreateListing();

    expect(matDialogSpy.open).toHaveBeenCalledWith(CreateListingDialogComponent, {
      width: '640px',
      maxWidth: '92vw',
      autoFocus: false,
    });
  });

  it('openCreateListing_AfterClosedNull_ShouldNotLog', () => {
    spyOn(console, 'log');

    dialogRefSpy.afterClosed.and.returnValue(of(null));
    matDialogSpy.open.and.returnValue(dialogRefSpy as any);

    component.openCreateListing();

    expect(console.log).not.toHaveBeenCalled();
  });

  it('openCreateListing_AfterClosedPayload_ShouldLogPayload', () => {
    spyOn(console, 'log');

    const payload: CreateListingPayload = {
      title: 'Table',
      description: 'Nice table',
      price: 100,
      location: 'Winnipeg',
      picture: null,
    };

    dialogRefSpy.afterClosed.and.returnValue(of(payload));
    matDialogSpy.open.and.returnValue(dialogRefSpy as any);

    component.openCreateListing();

    expect(console.log).toHaveBeenCalledWith('Create listing payload:', payload);
  });
});
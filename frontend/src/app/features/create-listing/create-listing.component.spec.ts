import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MatDialogRef } from '@angular/material/dialog';

import {
  CreateListingDialogComponent,
  CreateListingPayload,
} from './create-listing.component';

describe('CreateListingDialogComponent', () => {
  let fixture: ComponentFixture<CreateListingDialogComponent>;
  let component: CreateListingDialogComponent;

  const dialogRefSpy = jasmine.createSpyObj<MatDialogRef<CreateListingDialogComponent>>(
    'MatDialogRef',
    ['close']
  );

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CreateListingDialogComponent],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: dialogRefSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CreateListingDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    dialogRefSpy.close.calls.reset();
  });

  // -------------------------
  // Form validation tests
  // -------------------------
  it('form_TitleEmpty_ShouldBeInvalid', () => {
    const control = component.form.get('title')!;
    control.setValue('');
    expect(control.hasError('required')).toBeTrue();
    expect(control.invalid).toBeTrue();
  });

  it('form_DescriptionTooShort_ShouldBeInvalid', () => {
    const control = component.form.get('description')!;
    control.setValue('short');
    expect(control.hasError('minlength')).toBeTrue();
    expect(control.invalid).toBeTrue();
  });

  it('form_PriceNegative_ShouldBeInvalid', () => {
    const control = component.form.get('price')!;
    control.setValue(-1);
    expect(control.hasError('min')).toBeTrue();
    expect(control.invalid).toBeTrue();
  });

  it('form_LocationEmpty_ShouldBeInvalid', () => {
    const control = component.form.get('location')!;
    control.setValue('');
    expect(control.hasError('required')).toBeTrue();
    expect(control.invalid).toBeTrue();
  });

  // -------------------------
  // cancel() tests
  // -------------------------
  it('cancel_ShouldCloseDialogWithNull', () => {
    component.cancel();
    expect(dialogRefSpy.close).toHaveBeenCalledWith(null);
  });

  // -------------------------
  // onFileSelected() tests
  // -------------------------
  it('onFileSelected_WithFile_ShouldSetSelectedFile', () => {
    const file = new File(['hello'], 'photo.png', { type: 'image/png' });

    const input = document.createElement('input');
    Object.defineProperty(input, 'files', {
      value: [file],
    });

    component.onFileSelected({ target: input } as unknown as Event);

    expect(component.selectedFile).toBe(file);
  });

  // -------------------------
  // create() tests
  // -------------------------
  it('create_InvalidForm_ShouldNotCloseDialog', () => {
    // leave defaults invalid
    component.create();
    expect(dialogRefSpy.close).not.toHaveBeenCalled();
  });

  it('create_ValidForm_ShouldCloseDialogWithPayloadTrimmed', () => {
    component.form.setValue({
      title: '  Table  ',
      description: '  A nice wooden table for sale.  ',
      price: 150,
      location: '  Winnipeg  ',
    });

    const file = new File(['x'], 'img.jpg', { type: 'image/jpeg' });
    component.selectedFile = file;

    component.create();

    const expected: CreateListingPayload = {
      title: 'Table',
      description: 'A nice wooden table for sale.',
      price: 150,
      location: 'Winnipeg',
      picture: file,
    };

    expect(dialogRefSpy.close).toHaveBeenCalledWith(expected);
  });

  it('create_ValidForm_NoPicture_ShouldCloseDialogWithPictureNull', () => {
    component.form.setValue({
      title: 'Chair',
      description: 'Comfortable chair in good condition',
      price: 20,
      location: 'UofM',
    });

    component.selectedFile = null;

    component.create();

    expect(dialogRefSpy.close).toHaveBeenCalled();
    const payload = dialogRefSpy.close.calls.mostRecent().args[0] as CreateListingPayload;

    expect(payload.title).toBe('Chair');
    expect(payload.picture).toBeNull();
  });
});
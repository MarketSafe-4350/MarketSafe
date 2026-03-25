import { Injectable } from '@angular/core';

import { Offer } from './offers-api.service';

type OfferResolutionStatus = 'pending' | 'accepted' | 'declined';

@Injectable({ providedIn: 'root' })
export class BuyerOfferNotificationsService {
  private readonly snapshotKeyPrefix = 'buyer_offer_resolution_snapshot';
  private readonly seenKeyPrefix = 'buyer_offer_resolution_seen';

  syncResolvedOffers(offers: Offer[], userId: number | null): Set<number> {
    const snapshot = this.getSnapshot(userId);
    const nextSnapshot: Record<string, OfferResolutionStatus> = {};
    const seenIds = new Set(this.getSeenResolvedOfferIds(userId));

    for (const offer of offers) {
      const status: OfferResolutionStatus =
        offer.accepted === null
          ? 'pending'
          : offer.accepted
            ? 'accepted'
            : 'declined';
      const idKey = String(offer.id);
      nextSnapshot[idKey] = status;

      if (status !== 'pending' && snapshot[idKey] !== status) {
        seenIds.delete(offer.id);
      }
    }

    localStorage.setItem(this.snapshotKey(userId), JSON.stringify(nextSnapshot));
    localStorage.setItem(this.seenKey(userId), JSON.stringify([...seenIds]));
    return this.getUnseenResolvedOfferIds(offers, userId);
  }

  getUnseenResolvedOfferIds(offers: Offer[], userId: number | null): Set<number> {
    const seenIds = new Set(this.getSeenResolvedOfferIds(userId));
    const unseenIds = new Set<number>();

    for (const offer of offers) {
      if (offer.accepted !== null && !seenIds.has(offer.id)) {
        unseenIds.add(offer.id);
      }
    }

    return unseenIds;
  }

  markResolvedOffersSeen(offerIds: number[], userId: number | null): void {
    if (offerIds.length === 0) {
      return;
    }

    const seenIds = new Set(this.getSeenResolvedOfferIds(userId));
    for (const offerId of offerIds) {
      seenIds.add(offerId);
    }

    localStorage.setItem(this.seenKey(userId), JSON.stringify([...seenIds]));
  }

  private getSnapshot(userId: number | null): Record<string, OfferResolutionStatus> {
    try {
      const rawValue = localStorage.getItem(this.snapshotKey(userId));
      if (!rawValue) {
        return {};
      }

      return JSON.parse(rawValue) as Record<string, OfferResolutionStatus>;
    } catch {
      return {};
    }
  }

  private getSeenResolvedOfferIds(userId: number | null): number[] {
    try {
      const rawValue = localStorage.getItem(this.seenKey(userId));
      if (!rawValue) {
        return [];
      }

      const items = JSON.parse(rawValue) as number[];
      return items
        .map((item) => Number(item))
        .filter((item) => Number.isFinite(item));
    } catch {
      return [];
    }
  }

  private snapshotKey(userId: number | null): string {
    return `${this.snapshotKeyPrefix}:${userId ?? 'anonymous'}`;
  }

  private seenKey(userId: number | null): string {
    return `${this.seenKeyPrefix}:${userId ?? 'anonymous'}`;
  }
}

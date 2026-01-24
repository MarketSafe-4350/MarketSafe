# MarketSafe

## Team Members

| Name                             | GitHub Username | Email                   |
| -------------------------------- | --------------- | ----------------------- |
| Fidelio Ciandy                   | FidelioC        | ciandyf@myumanitoba.ca  |
| Farah Hegazi                     | Farahheg        | hegazif@myumanitoba.ca  |
| Michael King                     | MichaelKing1619 | kingm4@myumanitoba.ca   |
| Mohamed, Mohamed Youssef Mohamed | lMolMol         | mohammym@myumanitoba.ca |
| Thomas Awad                      | tomtom4343      | awadt@myumanitoba.ca    |

## Project Summary and Vision

MarketSafe is about creating a safe and reliable marketplace for students at the University of Manitoba.

It is intended to **help students buy and sell items with others from the same university in a way that feels comfortable and trustworthy**. Many students use online marketplaces to find textbooks, furniture, electronics, and other everyday items, but open platforms can feel risky or unreliable. This marketplace gives students a space where they know the people they are interacting with are also part of the University of Manitoba. The project supports simple actions such as posting items for sale, browsing available listings, sending offers, and keeping track of past activity. It also allows students to share feedback based on their experiences, which helps build trust and encourages fair behavior.

MarketSafe makes buying and selling easier, safer, and more convenient while supporting a stronger sense of trust within the the student community.

## Core Functional Features

1. [Account & Authentication system](#1-account--authentication-system)
2. [Marketplace Listings](#2-marketplace-listings)
3. [Send Offer](#3-send-offer)
4. [Rating](#4-rating)
5. [Search](#5-search)

## Technologies

- **Frontend**: Angular
- **Backend/ Server**: Python FastAPI
- **DB**: MySQL

## User Stories & Acceptance Criteria

#### 1. Account & Authentication system

- As a user (with a University of Manitoba domain email), I want to be able to create a secure account so that I can safely access the platform and its features.
  - Priority: High | Estimates: 5 days
  - Acceptance test:
    - Users can create an account, with authenticated UofM email.
- As a user I want to be able to log in and log out of my account so that my account remains protected and accessible only to me.
  - Priority: High : Estimates: 4 days
  - Acceptance test:
    - Users can login and logout, with authenticated UofM email.

- As a user, I want to be able to access my user profile so that I can view my personal account information.
  - Priority: High | Estimates: 3 days
  - Acceptance test:
    - Users can access their user profile and view their information.

#### 2. Marketplace Listings

- As a user, I want to be able to post a new listing so that I can offer items or services to other users on the marketplace.
  - Priority: High | Estimates: 4 days
  - Acceptance test:
    - Users can post new listings to the marketplace.

- As a user, I want to be able to see all marketplace listings so that I can browse and find items or services I am interested in.
  - Priority: High | Estimates: 4 days
  - Acceptance test:
    - Users can see all the marketplace listings that have been posted by other users.
- As a seller, I want to be able to delete my own listing so that I can remove items or services that are no longer available.
  - Priority: High | Estimates: 4 days
  - Acceptance test:
    - Sellers can delete their own listings.
    - Users can’t see deleted listings.

- As a user, I want to be able to comment on a listing so that I can ask questions or communicate with the listing owner.
  - Priority: High | Estimates: 4 days
  - Acceptance test:
    - Users can comment and reply to each other’s comments.

#### 3. Send Offer

- As a buyer, I want to be able to send an offer so that I can propose a price or terms to the seller for a listing I am interested in.
  - Priority: High | Estimates: 4 days
  - Acceptance test:
    - Buyers can send offers with a price and location to meet.

- As a seller, I want to be notified when I receive an offer so that I can respond in a timely manner.
  - Priority: High | Estimates: 4 days
  - Acceptance test:
    - Seller should get a notification when they get an offer from buyers.

- As a seller, I want to be able to either accept or decline an offer so that I can manage negotiations and decide the best outcome.
  - Priority: High | Estimates: 4 days
  - Acceptance test:
    - Sellers can decline or accept the offer.

- As a seller, when I accept an offer, I want my listing to be marked as sold (archived) so that it is no longer available to other buyers.
  - Priority: High | Estimates: 4 days
  - Acceptance test:
    - Users can only see items that are available on the market.

#### 4. Rating

- As a buyer, I want to be able to give a rating to a seller to share my experience and make the marketplace more reliable.
  - Priority: Medium | Estimates: 3 days
  - Acceptance test:
    - Users can give ratings to share their experience.

- As a user, I want to be able to see other users’ ratings so that I can make informed decisions.
  - Priority: Medium | Estimates: 3 days
  - Acceptance test:
    - Users can see other users’ ratings.

- As a user, I want to be able to see my own rating to understand how others perceive my profile.
  - Priority: Medium | Estimates: 2 days
  - Acceptance test:
    - Users can see their own rating.

#### 5. Search

- As a user, I want to be able to search through listing so I can quickly find specific items.
  - Priority: Medium | Estimates: 2 days
  - Acceptance test:
    - Users can search for specific items.

- As a user, I want to be able to filter listings through tags to narrow down results.
  - Priority: Medium | Estimates: 2 days
  - Acceptance test:
    - Users can filter through tags to search for items.

- As a user, I want to be able to sort marketplace listings to customize the order of my listings view.
  - Priority: Medium | Estimates: 2 days
  - Acceptance test:
    - Users can sort the marketplace listings.

## Others

- [MarketSafe Wiki](https://github.com/MarketSafe-4350/MarketSafe/wiki)
  - Consist of design diagrams & meeting minutes.

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
3. [Send Offer](#3-send-an-offer)
4. [Rating](#4-rating)
5. [Search](#5-search)

## Technologies

- **Frontend**: Angular
- **Backend/ Server**: Python FastAPI
- **DB**: MySQL

## Others

- [How To Contribute](./docs/CONTRIBUTING.md)
- [MarketSafe Wiki](https://github.com/MarketSafe-4350/MarketSafe/wiki)
  - Consist of design diagrams & meeting minutes.
- [Project Proposal Presentation](https://www.canva.com/design/DAG-yAiONts/6fduYGLEpoFRmz69pPE8Bw/view?utm_content=DAG-yAiONts&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=hfe609d86c8)
- [ER Diagram](./docs/ERDiagram-MarketSafe.png)

## User Stories & Acceptance Criteria

#### 1. Account & Authentication System

##### User Story: Account Registration

As a user (with a University of Manitoba domain email), I want to be able to create a secure account so that I can safely access the platform and its features.

- Priority: High
- Estimate: 5 days

###### Acceptance Criteria

- AC1  
  Given I am on the registration page,  
  When I enter a valid @umanitoba.ca email and a valid password,  
  Then I should be able to submit the registration form successfully.

- AC2  
  Given I have submitted a valid University of Manitoba email,  
  When the registration is complete,  
  Then I should receive an email verification message.

- AC3  
  Given I receive the verification email,  
  When I click the verification link within the valid time period,  
  Then my account should be activated.

- AC4  
  Given I try to register with an email that is not in the University of Manitoba domain,  
  Then I should see an error indicating that only University of Manitoba email addresses are permitted.

###### Definition of Done (DoD)

- Secure account creation with a University of Manitoba email is implemented
- Email verification flow is functional and verified
- All Acceptance Criteria are met and testable
- Code is peer-reviewed and merged into the main branch
- Automated and/or manual tests are written and passing
- Feature is tested in a QA or staging environment with no regressions
- No critical defects remain open

##### User Story: Login & Logout

As a user, I want to be able to log in and log out of my account so that my account remains protected and accessible only to me.

- Priority: High
- Estimate: 4 days

###### Acceptance Criteria

- AC1  
  Given I am on the login page,  
  When I enter valid credentials (email and password) and submit,  
  Then I should be logged in and taken to my account/dashboard.

- AC2  
  Given I am on the login page,  
  When I enter incorrect credentials and submit,  
  Then I should see an error message indicating invalid login.

- AC3  
  Given I am logged in,  
  When I choose to log out,  
  Then I should be logged out and redirected to the public/landing page.

- AC4  
  Given I am logged out,  
  When I navigate back to a protected page,  
  Then I should be prompted to log in again.

###### Definition of Done (DoD)

- User can successfully log in with valid credentials
- User receives an appropriate error on invalid login attempts
- Logout functionality fully works and redirects user appropriately
- All Acceptance Criteria are met and verified
- Code has been peer-reviewed and merged into the main branch
- Automated or manual tests are written and passing
- Feature is tested in QA or staging and does not break existing functionality
- No critical bugs remain open
- Relevant documentation is updated
- Product Owner has reviewed and accepted the story

##### User Story: View Profile

As a user, I want to be able to access my user profile so that I can view my personal account information.

- Priority: High
- Estimate: 3 days

###### Acceptance Criteria

- AC1  
  Given I am logged in,
  When I navigate to the profile page,
  Then I should see my personal account information (e.g., name, email, profile details).

- AC2  
  Given I am on the profile page,  
  When the profile information loads,  
  Then all displayed data should reflect the latest saved user information.

- AC3  
  Given I am not logged in,  
  When I attempt to access the profile page,  
  Then I should be redirected to the login page.

###### Definition of Done (DoD)

- Profile access feature is implemented and working
- All Acceptance Criteria are met and verified
- Code is peer-reviewed and merged into the main branch
- Automated and/or manual tests are written and passing
- Functionality is tested in QA or staging with no regressions
- No critical defects remain open
- Relevant documentation is updated
- Product Owner has reviewed and accepted the story

#### 2. Marketplace Listings

##### User Story: Create Listing

As a user, I want to be able to post a new listing so that I can offer items or services to other users on the marketplace.

- Priority: High
- Estimate: 4 days

###### Acceptance Criteria

- AC1  
  Given I am a logged-in user,  
  When I submit a new listing with all required information,  
  Then the listing should be created successfully and appear in the marketplace listings

- AC2  
  Given I am a logged-in user,  
  When I attempt to submit a new listing with missing required information,  
  Then the system should display validation errors and the listing should not be created.

###### Definition of Done (DoD)

- All Acceptance Criteria are met
- Required fields are validated
- Listing is stored persistently in the database
- Newly created listing is visible without page refreshing
- Only authenticated users can create listings
- No unhandled errors occur
- Features are accessible through the UI

##### User Story: View Listings

As a user, I want to be able to see all marketplace listings so that I can browse and find items or services I am interested in.

- Priority: High
- Estimate: 4 days

###### Acceptance Criteria

- AC1  
  Given I am a logged-in user,  
  When I navigate to the Marketplace page,  
  Then I should see all active listings posted by other users.

- AC2  
  Given I am a logged-in user
  When a listing has been deleted by its owner
  Then that listing should not be visible in the marketplace listings

###### Definition of Done (DoD)

- All Acceptance Criteria are met
- Only active (non-deleted) listings are displayed
- Listings load correctly after page refresh
- Marketplace page is accessible only to authenticated users
- Empty state is shown when no listings exist

##### User Story: Delete Listing

As a seller, I want to be able to delete my own listing so that I can remove items or services that are no longer available.

- Priority: High
- Estimate: 4 days

###### Acceptance Criteria

- AC1  
  Given I am a logged-in seller
  And I am the owner of a listing
  When I choose to delete my listing
  Then the listing should be removed from the marketplace
  And other users should no longer be able to view it

- AC2  
  Given I am a logged-in user
  And I am not the owner of a listing
  When I attempt to delete that listing
  Then the system should prevent the action

###### Definition of Done (DoD)

- All acceptance criteria are met
- Only the listing owner can delete the listing
- Deleted listings are not visible to any user
- Deletion persists in the database
- Unauthorized deletion attempts are blocked
- UI updates immediately after deletion

##### User Story: Comments

As a user, I want to be able to comment on a listing so that I can ask questions or communicate with the listing owner.

- Priority: High
- Estimate: 4 days

###### Acceptance Criteria

- AC1  
  Given I am a logged-in user,  
  When I submit a comment on a listing,  
  Then the comment should be displayed under the listing.

- AC2  
  Given I am a logged-in user
  And I am viewing a listing with existing comments
  When I reply to a comment
  Then my reply should be displayed under the correct comment thread

###### Definition of Done (DoD)

- Only authenticated users can comment or reply
- Comments and replies are saved in the database
- Comments show correct user and timestamp
- Replies are linked to the correct parent comment
- Comments persist after page refresh

#### 3. Send an Offer

##### User Story: Send Offer

As a buyer, I want to be able to send an offer so that I can propose a price or terms to the seller.

- Priority: High
- Estimate: 4 days

###### Acceptance Criteria

- AC1  
  Given I am a buyer viewing an active listing
  When I submit an offer with valid details
  Then the offer should be successfully sent to the seller

- AC2  
  Given an offer has been sent
  When the seller views their offers
  Then the offer details should be visible for review

###### Definition of Done (DoD)

- Buyer can create and submit an offer for an active listing
- Offer is stored and associated with the correct listing and buyer
- Seller can view the submitted offer
- Acceptance Criteria are met
- Code is reviewed and merged
- Feature is tested and does not break existing functionality

##### User Story: Offer Notification

As a seller, I want to be notified when I receive an offer so that I can respond in a timely manner.

- Priority: High
- Estimate: 4 days

###### Acceptance Criteria

- AC1  
  Given I am a seller with an active listing
  When a buyer submits an offer on my listing
  Then I should receive a notification about the new offer

- AC2  
  Given I receive an offer notification
  When I open the notification
  Then I should be able to view the offer details

###### Definition of Done (DoD)

- Seller receives a notification when a new offer is submitted
- Notification links to the relevant offer or listing
- Acceptance Criteria are met
- Code is reviewed and merged
- Feature is tested and does not break existing functionality

##### User Story: Accept or Decline Offer

As a seller, I want to be able to either accept or decline an offer so that I can manage negotiations and decide the best outcome.

- Priority: High
- Estimate: 4 days

###### Acceptance Criteria

- AC1  
  Given I am a seller viewing offers on my listing
  When I choose to accept an offer
  Then the offer status should be updated to Accepted

- AC2  
  Given I am a seller viewing offers on my listing
  When I choose to decline an offer
  Then the offer status should be updated to Declined

###### Definition of Done (DoD)

- Seller can accept or decline an offer from the listing interface
- Offer status is correctly updated and persisted
- Acceptance Criteria are met
- Code is reviewed and merged
- Feature is tested and does not break existing functionality

##### User Story: Mark Listing as Sold

As a seller, when I accept an offer, I want my listing to be marked as sold (archived) so that it is no longer available to other buyers

- Priority: High
- Estimate: 4 days

###### Acceptance Criteria

- AC1  
  Given that I am a seller with an active listing
  When I accept an offer on that listing
  Then the listing status should change to Sold

- AC2  
  Given a listing is marked as Sold
  When other buyers browse or search listings
  Then the sold listing should not appear in the available listings

###### Definition of Done (DoD)

- Listing status is updated to Sold after offer acceptance
- Sold listing is no longer visible to buyers in search or browse views
- Acceptance Criteria are met
- Code is reviewed and merged
- Feature is tested and does not break existing functionality

#### 4. Rating

##### User Story: Rate Seller

As a buyer, I want to be able to give a rating to a seller to share my experience and make the marketplace more reliable.

- Priority: Medium
- Estimate: 3 days

###### Acceptance Criteria

- AC1  
  Given I am a buyer who has completed a transaction with a seller
  When I submit a rating with valid details
  Then the rating should be successfully saved

- AC2  
  Given a rating has been submitted
  When the seller’s profile is viewed
  Then the rating should be visible

###### Definition of Done (DoD)

- Buyer can submit a rating for a seller after a completed transaction
- Rating is saved and associated with the correct seller
- Acceptance Criteria are met
- Code is reviewed and merged
- Feature is tested and does not break existing functionality

##### User Story: View Ratings

As a user, I want to be able to see other users’ ratings so that I can make informed decisions.

- Priority: Medium
- Estimate: 3 days

###### Acceptance Criteria

- AC1  
  Given I am viewing another user’s profile
  When the profile loads
  Then the user’s rating should be visible

- AC2  
  Given a user has received one or more ratings
  When their rating is displayed
  Then it should reflect the submitted ratings accurately

###### Definition of Done (DoD)

- User ratings are visible on a user’s profile
- Displayed rating reflects stored rating data
- Acceptance Criteria are met
- Code is reviewed and merged
- Feature is tested and does not break existing functionality

##### User Story: View Own Rating

As a user, I want to be able to see my own rating to understand how others perceive my profile.

- Priority: Medium
- Estimate: 2 days

###### Acceptance Criteria

- AC1  
  Given I am viewing my profile
  When the profile loads
  Then my rating should be visible

- AC2  
  Given I have received one or more ratings
  When my rating is displayed
  Then it should reflect all submitted ratings accurately

###### Definition of Done (DoD)

- User can view their own rating on their profile
- Displayed rating reflects stored rating data
- Acceptance Criteria are met
- Code is reviewed and merged
- Feature is tested and does not break existing functionality

#### 5. Search

##### User Story: Search Listings

As a user, I want to be able to search through listing so I can quickly find specific items.

- Priority: Medium
- Estimate: 2 days

###### Acceptance Criteria

- AC1  
  Given I am viewing the marketplace listings
  When I enter a keyword into the search bar
  Then listings matching the keyword should be displayed

- AC2  
  Given I am viewing the marketplace listings
  When I clear or change the search keyword
  Then the displayed listings should update accordingly

###### Definition of Done (DoD)

- Users can search listings using keywords
- Search results update correctly based on input
- Acceptance Criteria are met
- Code is reviewed and merged
- Feature is tested and does not break existing functionality

##### User Story: Filter by Tags

As a user, I want to be able to filter listings through tags to narrow down results.

- Priority: Medium
- Estimate: 2 days

###### Acceptance Criteria

- AC1  
  Given I am viewing marketplace listings
  When I select one or more tags
  Then only listings with the selected tags should be displayed

- AC2  
  Given I am viewing marketplace listings
  When I remove a selected tag
  Then the listings should update to reflect the change

###### Definition of Done (DoD)

- Users can filter listings by tags
- Multiple tags can be applied and removed
- Acceptance Criteria are met
- Code is reviewed and merged
- Feature is tested and does not break existing functionality

##### User Story: Sort Listings

As a user, I want to be able to sort marketplace listings to customize the order of my listings view.

- Priority: Medium
- Estimate: 2 days

###### Acceptance Criteria

- AC1  
  Given I am viewing marketplace listings
  When I select a sorting option
  Then the listings should be reordered accordingly

- AC2  
  Given I am viewing marketplace listings
  When I change the sorting option
  Then the listings should update to reflect the new order

###### Definition of Done (DoD)

- Users can sort listings using available options
- Sorting is applied consistently
- Acceptance Criteria are met
- Code is reviewed and merged
- Feature is tested and does not break existing functionality

---

_Note: we use ChatGPT to improve our acceptance criteria and definition of done_

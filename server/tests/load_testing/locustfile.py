import os
import time
from locust import HttpUser, task, between


class LoadTest(HttpUser):
    wait_time = between(5, 7)
    host = "http://localhost:8000"

    def on_start(self):
        self.account_id = os.getenv("LOADTEST_ACCOUNT_ID", "1")
        self.seller_id = os.getenv("LOADTEST_SELLER_ID", self.account_id)
        self.listing_id = os.getenv("LOADTEST_LISTING_ID")
        self.offer_id = os.getenv("LOADTEST_OFFER_ID")
        self.verify_token = os.getenv("LOADTEST_VERIFY_TOKEN")

        response = self.client.post("/accounts/login", json={
            "email": "loadtest@umanitoba.ca",
            "password": "LoadTestPass123"
        }, name="/accounts/login")

        if response.status_code != 200:
            raise Exception(f"Login failed: {response.status_code} {response.text}")

        data = response.json()
        token = data["access_token"]
        self.client.headers.update({
            "Authorization": f"Bearer {token}"
        })

    #~~~~~~~~~~~~~~~~~~
    # Offer
    #~~~~~~~~~~~~~~~~~~

    @task(3)
    def sent_offers(self):
        self.client.get("/accounts/offers/sent", name="/accounts/offers/sent")

    @task(2)
    def received_offers(self):
        self.client.get("/accounts/offers/received", name="/accounts/offers/received")

    @task(2)
    def pending_received(self):
        self.client.get(
            "/accounts/offers/received/pending",
            name="/accounts/offers/received/pending"
        )

    @task(2)
    def unseen_received(self):
        self.client.get(
            "/accounts/offers/received/unseen",
            name="/accounts/offers/received/unseen"
        )

    @task(2)
    def my_account(self):
        self.client.get("/accounts/me", name="/accounts/me")

    @task(2)
    def pending_sent(self):
        self.client.get(
            "/accounts/offers/sent/pending",
            name="/accounts/offers/sent/pending"
        )

    #~~~~~~~~~~~~~~~~~~
    # Get Listings
    #~~~~~~~~~~~~~~~~~~

    @task(5)
    def all_listings(self):
        self.client.get("/listings", name="/listings")

    @task(4)
    def my_listings(self):
        self.client.get("/listings/me", name="/listings/me")

    @task(5)
    def search_listings(self):
        self.client.get("/listings/search?q=test", name="/listings/search")

    @task(3)
    def seller_listings(self):
        self.client.get(
            f"/listings/seller/{self.seller_id}",
            name="/listings/seller/{seller_id}"
        )

    @task(2)
    def listing_comments(self):
        if not self.listing_id:
            return
        self.client.get(
            f"/listings/{self.listing_id}/comments",
            name="/listings/{listing_id}/comments"
        )

    @task(2)
    def listing_ratings(self):
        if not self.listing_id:
            return
        self.client.get(
            f"/listings/{self.listing_id}/ratings",
            name="/listings/{listing_id}/ratings [GET]"
        )

    # -------------------------
    # Create Listing
    # -------------------------

    @task(0)
    def create_listing(self):
        unique = int(time.time() * 1000)
        self.client.post(
            "/listings",
            json={
                "title": f"Load Test Listing {unique}",
                "description": "Listing created during load testing",
                "price": 99.99,
                "location": "Winnipeg",
                "image_url": None
            },
            name="/listings [POST]"
        )

    @task(0)
    def create_listing_comment(self):
        if not self.listing_id:
            return
        unique = int(time.time() * 1000)
        self.client.post(
            f"/listings/{self.listing_id}/comments",
            json={
                "content": f"Load test comment {unique}"
            },
            name="/listings/{listing_id}/comments [POST]"
        )

    @task(1)
    def rate_listing(self):
        if not self.listing_id:
            return
        self.client.post(
            f"/listings/{self.listing_id}/ratings",
            json={
                "transaction_rating": 5
            },
            name="/listings/{listing_id}/ratings [POST]"
        )

    @task(0)
    def create_listing_with_upload(self):
        image_path = os.getenv("LOADTEST_IMAGE_PATH")
        if not image_path:
            return

        with open(image_path, "rb") as img:
            self.client.post(
                "/listings/upload",
                data={
                    "title": "Uploaded listing",
                    "description": "Created via Locust upload",
                    "price": "125.50",
                    "location": "Winnipeg",
                },
                files={"image": ("loadtest.jpg", img, "image/jpeg")},
                name="/listings/upload"
            )

    @task(0)
    def delete_listing(self):
        if not self.listing_id:
            return
        self.client.delete(
            f"/listings/{self.listing_id}",
            name="/listings/{listing_id} [DELETE]"
        )

    @task(1)
    def account_by_id(self):
        self.client.get(
            f"/accounts/id/{self.account_id}",
            name="/accounts/id/{account_id}"
        )

    @task(1)
    def signup_account(self):
        unique = int(time.time() * 1000)
        self.client.post(
            "/accounts",
            json={
                "email": f"loadtest_signup_{unique}@umanitoba.ca",
                "password": "LoadTestPass123",
                "fname": "Load",
                "lname": "Tester",
            },
            name="/accounts"
        )

    @task(1)
    def verify_email(self):
        if not self.verify_token:
            return
        self.client.get(
            f"/accounts/verify-email?auth_token={self.verify_token}",
            name="/accounts/verify-email"
        )

    @task(1)
    def offers_by_listing(self):
        if not self.listing_id:
            return
        self.client.get(
            f"/listings/{self.listing_id}/offer",
            name="/listings/{listing_id}/offer [GET]"
        )

    @task(1)
    def create_offer(self):
        if not self.listing_id:
            return
        self.client.post(
            f"/listings/{self.listing_id}/offer",
            json={
                "offered_price": 99.99,
                "location_offered": "Winnipeg"
            },
            name="/listings/{listing_id}/offer [POST]"
        )

    @task(1)
    def get_offer_by_id(self):
        if not self.offer_id:
            return
        self.client.get(
            f"/offers/{self.offer_id}",
            name="/offers/{offer_id}"
        )

    @task(1)
    def mark_offer_seen(self):
        if not self.offer_id:
            return
        self.client.patch(
            f"/offers/{self.offer_id}/seen",
            name="/offers/{offer_id}/seen"
        )

    @task(1)
    def resolve_offer(self):
        if not self.offer_id:
            return
        self.client.post(
            f"/offers/{self.offer_id}/resolve?accepted=true",
            name="/offers/{offer_id}/resolve"
        )

    @task(1)
    def delete_offer(self):
        if not self.offer_id:
            return
        self.client.delete(
            f"/offers/{self.offer_id}",
            name="/offers/{offer_id} [DELETE]"
        )




# import os
# import time
# from locust import HttpUser, task, between


# class OfferUser(HttpUser):
#     wait_time = between(5, 7)
#     host = "http://localhost:8000"

#     def on_start(self):
#         self.account_id = os.getenv("LOADTEST_ACCOUNT_ID", "1")
#         self.listing_id = os.getenv("LOADTEST_LISTING_ID")
#         self.offer_id = os.getenv("LOADTEST_OFFER_ID")
#         self.verify_token = os.getenv("LOADTEST_VERIFY_TOKEN")

#         response = self.client.post(
#             "/accounts/login",
#             json={
#                 "email": "loadtest@umanitoba.ca",
#                 "password": "LoadTestPass123",
#             },
#             name="/accounts/login",
#         )

#         if response.status_code != 200:
#             raise Exception(
#                 f"Login failed: {response.status_code} {response.text}"
#             )

#         data = response.json()
#         token = data.get("access_token")
#         if not token:
#             raise Exception(f"No access_token returned: {data}")

#         self.client.headers.update({
#             "Authorization": f"Bearer {token}"
#         })

#     # -------------------------
#     # Account routes
#     # -------------------------

#     @task(3)
#     def my_account(self):
#         self.client.get("/accounts/me", name="/accounts/me")

#     @task(1)
#     def account_by_id(self):
#         self.client.get(
#             f"/accounts/id/{self.account_id}",
#             name="/accounts/id/{account_id}",
#         )

#     @task(0)
#     def signup_account(self):
#         unique = int(time.time() * 1000)
#         self.client.post(
#             "/accounts",
#             json={
#                 "email": f"loadtest_signup_{unique}@umanitoba.ca",
#                 "password": "LoadTestPass123",
#                 "fname": "Load",
#                 "lname": "Tester",
#             },
#             name="/accounts",
#         )

#     @task(0)
#     def verify_email(self):
#         if not self.verify_token:
#             return

#         self.client.get(
#             f"/accounts/verify-email?auth_token={self.verify_token}",
#             name="/accounts/verify-email",
#         )

#     # -------------------------
#     # Offer routes already present
#     # -------------------------

#     @task(4)
#     def sent_offers(self):
#         self.client.get("/accounts/offers/sent", name="/accounts/offers/sent")

#     @task(4)
#     def received_offers(self):
#         self.client.get(
#             "/accounts/offers/received",
#             name="/accounts/offers/received",
#         )

#     @task(2)
#     def pending_received(self):
#         self.client.get(
#             "/accounts/offers/received/pending",
#             name="/accounts/offers/received/pending",
#         )

#     @task(2)
#     def unseen_received(self):
#         self.client.get(
#             "/accounts/offers/received/unseen",
#             name="/accounts/offers/received/unseen",
#         )

#     # -------------------------
#     # Missing offer routes
#     # -------------------------

#     @task(2)
#     def pending_sent(self):
#         self.client.get(
#             "/accounts/offers/sent/pending",
#             name="/accounts/offers/sent/pending",
#         )

#     @task(1)
#     def offers_by_listing(self):
#         if not self.listing_id:
#             return

#         self.client.get(
#             f"/listings/{self.listing_id}/offer",
#             name="/listings/{listing_id}/offer [GET]",
#         )

#     @task(0)
#     def create_offer(self):
#         if not self.listing_id:
#             return

#         self.client.post(
#             f"/listings/{self.listing_id}/offer",
#             json={
#                 "offered_price": 99.99,
#                 "location_offered": "Winnipeg",
#             },
#             name="/listings/{listing_id}/offer [POST]",
#         )

#     @task(1)
#     def get_offer_by_id(self):
#         if not self.offer_id:
#             return

#         self.client.get(
#             f"/offers/{self.offer_id}",
#             name="/offers/{offer_id}",
#         )

#     @task(0)
#     def mark_offer_seen(self):
#         if not self.offer_id:
#             return

#         self.client.patch(
#             f"/offers/{self.offer_id}/seen",
#             name="/offers/{offer_id}/seen",
#         )

#     @task(0)
#     def resolve_offer(self):
#         if not self.offer_id:
#             return

#         self.client.post(
#             f"/offers/{self.offer_id}/resolve?accepted=true",
#             name="/offers/{offer_id}/resolve",
#         )

#     @task(0)
#     def delete_offer(self):
#         if not self.offer_id:
#             return

#         self.client.delete(
#             f"/offers/{self.offer_id}",
#             name="/offers/{offer_id} [DELETE]",
#         )


# # from locust import HttpUser, task

# # from locust import HttpUser, task, between

# # class OfferUser(HttpUser):
# #     wait_time = between(1, 3)
# #     host = "http://localhost:8000"

# #     def on_start(self):
# #         response = self.client.post("/accounts/login", json={
# #             "email": "loadtest@umanitoba.ca",
# #             "password": "LoadTestPass123"
# #         })
# #         token = response.json()["access_token"]
# #         self.client.headers.update({
# #             "Authorization": f"Bearer {token}"
# #         })

# #     @task(4)
# #     def sent_offers(self):
# #         self.client.get("/accounts/offers/sent")

# #     @task(4)
# #     def received_offers(self):
# #         self.client.get("/accounts/offers/received")

# #     @task(2)
# #     def pending_received(self):
# #         self.client.get("/accounts/offers/received/pending")

# #     @task(2)
# #     def unseen_received(self):
# #         self.client.get("/accounts/offers/received/unseen")

    

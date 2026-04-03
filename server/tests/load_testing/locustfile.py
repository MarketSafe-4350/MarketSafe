import os
import time
import requests
from locust import HttpUser, task, between, events
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../.env"))

API_PORT = os.getenv("API_PORT", "8000")
BASE_URL = f"http://localhost:{API_PORT}"

shared_data = {
    "seller_account_id": None,
    "load_tester_account_id": None,
    "listing_id": None,
    "token": None,
}

@events.test_start.add_listener
def setup_test(environment, **kwargs):
    print("Running Load Test Setup")

    unique = int(time.time() * 1000)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~
    # Create dummy seller account
    # ~~~~~~~~~~~~~~~~~~~~~~~~~
    seller_email = f"seller_{unique}@umanitoba.ca"

    r = requests.post(f"{BASE_URL}/accounts", json={
        "email": seller_email,
        "password": "LoadTestPass123",
        "fname": "Seller",
        "lname": "User",
    })
    r.raise_for_status()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~
    # Log into dummy seller account
    # ~~~~~~~~~~~~~~~~~~~~~~~~~

    r = requests.post(f"{BASE_URL}/accounts/login", json={
        "email": seller_email,
        "password": "LoadTestPass123"
    })
    seller_token = r.json()["access_token"]
    seller_headers = {"Authorization": f"Bearer {seller_token}"}

    r = requests.get(
        f"{BASE_URL}/accounts/me",
        headers={"Authorization": f"Bearer {seller_token}"}
    )
    r.raise_for_status()
    shared_data["seller_account_id"] = r.json()["id"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~
    # Create dummy listing
    # ~~~~~~~~~~~~~~~~~~~~~~~~~
    r = requests.post(
        f"{BASE_URL}/listings",
        headers=seller_headers,
        json={
            "title": f"Load Test Listing {unique}",
            "description": "Dummy listing",
            "price": 9999,
            "location": "Winnipeg",
            "image_url": None,
        },
    )
    r.raise_for_status()

    listing_data = r.json()
    shared_data["listing_id"] = listing_data["id"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~
    # Create dummy load tester account
    # ~~~~~~~~~~~~~~~~~~~~~~~~~
    load_tester_email = f"loadtest_{unique}@umanitoba.ca"

    r = requests.post(f"{BASE_URL}/accounts", json={
        "email": load_tester_email,
        "password": "LoadTestPass123",
        "fname": "Load",
        "lname": "Tester",
    })
    r.raise_for_status()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~
    # Login dummy load tester
    # ~~~~~~~~~~~~~~~~~~~~~~~~~
    r = requests.post(f"{BASE_URL}/accounts/login", json={
        "email": load_tester_email,
        "password": "LoadTestPass123"
    })
    r.raise_for_status()

    load_tester_token = r.json()["access_token"]
    shared_data["token"] = load_tester_token

    # Get load tester account ID
    r = requests.get(
        f"{BASE_URL}/accounts/me",
        headers={"Authorization": f"Bearer {load_tester_token}"}
    )
    r.raise_for_status()

    shared_data["load_tester_account_id"] = r.json()["id"]

    print("Setup complete:")
    print("Listing ID:", shared_data["listing_id"])
    print("Load tester account ID:", shared_data["load_tester_account_id"])



class LoadTest(HttpUser):
    wait_time = between(3, 5) # ~300 req/min with 20 users; lower values = more requests per minute
    host = BASE_URL

    def on_start(self):
        self.listing_id = shared_data["listing_id"]
        self.offer_id = None
        self.verify_token = None
        self.account_id = shared_data["load_tester_account_id"]
        self.seller_id = shared_data["seller_account_id"]

        self.client.headers.update({
            "Authorization": f"Bearer {shared_data['token']}"
        })


    # ~~~~~~~~~~~~~~~~~~~~~~~~~
    # Account Routes
    # ~~~~~~~~~~~~~~~~~~~~~~~~~

    # DONE IN SETUP
    @task(0)
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

    # get account
    @task(2)
    def my_account(self):
        self.client.get("/accounts/me", name="/accounts/me")

    # SKIP verify email
    @task(0)
    def verify_email(self):
        if not self.verify_token:
            return
        self.client.get(
            f"/accounts/verify-email?auth_token={self.verify_token}",
            name="/accounts/verify-email"
        )
    
    # get account by id
    @task(1)
    def account_by_id(self):
        self.client.get(
            f"/accounts/id/{self.account_id}",
            name="/accounts/id/{account_id}"
        )
    

    # ~~~~~~~~~~~~~~~~~~~~~~~~~
    # Listing Routes
    # ~~~~~~~~~~~~~~~~~~~~~~~~~

    # get all listings
    @task(5)
    def all_listings(self):
        self.client.get("/listings", name="/listings")

    # get my listings
    @task(4)
    def my_listings(self):
        self.client.get("/listings/me", name="/listings/me")

    # search listings
    @task(5)
    def search_listings(self):
        self.client.get("/listings/search?q=test", name="/listings/search")

    # get listings by seller
    @task(3)
    def seller_listings(self):
        self.client.get(
            f"/listings/seller/{self.seller_id}",
            name="/listings/seller/{seller_id}"
        )

    # DONE IN SETUP
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
    # SKIP create listing with upload
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
    # SKIP delete listing
    @task(0)
    def delete_listing(self):
        if not self.listing_id:
            return
        self.client.delete(
            f"/listings/{self.listing_id}",
            name="/listings/{listing_id} [DELETE]"
        )
    
    # get listing comment
    @task(2)
    def listing_comments(self):
        if not self.listing_id:
            return
        self.client.get(
            f"/listings/{self.listing_id}/comments",
            name="/listings/{listing_id}/comments"
        )

    # SKIP rate listing
    @task(0)
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

    # get listing rating
    @task(2)
    def listing_ratings(self):
        if not self.listing_id:
            return
        self.client.get(
            f"/listings/{self.listing_id}/ratings",
            name="/listings/{listing_id}/ratings [GET]"
        )

    # create listing comment
    @task(1)
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
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~
    # Offer Routes
    # ~~~~~~~~~~~~~~~~~~~~~~~~~

    # SKIP create offer - 'ConflictError' thrown if more than one offer sent from same user
    @task(0)
    def create_offer(self):
        if not self.listing_id:
            return
        self.client.post(
            f"/listings/{self.listing_id}/offer",
            json={
                "offered_price": 888,
                "location_offered": "UC"
            },
            name="/listings/{listing_id}/offer [POST]"
        )

    # get offer by id
    @task(1)
    def get_offer_by_id(self):
        if not self.offer_id:
            return
        self.client.get(
            f"/offers/{self.offer_id}",
            name="/offers/{offer_id}"
        )

    # get offers by listing
    @task(1)
    def offers_by_listing(self):
        if not self.listing_id:
            return
        self.client.get(
            f"/listings/{self.listing_id}/offer",
            name="/listings/{listing_id}/offer [GET]"
        )

    # get offers sent
    @task(3)
    def sent_offers(self):
        self.client.get("/accounts/offers/sent", name="/accounts/offers/sent")

    # get offers received
    @task(2)
    def received_offers(self):
        self.client.get("/accounts/offers/received", name="/accounts/offers/received")

    # get pending received offers
    @task(2)
    def pending_received(self):
        self.client.get(
            "/accounts/offers/received/pending",
            name="/accounts/offers/received/pending"
        )

    # get unseen received offers
    @task(2)
    def unseen_received(self):
        self.client.get(
            "/accounts/offers/received/unseen",
            name="/accounts/offers/received/unseen"
        )

    # get pending sent offers
    @task(2)
    def pending_sent(self):
        self.client.get(
            "/accounts/offers/sent/pending",
            name="/accounts/offers/sent/pending"
        )

    # mark offer seen
    @task(1)
    def mark_offer_seen(self):
        if not self.offer_id:
            return
        self.client.patch(
            f"/offers/{self.offer_id}/seen",
            name="/offers/{offer_id}/seen"
        )
    
    # resolve offer
    @task(1)
    def resolve_offer(self):
        if not self.offer_id:
            return
        self.client.post(
            f"/offers/{self.offer_id}/resolve?accepted=true",
            name="/offers/{offer_id}/resolve"
        )

    # delete offer
    @task(1)
    def delete_offer(self):
        if not self.offer_id:
            return
        self.client.delete(
            f"/offers/{self.offer_id}",
            name="/offers/{offer_id} [DELETE]"
        )

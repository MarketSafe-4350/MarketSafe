from fastapi import Request
from src.media_storage import MediaStorageUtility

def get_media_storage(request: Request) -> MediaStorageUtility:
    """
      Returns the single MediaStorageUtility instance initialized at app startup.

      Expected setup in create_app():
          app.state.media_storage = MediaStorageUtility(...)
      """
    return request.app.state.media_storage
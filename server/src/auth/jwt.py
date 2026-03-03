import jwt

from src.api.errors.api_error import ApiError
from src.config import SECRET_KEY


def get_user_id_from_token(token: str) -> int:
    if not token:
        raise ApiError(status_code=401, message="Missing authentication auth_token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")

        if not user_id:
            raise ApiError(status_code=401, message="Invalid auth_token payload")

        return int(user_id)

    except jwt.ExpiredSignatureError:
        raise ApiError(status_code=401, message="Token has expired")

    except jwt.InvalidTokenError:
        raise ApiError(status_code=401, message="Invalid auth_token")

    except ValueError:
        raise ApiError(status_code=401, message="Invalid user ID in auth_token")

from abc import ABC, abstractmethod
from src.db import DBUtility
from src.domain_models import Comment
from typing import Optional, List


class CommentDB(ABC):
    """
    Contract for Comment table persistence.

    IMPORTANT DESIGN RULES:
    - This layer is responsible ONLY for database access.
    - It does NOT contain business logic (authorization, ownership rules, etc.).
    - It does NOT decide HTTP responses.
    - It does NOT decide authentication logic.
    - It only performs CRUD + clearly-scoped queries.

    Return conventions:
    - Methods that fetch a single row return Optional[Comment]:
        None means "not found".
    - Methods that fetch multiple rows return List[Comment]:
        empty list is valid and MUST be returned when no results exist.

    ======================================================
    ERROR CONTRACT
    ======================================================

    All implementations MUST follow this error policy:

    1. Parameter validation failures:
       -> Raise ValidationError

    2. Record not found (when contract requires raising):
       -> Raise CommentNotFoundError

    3. Query-level SQL failures:
       -> Raise DatabaseQueryError

    4. Connection-level failures:
       -> Raised by DBUtility as DatabaseUnavailableError
          (Implementations should NOT catch/re-wrap those)
    """

    def __init__(self, db: DBUtility) -> None:
        """
        DBUtility must be injected to:
        - Reuse connection pooling
        - Enable mocking in tests
        - Maintain separation of concerns
        """
        self._db = db

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------
    @abstractmethod
    def add(self, comment: Comment) -> Comment:
        """
        Insert a new comment row.

        Expected behavior:
        - Insert comment into database.
        - Return created Comment with generated ID and created_date.
        - Must raise exception on:
            - listing_id or author_id does not exist (FK violation)
            - Database is unavailable
            - Any SQL error occurs

        Constraints/ notes:
        - created_date is DB-managed (DEFAULT CURRENT_TIMESTAMP)
        - Never returns None

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # READ
    # --------------------------------------------------

    @abstractmethod
    def get_by_id(self, comment_id: int) -> Optional[Comment]:
        """
        Fetch comment by primary key.

        Expected behavior:
        - Return Comment if a row exists.
        - Return None if no row is found.
        - Must NOT raise exception for "not found".
        - Must raise exception is a database error occurs

        Raises:
            ValidationError:
                - comment_id is not int
            DatabaseQueryError:
                - SQL failure
            DatabaseUnavailableError:
                - Connection failure
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_listing_id(self, listing_id: int) -> List[Comment]:
        """
        Fetch all comments for a specific listing.

        Expected behavior:
        - Return empty list if no comments exist.
        - Must raise exception if a database error occurs.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_author_id(self, author_id: int) -> List[Comment]:
        """
        Fetch all comments written by a specific account.

        Expected behavior:
        - Return empty list if none exist.
        - Must raise exception if a database error occurs.

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    @abstractmethod
    def update_body(self, comment_id: int, body: str | None) -> None:
        """
        Update the body of a comment.

        Expected behavior:
        - Update comment body.
        - If comment_id does not exist:
              raise CommentNotFoundError
        - Must raise exception on SQL errors.

        Constraints:
        - body may be None (DB allows NULL).

        Raises:
            ValidationError
            CommentNotFoundError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    @abstractmethod
    def remove(self, comment_id: int) -> bool:
        """
        Delete a comment by ID.

        Expected behavior:
        - Return True if row was deleted.
        - Return False if no row matched the ID.
        - Must NOT raise exception for "not found".
        - Must raise exception for database errors.

        Constraints / notes:
        - Higher layers must enforce ownership/authorization before calling this
        (only the author/ admin can remove a comment).

        Raises:
            ValidationError
            DatabaseQueryError
            DatabaseUnavailableError
        """
        raise NotImplementedError

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.db.comment import CommentDB
from src.utils import Validation

from src.domain_models import Account, Listing, Comment


class ICommentManager(ABC):
    """
    Comment business layer contract (manager/service).

    Responsibilities:
        - Contains business logic and orchestration.
        - Calls persistence layer (CommentDB, optionally ListingDB/AccountDB if needed).
        - Decides which domain errors to raise (404/409/422/etc.).
        - Does NOT write SQL.

    IMPORTANT:
        - This manager enforces business rules such as:
            - who is allowed to comment (e.g., authenticated users only)
            - any policy like "no comments on sold listings" (if you want that rule)
            - (optional) only allow deleting your own comments, etc.
        - It should NOT enforce DB concerns (FKs/SQL), those remain in CommentDB.
    """

    def __init__(self, comment_db: CommentDB) -> None:
        Validation.require_not_none(comment_db, "comment_db")
        self._comment_db = comment_db

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    @abstractmethod
    def create_comment(
        self, actor: Account, listing: Listing, body: str | None
    ) -> Comment:
        """
        PURPOSE:
            Create a new comment for a listing.

        EXPECTED BEHAVIOR:
            - Validate actor/listing are present and persisted (ids exist).
            - Enforce commenting rules (business rules), e.g.:
                - actor must be authenticated / verified
                - cannot comment on sold listings
            - Create Comment(domain object)
            - Persist via comment_db.add(comment)

        INPUTS:
            actor: Account (the author)
            listing: Listing (the target listing)
            body: str | None  (nullable per schema)

        RETURNS:
            Created Comment (with generated id and created_date)

        RAISES (typical):
            - ValidationError
            - UnapprovedBehaviorError (can't let not verified user comments)
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # READ
    # --------------------------------------------------

    @abstractmethod
    def get_comment_by_id(self, comment_id: int) -> Optional[Comment]:
        """
        PURPOSE:
            Fetch a comment by ID.

        EXPECTED BEHAVIOR:
            - Return Comment if exists
            - Return None if not found (do not raise for missing)

        IMPLEMENTATION NOTES:
            - Calls comment_db.get_by_id(comment_id)

        RETURNS:
            Comment | None

        RAISES (typical):
            - ValidationError: if comment_id is invalid
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_comments_for_listing(self, listing_id: int) -> List[Comment]:
        """
        PURPOSE:
            List all comments on a listing.

        EXPECTED BEHAVIOR:
            - Return empty list if none exist.

        IMPLEMENTATION NOTES:
            - Calls comment_db.get_by_listing_id(listing_id)

        RETURNS:
            list[Comment]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    @abstractmethod
    def list_comments_for_author(self, author_id: int) -> List[Comment]:
        """
        PURPOSE:
            List all comments created by a specific author.

        IMPLEMENTATION NOTES:
            - Calls comment_db.get_by_author_id(author_id)

        RETURNS:
            list[Comment]

        RAISES (typical):
            - ValidationError
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError
    
    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    @abstractmethod
    def update_comment_body(self, actor: Account, comment_id: int, body: str | None) -> Comment:
        """
        PURPOSE:
            Update the body of a comment.

        EXPECTED BEHAVIOR:
            - Enforce business rules:
                - only the author (or admin) can edit
            - Calls comment_db.update_body(comment_id, body)

        IMPLEMENTATION NOTES:
            - Calls comment_db.update_body(comment_id, body)
            
        RETURNS:
            Updated Comment (re-read)

        RAISES (typical):
            - ValidationError
            - CommentNotFoundError
            - UnapprovedBehaviorError (if actor cannot edit)
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------
    @abstractmethod
    def delete_comment(self, actor: Account, comment_id: int) -> bool:
        """
        PURPOSE:
            Delete a comment.

        EXPECTED BEHAVIOR:
            - Enforce business rules:
                - only the author (or admin) can delete
            - Return True if deleted, False if not found (idempotent delete)
            - Calls comment_db.remove(comment_id)

        IMPLEMENTATION NOTES:
            - Calls comment_db.remove(comment_id)
            
        RETURNS:
            bool

        RAISES (typical):
            - ValidationError
            - UnapprovedBehaviorError (if actor cannot delete)
            - DatabaseUnavailableError / DatabaseQueryError
        """
        raise NotImplementedError
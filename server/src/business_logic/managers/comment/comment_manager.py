from src.business_logic.managers.comment import ICommentManager 
from src.db.comment import CommentDB
from src.domain_models import Account, Listing, Comment
from src.utils import Validation, ValidationError, UnapprovedBehaviorError, CommentNotFoundError

from typing_extensions import override
from typing import List, Optional

class CommentManager(ICommentManager):
    """
    Comment manager implementation.

    Responsibilities:
    - Orchestrate listing operations (no SQL here).
    - Validate inputs at the manager boundary (optional but recommended).
    
    Dependencies:
    - comment_db: CommentDB (required)
    
    Notes:
    - Assumes routing/service layer already authenticated the user (JWT -> Account).
    - Enforces authorization + business rules here.
    - Delegates persistence to CommentDB.
    """

    def __init__(self, comment_db: CommentDB) -> None:
        super().__init__(comment_db)

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------
    @override
    def create_comment(self, actor: Account, listing: Listing, comment: Comment) -> Comment:
        Validation.require_not_none(actor, "actor")
        Validation.require_not_none(listing, "listing")
        Validation.require_not_none(comment, "comment")

        # Persisted checks
        if actor.id is None:
            raise ValidationError("actor must be persisted (actor.id is None).")
        if listing.id is None:
            raise ValidationError("listing must be persisted (listing.id is None).")

        if comment.id is not None:
            raise ValidationError("comment must be new (comment.id must be None on create).")

        if int(comment.author_id) != int(actor.id):
            raise UnapprovedBehaviorError("Cannot create a comment on behalf of another user.")

        if int(comment.listing_id) != int(listing.id):
            raise ValidationError("comment.listing_id must match listing.id.")

        # verified required
        if not bool(actor.verified):
            raise UnapprovedBehaviorError("Only verified users can create comments.")

        # cannot comment on sold listings
        if bool(listing.is_sold):
            raise UnapprovedBehaviorError("Cannot comment on a sold listing.")

        return self._comment_db.add(comment)


    # --------------------------------------------------
    # READ
    # --------------------------------------------------
    @override
    def get_comment_by_id(self, comment_id: int) -> Optional[Comment]:
        comment_id = Validation.require_int(comment_id, "comment_id")
        return self._comment_db.get_by_id(comment_id)

    @override
    def list_comments_for_listing(self, listing_id: int) -> List[Comment]:
        listing_id = Validation.require_int(listing_id, "listing_id")
        return self._comment_db.get_by_listing_id(listing_id)

    @override
    def list_comments_for_author(self, author_id: int) -> List[Comment]:
        author_id = Validation.require_int(author_id, "author_id")
        return self._comment_db.get_by_author_id(author_id)
    
    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------
    @override
    def update_comment_body(self, actor: Account, comment: Comment) -> Comment:
        Validation.require_not_none(actor, "actor")
        Validation.require_not_none(comment, "comment")

        if actor.id is None:
            raise ValidationError("actor must be persisted (actor.id is None).")

        if comment.id is None:
            raise ValidationError("comment must be persisted (comment.id is None).")

        # verified users only
        if not bool(actor.verified):
            raise UnapprovedBehaviorError("Only verified users can edit comments.")

        # Authorization: only author can edit
        if int(comment.author_id) != int(actor.id):
            raise UnapprovedBehaviorError("Only the comment author can edit this comment.")

        # Persist update
        self._comment_db.update_body(comment.id, comment.body)

        # Return refreshed version
        updated = self._comment_db.get_by_id(comment.id)
        if updated is None:
            raise CommentNotFoundError(
                message=f"Comment not found after update for id: {comment.id}",
                details={"comment_id": comment.id},
            )

        return updated
    
    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------
    @override
    def delete_comment(self, actor: Account, comment_id: int) -> bool:
        Validation.require_not_none(actor, "actor")
        comment_id = Validation.require_int(comment_id, "comment_id")

        if actor.id is None:
            raise ValidationError("actor must be persisted (actor.id is None).")

        if not bool(actor.verified):
            raise UnapprovedBehaviorError("Only verified users can delete comments.")

        existing = self._comment_db.get_by_id(comment_id)
        if existing is None:
            # idempotent delete
            return False

        # Authorization: only author can delete
        if int(existing.author_id) != int(actor.id):
            raise UnapprovedBehaviorError("Only the comment author can delete this comment.")

        return self._comment_db.remove(comment_id)

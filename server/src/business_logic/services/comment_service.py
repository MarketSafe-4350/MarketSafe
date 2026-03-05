from src.business_logic.managers.comment import ICommentManager
from src.business_logic.managers.listing import IListingManager
from src.business_logic.managers.account import IAccountManager
from src.domain_models import Comment, Account, Listing

from typing import List
from dataclasses import dataclass


@dataclass(frozen=True)
class CommentWithAuthor:
    comment: Comment
    author: Account


class CommentService:
    """Service class for handling comment-related business logic"""

    def __init__(
        self,
        comment_manager: ICommentManager,
        listing_manager: IListingManager,
        account_manager: IAccountManager,
    ):
        self._comment_manager = comment_manager
        self._listing_manager = listing_manager
        self._account_manager = account_manager

    def get_all_comments_listing(self, listing_id: int) -> List[CommentWithAuthor]:
        """
        Get all comments for a listing, including author info.
        """
        comments: List[Comment] = self._comment_manager.list_comments_for_listing(
            listing_id=listing_id
        )

        unique_author_ids: set[int] = {c.author_id for c in comments}

        authors_by_id: dict[int, Account] = {
            author_id: self._account_manager.get_account_by_id(account_id=author_id)
            for author_id in unique_author_ids
        }

        return [
            CommentWithAuthor(comment=c, author=authors_by_id.get(c.author_id))
            for c in comments
        ]

    def create_comment(
        self, actor_id: int, listing_id: int, comment: Comment
    ) -> CommentWithAuthor:
        """
        Create a comment and return it with author info.
        """
        actor: Account = self._account_manager.get_account_by_id(account_id=actor_id)

        listing: Listing = self._listing_manager.get_listing_by_id(
            listing_id=listing_id
        )

        created_comment: Comment = self._comment_manager.create_comment(
            actor=actor,
            listing=listing,
            comment=comment,
        )

        return CommentWithAuthor(
            comment=created_comment,
            author=actor,
        )

from src.business_logic.managers.comment import ICommentManager
from src.business_logic.managers.listing import IListingManager
from src.business_logic.managers.account import IAccountManager
from src.domain_models import Comment, Account, Listing

from typing import List


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

    def get_all_comments_listing(self, listing_id: int) -> List[Comment]:
        """get all comments for a listing

        Args:
            listing_id (int): listing id

        Returns:
            List[Comment]: list of comments
        """
        return self._comment_manager.list_comments_for_listing(listing_id=listing_id)

    def create_comment(
        self, actor_id: int, listing_id: int, comment: Comment
    ) -> Comment:
        """create a comment for a listin

        Args:
            actor_id (int): author who created the comment
            listing_id (int): listing id for the comment
            comment (Comment): Comment object, to insert

        Returns:
            Comment: Created comment
        """
        actor: Account = self._account_manager.get_account_by_id(account_id=actor_id)
        listing: Listing = self._listing_manager.get_listing_by_id(
            listing_id=listing_id
        )
        return self._comment_manager.create_comment(
            actor=actor, listing=listing, comment=comment
        )

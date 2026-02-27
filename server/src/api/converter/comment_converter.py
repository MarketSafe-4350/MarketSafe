from pydantic import BaseModel
from src.domain_models.comment import Comment
from src.domain_models.account import Account


class CommentCreate(BaseModel):
    """Data model for creating a new comment."""

    body: str | None = None

    def to_domain(self, listing_id: int, author_id: int) -> Comment:
        return Comment(
            listing_id=listing_id,
            author_id=author_id,
            body=self.body,
        )


class CommentResponse(BaseModel):
    """Data model for comment response."""

    id: int | None = None
    listing_id: int
    author_id: int
    author_name: str
    body: str | None = None
    created_date: str | None = None

    @staticmethod
    def from_domain(comment: Comment, author: Account) -> "CommentResponse":
        return CommentResponse(
            id=comment.id,
            listing_id=comment.listing_id,
            author_id=comment.author_id,
            author_name=author.fname + " " + author.lname,
            body=comment.body,
            created_date=(
                comment.created_date.isoformat() if comment.created_date else None
            ),
        )

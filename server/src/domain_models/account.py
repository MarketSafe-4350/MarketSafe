from src.utils import ValidationError, UnapprovedBehaviorError, Validation


class Account:
    """
    Domain Entity: Account

    This class represents the `account` table in the database.

    Design Decisions (SoftEng 2):

    1. Encapsulation
       - All internal state is stored in variables prefixed with `_`.
       - Python does not enforce true private access like Java.
       - Instead, `_variable` is used by convention to signal
         that these fields must not be modified directly.

    2. No Double Underscore (__)
       - We intentionally avoid `__variable` (name mangling).
       - It is unnecessary for domain entities and complicates debugging.
       - `_variable` is the Pythonic standard for protected fields.

    3. Controlled Access
       - Read access is provided using `@property`.
       - Mutation is allowed only through domain methods.
       - This mirrors Java's private fields + public methods approach.

    4. Invariants
       - Email is normalized and validated.
       - Names cannot be empty.
       - Password must already be hashed before reaching this entity.
       - ID can only be assigned once (after DB persistence).

    5. Keyword-Only Parameters (*)
       - Parameters after `*` must be passed explicitly by name.
       - This prevents accidental parameter misordering.
       - Improves clarity and safety in object creation.
    """

    def __init__(
            self,
            email: str,
            password: str,
            fname: str,
            lname: str,
            *,
            account_id: int | None = None,
            verified: bool = False,
    ):
        # Internal state (protected by convention)
        self._id = account_id
        self._email = Validation.valid_email(email)
        self._password = Validation.require_str(password, "password")
        self._fname = Validation.require_str(fname, "fname")
        self._lname = Validation.require_str(lname, "lname")
        self._verified = Validation.is_boolean(verified, "verified")

    # ==============================
    # ID (read-only, may be None before DB insert)
    # ==============================

    @property
    def id(self):
        return self._id

    def mark_persisted(self, account_id: int):
        if account_id is None:
            raise ValidationError("Account ID cannot be None.")
        if self._id is not None:
            raise UnapprovedBehaviorError(
                "Account ID has already been assigned."
            )
        self._id = account_id

    # ==============================
    # EMAIL (NOT NULL)
    # ==============================

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._email = Validation.valid_email(value)

    # ==============================
    # PASSWORD (NOT NULL)
    # ==============================

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = Validation.require_str(value, "password")

    # ==============================
    # FIRST NAME (NOT NULL)
    # ==============================

    @property
    def fname(self):
        return self._fname

    @fname.setter
    def fname(self, value):
        self._fname = Validation.require_str(value, "fname")

    # ==============================
    # LAST NAME (NOT NULL)
    # ==============================

    @property
    def lname(self):
        return self._lname


    @lname.setter
    def lname(self, value):
        self._lname = Validation.require_str(value, "lname")

    # ==============================
    # VERIFIED (NOT NULL)
    # ==============================

    @property
    def verified(self):
        return self._verified

    @verified.setter
    def verified(self, value):
        if value is None:
            raise ValidationError("verified cannot be None")
        self._verified = value

    # ==============================
    # DEBUG REPRESENTATION
    # ==============================

    def __repr__(self):
        return (
            f"Account(id={self._id}, "
            f"email={self._email!r}, "
            f"fname={self._fname!r}, "
            f"lname={self._lname!r}, "
            f"verified={self._verified})"
        )
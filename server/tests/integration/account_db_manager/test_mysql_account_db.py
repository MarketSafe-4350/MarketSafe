from __future__ import annotations

import unittest
from uuid import uuid4

from src.db.account.mysql import MySQLAccountDB
from src.domain_models import Account
from src.utils import AccountAlreadyExistsError, AccountNotFoundError

from tests.helpers.integration_db_session import acquire, get_db, release


class TestMySQLAccountDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._session = acquire(timeout_s=60)
        cls._db = get_db()
        cls._account_db = MySQLAccountDB(cls._db)

    @classmethod
    def tearDownClass(cls) -> None:
        release(cls._session, remove_volumes=False)

    def setUp(self) -> None:
        # Keep tests isolated: clean the table before each test
        self._account_db.clear_db()

    def _new_account(self) -> Account:
        uniq = uuid4().hex[:10]
        return Account(
            email=f"test_{uniq}@example.com",
            password="pass",
            fname="Test",
            lname="User",
            verified=False,
        )

    def test_add_and_get_by_id(self) -> None:
        acc = self._new_account()
        created = self._account_db.add(acc)

        self.assertIsNotNone(created.id)
        self.assertEqual(created.email, acc.email)

        fetched = self._account_db.get_by_id(created.id)
        self.assertIsNotNone(fetched)
        assert fetched is not None

        self.assertEqual(fetched.email, acc.email)
        self.assertEqual(fetched.fname, acc.fname)
        self.assertEqual(fetched.lname, acc.lname)
        self.assertEqual(bool(fetched.verified), False)

    def test_get_by_email(self) -> None:
        acc = self._new_account()
        created = self._account_db.add(acc)

        fetched = self._account_db.get_by_email(created.email)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.email, created.email)

    def test_add_duplicate_email_raises(self) -> None:
        acc = self._new_account()
        self._account_db.add(acc)

        with self.assertRaises(AccountAlreadyExistsError):
            self._account_db.add(acc)

    def test_set_verified_by_id(self) -> None:
        acc = self._new_account()
        created = self._account_db.add(acc)

        self._account_db.set_verified(created.id, True)

        updated = self._account_db.get_by_id(created.id)
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(bool(updated.verified), True)

    def test_set_verified_by_email(self) -> None:
        acc = self._new_account()
        created = self._account_db.add(acc)

        self._account_db.set_verified_by_email(created.email, True)

        updated = self._account_db.get_by_email(created.email)
        self.assertIsNotNone(updated)
        assert updated is not None
        self.assertEqual(bool(updated.verified), True)

    def test_set_verified_missing_raises(self) -> None:
        with self.assertRaises(AccountNotFoundError):
            self._account_db.set_verified(999999, True)

        with self.assertRaises(AccountNotFoundError):
            self._account_db.set_verified_by_email("missing@example.com", True)

    def test_remove(self) -> None:
        acc = self._new_account()
        created = self._account_db.add(acc)

        deleted = self._account_db.remove(created.id)
        self.assertTrue(deleted)

        deleted_again = self._account_db.remove(created.id)  # type: ignore[arg-type]
        self.assertFalse(deleted_again)
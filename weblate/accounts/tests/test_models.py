# Copyright © Michal Čihař <michal@weblate.org>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests fors models (AuditLog and Profile)."""

from __future__ import annotations

from django.test import SimpleTestCase, TestCase
from django.test.utils import override_settings

from weblate.accounts.models import AuditLog, Profile
from weblate.auth.models import User


class AuditLogTestCase(SimpleTestCase):
    def test_address_ipv4(self) -> None:
        audit = AuditLog(address="127.0.0.1")
        self.assertEqual(audit.shortened_address, "127.0.0.0")

    def test_address_ipv6_local(self) -> None:
        audit = AuditLog(address="fe80::54c2:1234:5678:90ab")
        self.assertEqual(audit.shortened_address, "fe80::")

    def test_address_ipv6_weblate(self) -> None:
        audit = AuditLog(address="2a01:4f8:c0c:a84b::1")
        self.assertEqual(audit.shortened_address, "2a01:4f8:c0c::")

    def test_address_blank(self) -> None:
        audit = AuditLog()
        self.assertEqual(audit.shortened_address, "")

class ProfileCommitNameTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testuser",
            full_name="Test User",
            email="test@example.com",
        )
        self.profile = self.user.profile

    @override_settings(
        PRIVATE_COMMIT_NAME_TEMPLATE="{site_title} user {id}",
        SITE_TITLE="WeblateTest",
    )
    def test_get_site_commit_name(self) -> None:
        name = self.profile.get_site_commit_name()
        self.assertEqual(name, f"WeblateTest user {self.user.id}")

    @override_settings(
        PRIVATE_COMMIT_NAME_TEMPLATE="Anonymous {username}",
        PRIVATE_COMMIT_NAME_OPT_IN=False,
    )
    def test_get_commit_name_forced(self) -> None:
        self.profile.commit_name = ""
        self.assertEqual(self.profile.get_commit_name(), "Anonymous testuser")

    @override_settings(
        PRIVATE_COMMIT_NAME_TEMPLATE="Anonymous {id}",
        PRIVATE_COMMIT_NAME_OPT_IN=True,
    )
    def test_get_commit_name_opt_in(self) -> None:
        self.profile.commit_name = ""
        self.assertEqual(self.profile.get_commit_name(), "Test User")

    def test_get_commit_name_explicit(self) -> None:
        self.profile.commit_name = "Custom Name"
        self.assertEqual(self.profile.get_commit_name(), "Custom Name")

    @override_settings(
        PRIVATE_COMMIT_NAME_TEMPLATE="Anon",
        PRIVATE_COMMIT_NAME_OPT_IN=False,
    )
    def test_bot_naming_remains_visible(self) -> None:
        self.user.is_bot = True
        self.user.save()
        self.profile.commit_name = ""
        self.assertEqual(self.profile.get_commit_name(), "Test User")

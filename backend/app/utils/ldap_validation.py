"""LDAP / Active Directory validation utilities.

Provides:
- NT credential verification via simple bind
- Recursive AD group membership check (OID 1.2.840.113556.1.4.1941)
- User group listing

Requires: ldap3==2.9.1, pyasn1==0.5.1

Includes MD4 patch for Python 3.13+ / OpenSSL 3.0+ environments where
hashlib no longer exposes MD4.
"""

from __future__ import annotations

import hashlib
import logging
import struct

import ldap3
from ldap3 import NTLM, Connection, Server

from app.config import settings

logger = logging.getLogger(__name__)

_AD_HOST = "ap.corning.com"
_AD_DOMAIN = "corning.com"
_AD_SEARCH_BASE = "DC=ap,DC=corning,DC=com"

# ---------------------------------------------------------------------------
# MD4 pure-Python fallback (Python 3.13 + OpenSSL 3.0 removed MD4)
# ---------------------------------------------------------------------------

_has_native_md4 = False
try:
    hashlib.new("md4")
    _has_native_md4 = True
except ValueError:
    pass


def _left_rotate(n: int, b: int) -> int:
    return ((n << b) | (n >> (32 - b))) & 0xFFFFFFFF


class _MD4:
    """Pure-Python MD4 implementation (RFC 1320).

    Only used as fallback when OpenSSL does not provide MD4.
    """

    block_size = 64
    digest_size = 16

    def __init__(self, data: bytes = b""):
        self._buffer = b""
        self._count = 0
        self._state = (0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476)
        if data:
            self.update(data)

    def update(self, data: bytes) -> None:
        self._buffer += data
        self._count += len(data)
        while len(self._buffer) >= 64:
            self._process_block(self._buffer[:64])
            self._buffer = self._buffer[64:]

    def digest(self) -> bytes:
        # Padding
        msg = self._buffer
        msg_len = self._count
        msg += b"\x80"
        msg += b"\x00" * ((55 - msg_len % 64) % 64)
        msg += struct.pack("<Q", msg_len * 8)

        state = self._state
        for i in range(0, len(msg), 64):
            block = msg[i : i + 64]
            a, b, c, d = state

            x = struct.unpack("<16I", block)

            # Round 1
            def _f(x_val, y, z):
                return (x_val & y) | (~x_val & z)

            for i_r in [0, 4, 8, 12]:
                a = _left_rotate((a + _f(b, c, d) + x[i_r]) & 0xFFFFFFFF, 3)
                d = _left_rotate((d + _f(a, b, c) + x[i_r + 1]) & 0xFFFFFFFF, 7)
                c = _left_rotate((c + _f(d, a, b) + x[i_r + 2]) & 0xFFFFFFFF, 11)
                b = _left_rotate((b + _f(c, d, a) + x[i_r + 3]) & 0xFFFFFFFF, 19)

            # Round 2
            def _g(x_val, y, z):
                return (x_val & y) | (x_val & z) | (y & z)

            for i_r in [0, 1, 2, 3]:
                a = _left_rotate(
                    (a + _g(b, c, d) + x[i_r] + 0x5A827999) & 0xFFFFFFFF, 3
                )
                d = _left_rotate(
                    (d + _g(a, b, c) + x[i_r + 4] + 0x5A827999) & 0xFFFFFFFF, 5
                )
                c = _left_rotate(
                    (c + _g(d, a, b) + x[i_r + 8] + 0x5A827999) & 0xFFFFFFFF, 9
                )
                b = _left_rotate(
                    (b + _g(c, d, a) + x[i_r + 12] + 0x5A827999) & 0xFFFFFFFF, 13
                )

            # Round 3
            def _h(x_val, y, z):
                return x_val ^ y ^ z

            for i_r in [0, 2, 1, 3]:
                a = _left_rotate(
                    (a + _h(b, c, d) + x[i_r] + 0x6ED9EBA1) & 0xFFFFFFFF, 3
                )
                d = _left_rotate(
                    (d + _h(a, b, c) + x[i_r + 8] + 0x6ED9EBA1) & 0xFFFFFFFF, 9
                )
                c = _left_rotate(
                    (c + _h(d, a, b) + x[i_r + 4] + 0x6ED9EBA1) & 0xFFFFFFFF, 11
                )
                b = _left_rotate(
                    (b + _h(c, d, a) + x[i_r + 12] + 0x6ED9EBA1) & 0xFFFFFFFF, 15
                )

            state = (
                (state[0] + a) & 0xFFFFFFFF,
                (state[1] + b) & 0xFFFFFFFF,
                (state[2] + c) & 0xFFFFFFFF,
                (state[3] + d) & 0xFFFFFFFF,
            )

        return struct.pack("<4I", *state)

    def hexdigest(self) -> str:
        return self.digest().hex()

    def _process_block(self, block: bytes) -> None:
        a, b, c, d = self._state

        x = struct.unpack("<16I", block)

        def _f(x_val, y, z):
            return (x_val & y) | (~x_val & z)

        for i_r in [0, 4, 8, 12]:
            a = _left_rotate((a + _f(b, c, d) + x[i_r]) & 0xFFFFFFFF, 3)
            d = _left_rotate((d + _f(a, b, c) + x[i_r + 1]) & 0xFFFFFFFF, 7)
            c = _left_rotate((c + _f(d, a, b) + x[i_r + 2]) & 0xFFFFFFFF, 11)
            b = _left_rotate((b + _f(c, d, a) + x[i_r + 3]) & 0xFFFFFFFF, 19)

        def _g(x_val, y, z):
            return (x_val & y) | (x_val & z) | (y & z)

        for i_r in [0, 1, 2, 3]:
            a = _left_rotate(
                (a + _g(b, c, d) + x[i_r] + 0x5A827999) & 0xFFFFFFFF, 3
            )
            d = _left_rotate(
                (d + _g(a, b, c) + x[i_r + 4] + 0x5A827999) & 0xFFFFFFFF, 5
            )
            c = _left_rotate(
                (c + _g(d, a, b) + x[i_r + 8] + 0x5A827999) & 0xFFFFFFFF, 9
            )
            b = _left_rotate(
                (b + _g(c, d, a) + x[i_r + 12] + 0x5A827999) & 0xFFFFFFFF, 13
            )

        def _h(x_val, y, z):
            return x_val ^ y ^ z

        for i_r in [0, 2, 1, 3]:
            a = _left_rotate(
                (a + _h(b, c, d) + x[i_r] + 0x6ED9EBA1) & 0xFFFFFFFF, 3
            )
            d = _left_rotate(
                (d + _h(a, b, c) + x[i_r + 8] + 0x6ED9EBA1) & 0xFFFFFFFF, 9
            )
            c = _left_rotate(
                (c + _h(d, a, b) + x[i_r + 4] + 0x6ED9EBA1) & 0xFFFFFFFF, 11
            )
            b = _left_rotate(
                (b + _h(c, d, a) + x[i_r + 12] + 0x6ED9EBA1) & 0xFFFFFFFF, 15
            )

        self._state = (
            (self._state[0] + a) & 0xFFFFFFFF,
            (self._state[1] + b) & 0xFFFFFFFF,
            (self._state[2] + c) & 0xFFFFFFFF,
            (self._state[3] + d) & 0xFFFFFFFF,
        )


def _md4_hash(data: bytes) -> bytes:
    """Compute MD4 hash, using native OpenSSL if available, else pure-Python."""
    if _has_native_md4:
        return hashlib.new("md4", data).digest()
    return _MD4(data).digest()


# Monkey-patch hashlib for ldap3 NTLM support if MD4 is missing
if not _has_native_md4:
    _original_hashlib_new = hashlib.new

    def _patched_hashlib_new(name: str, *args, **kwargs):
        if name.lower() == "md4":

            class _MD4Wrapper:
                digest_size = 16
                block_size = 64

                def __init__(self, data: bytes = b""):
                    self._impl = _MD4(data)

                def update(self, data: bytes):
                    self._impl.update(data)

                def digest(self):
                    return self._impl.digest()

                def hexdigest(self):
                    return self._impl.hexdigest()

            if args:
                return _MD4Wrapper(args[0])
            return _MD4Wrapper()
        return _original_hashlib_new(name, *args, **kwargs)

    hashlib.new = _patched_hashlib_new  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# LDAP operations
# ---------------------------------------------------------------------------


def _get_server() -> Server:
    return Server(_AD_HOST, port=636, use_ssl=True, get_info=ldap3.ALL)


def check_account_and_password(account: str, password: str) -> bool:
    """Verify NT credentials via simple bind.

    Args:
        account: sAMAccountName (e.g. 'wangm44')
        password: User's domain password

    Returns:
        True if bind succeeds, False otherwise.
    """
    server = _get_server()
    user_dn = f"{_AD_DOMAIN}\\{account}"
    try:
        conn = Connection(
            server,
            user=user_dn,
            password=password,
            authentication=NTLM,
            auto_bind=True,
            read_only=True,
        )
        conn.unbind()
        return True
    except ldap3.core.exceptions.LDAPBindError:
        logger.debug("LDAP bind failed for %s", account)
        return False
    except Exception as exc:
        logger.error("LDAP connection error for %s: %s", account, exc)
        return False


def _get_service_connection() -> Connection:
    """Create an NTLM-authenticated connection using the service account."""
    server = _get_server()
    conn = Connection(
        server,
        user=settings.ldap_bind_dn,
        password=settings.ldap_bind_password,
        authentication=NTLM,
        auto_bind=True,
        read_only=True,
    )
    return conn


def check_ad_group_membership(username: str, required_group: str) -> bool:
    """Check if user is a member of the specified AD group (recursive).

    Uses OID 1.2.840.113556.1.4.1941 (LDAP_MATCHING_RULE_IN_CHAIN) for
    recursive group membership resolution.

    Args:
        username: sAMAccountName
        required_group: CN of the required group

    Returns:
        True if user is a member (direct or nested), False otherwise.
    """
    try:
        conn = _get_service_connection()
    except Exception as exc:
        logger.error("Failed to connect with service account: %s", exc)
        return False

    try:
        # First find the user's DN
        conn.search(
            search_base=_AD_SEARCH_BASE,
            search_filter=f"(sAMAccountName={username})",
            attributes=["distinguishedName"],
        )
        if not conn.entries:
            logger.warning("User %s not found in AD", username)
            return False

        user_dn = str(conn.entries[0].distinguishedName)

        # Now check recursive membership using LDAP_MATCHING_RULE_IN_CHAIN
        # OID 1.2.840.113556.1.4.1941
        search_filter = (
            f"(&(objectClass=group)(cn={required_group})"
            f"(member:1.2.840.113556.1.4.1941:={user_dn}))"
        )
        conn.search(
            search_base=_AD_SEARCH_BASE,
            search_filter=search_filter,
            attributes=["cn"],
        )

        return len(conn.entries) > 0
    except Exception as exc:
        logger.error("Group membership check failed for %s: %s", username, exc)
        return False
    finally:
        conn.unbind()


def get_user_groups(username: str) -> list[str]:
    """List all AD groups a user belongs to (recursive).

    Args:
        username: sAMAccountName

    Returns:
        List of group CNs the user belongs to.
    """
    try:
        conn = _get_service_connection()
    except Exception as exc:
        logger.error("Failed to connect with service account: %s", exc)
        return []

    try:
        # Find the user's DN
        conn.search(
            search_base=_AD_SEARCH_BASE,
            search_filter=f"(sAMAccountName={username})",
            attributes=["memberOf"],
        )
        if not conn.entries:
            logger.warning("User %s not found in AD", username)
            return []

        member_of = conn.entries[0].memberOf.values if conn.entries[0].memberOf else []

        # Extract CN from each DN
        groups = []
        for dn in member_of:
            parts = str(dn).split(",")
            for part in parts:
                if part.strip().upper().startswith("CN="):
                    groups.append(part.strip()[3:])
                    break

        return groups
    except Exception as exc:
        logger.error("Failed to get groups for %s: %s", username, exc)
        return []
    finally:
        conn.unbind()

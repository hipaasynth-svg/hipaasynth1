# HipAAsynth — Synthetic health data fairness testing for invisible populations.
# Copyright (C) 2026 HipAAsynth Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import hashlib


def compute_sha256(file_path):
    """Compute the SHA256 hex digest of a file."""
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except OSError as exc:
        raise RuntimeError(f"Failed to hash file: {file_path}") from exc
    return h.hexdigest()


def stable_seed_from_id(identifier, salt: int = 0) -> int:
    """
    Process-stable 32-bit seed derived from a string identifier.

    Python's built-in hash() is process-randomized unless PYTHONHASHSEED is
    pinned, which violates the determinism contract required by
    the determinism contract (results must be byte-identical across separate
    interpreter runs and across machines).

    This helper produces an identical 32-bit unsigned seed every time for
    the same (identifier, salt) pair, on any host, in any process.

    Args:
        identifier: Stable identifier string (e.g., patient_id).
        salt:       Optional integer salt mixed in via XOR before hashing.
                    Use to namespace seeds for different operations on the
                    same identifier (e.g., noise vs drift).

    Returns:
        A 32-bit unsigned integer suitable for seeding random.Random.
    """
    if not isinstance(identifier, (str, bytes)):
        identifier = str(identifier)
    if isinstance(identifier, str):
        identifier = identifier.encode("utf-8")

    salted = identifier + b"|" + str(int(salt)).encode("ascii")
    digest = hashlib.sha256(salted).digest()
    # Take the first 4 bytes as a big-endian unsigned 32-bit int.
    return int.from_bytes(digest[:4], "big")

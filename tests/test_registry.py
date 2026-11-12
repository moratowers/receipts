"""Every OpenTimestamps proof in registry/ matches the file it stamps, is anchored in Bitcoin, and points at the
block's real merkle root. The roots below were read from blockstream.info on 2026-11-12; any block explorer shows
the same values for these heights, so a reader can check them without trusting this file."""
import hashlib
import re
from pathlib import Path

import pytest
from opentimestamps.core.notary import BitcoinBlockHeaderAttestation
from opentimestamps.core.serialize import StreamDeserializationContext
from opentimestamps.core.timestamp import DetachedTimestampFile

REG = Path(__file__).resolve().parent.parent / "registry"

MERKLE_ROOTS = {  # height: (block time UTC, merkle root)
    971902: ("2026-10-17T20:02:55Z", "607098ed0dd23f6b4b640e4fdfb8c31a959763e10efbb919aa7697ede4028583"),
    971906: ("2026-10-17T20:45:01Z", "abb6f66e8d52247cad4e602933070348d813b027edfa74daf83b220c9668ba9f"),
    972850: ("2026-10-24T00:13:42Z", "bfb0efe3c54ef54dc8a7101d028b93e93be3b6e8e58fffd7ffd6cd5d27deb31c"),
    972852: ("2026-10-24T00:43:00Z", "c8a684f5814e05d6118ada0f38a8d440450ea1f611912c618a99c81dff39d394"),
    972858: ("2026-10-24T02:03:39Z", "db99b2da838f5847f99c5bb2cc60846df77746e98c571697f564029f5d5c797f"),
    972859: ("2026-10-24T02:04:00Z", "64ebf83a0e034011110fb94e78493e220ebbf52e3c99e80367c226e55f56e0d7"),
    972860: ("2026-10-24T02:08:18Z", "a36c5ae112ead9152d38c17912709cf131e7170f4617acbc6d35ad7a4f89bdc6"),
    972871: ("2026-10-24T03:42:03Z", "96023e29396199d7f998b73198fe082536fa2b29b84bd1f8307762231f94e59d"),
    972908: ("2026-10-24T10:02:17Z", "ddbe823c737d0b152f5ec98821a242bf42b77f8956524d6d0e7fe22e75b56b08"),
}

PROOFS = sorted(REG.rglob("*.ots"))


def _attestations(ots_path):
    with open(ots_path, "rb") as f:
        dt = DetachedTimestampFile.deserialize(StreamDeserializationContext(f))
    out = []
    for msg, att in dt.timestamp.all_attestations():
        if isinstance(att, BitcoinBlockHeaderAttestation):
            out.append((att.height, msg[::-1].hex()))
    return dt.file_digest, out


def test_there_are_24_proofs():
    assert len(PROOFS) == 24  # 21 digest files and 3 manifests


@pytest.mark.parametrize("ots", PROOFS, ids=lambda p: p.name)
def test_proof_matches_file_and_is_anchored_in_bitcoin(ots):
    digest, atts = _attestations(ots)
    target = ots.with_suffix("")
    assert hashlib.sha256(target.read_bytes()).digest() == digest
    assert atts, "proof is still pending: run `ots upgrade` on it"
    for height, root in atts:
        assert height in MERKLE_ROOTS, height
        assert root == MERKLE_ROOTS[height][1]


def _manifest(name):
    rows = {}
    for line in (REG / name).read_text().splitlines():
        digest, label = line.split("  ", 1)
        rows[label] = digest
    return rows


def test_each_digest_file_is_one_line_in_a_manifest():
    listed = {**_manifest("manifest.txt"), **_manifest("manifest_amendment_2026-10-24.txt")}
    files = sorted((REG / "digests").glob("*.sha256"))
    assert len(files) == len(listed) == 21
    seen = []
    for f in files:
        text = f.read_text()
        assert re.fullmatch(r"[0-9a-f]{64}\n", text), f.name
        # Test entries are named test_NN here; the stamped manifest puts one more word before "test NN".
        label = f.name[: -len(".sha256")].replace("_", " ")
        match = [lab for lab in listed
                 if lab == label or lab.endswith(" " + label) or lab.replace(" (amends frozen code 02)", "") == label]
        assert len(match) == 1, f.name
        assert listed[match[0]] == text.strip()
        seen.append(match[0])
    assert sorted(seen) == sorted(listed)  # every manifest label is covered exactly once


def test_plan_manifest_names_the_frozen_plan_hash_shown_on_the_ledger_page():
    plan = _manifest("manifest_plan_2026-10-24.txt")
    assert len(plan) == 6
    first = next(iter(plan.items()))
    assert first[0].startswith("PREREG.md")
    assert first[1] == "3b5cf4df90921400c0ca26ccb930912a63564761d5142939a0d7f93a0432e333"

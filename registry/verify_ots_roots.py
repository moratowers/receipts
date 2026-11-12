import sys, hashlib
from opentimestamps.core.serialize import StreamDeserializationContext
from opentimestamps.core.timestamp import DetachedTimestampFile
from opentimestamps.core.notary import BitcoinBlockHeaderAttestation
for path in sys.argv[1:]:
    with open(path, 'rb') as f:
        dt = DetachedTimestampFile.deserialize(StreamDeserializationContext(f))
    target = path[:-4]
    try:
        h = hashlib.sha256(open(target, 'rb').read()).digest()
        match = (h == dt.file_digest)
    except FileNotFoundError:
        match = None
    for msg, att in dt.timestamp.all_attestations():
        if isinstance(att, BitcoinBlockHeaderAttestation):
            print(path, att.height, msg[::-1].hex(), 'file_digest_match=%s' % match)

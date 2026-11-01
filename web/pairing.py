"""Persistent browser grants; photo ownership is stored separately."""
import hashlib
import json
import re
import time
from printing.service import atomic

LIFETIME = 31536000

class Pairings:
    def __init__(self, data):
        self.path = data/'web-pairings.json'
        try: self.records = json.loads(self.path.read_text())
        except FileNotFoundError: self.records = {}
        if not isinstance(self.records, dict): raise ValueError('Invalid browser grants')
        for key, record in self.records.items():
            if not re.fullmatch('[0-9a-f]{64}', key) or not isinstance(record, dict) or not re.fullmatch('[0-9a-f]{64}', str(record.get('ownerKey', ''))) or type(record.get('expires')) is not int:
                raise ValueError('Invalid browser grant')

    def live(self):
        return {key:record for key,record in self.records.items() if record['expires'] > time.time()}

    def find(self, token):
        if not isinstance(token, str) or not re.fullmatch('[A-Za-z0-9_-]{64}', token): return None
        return self.live().get(hashlib.sha256(token.encode()).hexdigest())

    def available(self, owner_key):
        records = self.live()
        return len(records) < 12 or any(r['ownerKey'] == owner_key for r in records.values())

    def grant(self, token, owner_key):
        records = {key:r for key,r in self.live().items() if r['ownerKey'] != owner_key}
        if len(records) >= 12: raise ValueError('Browser limit reached')
        records[hashlib.sha256(token.encode()).hexdigest()] = {'ownerKey':owner_key, 'expires':int(time.time())+LIFETIME}
        atomic(self.path, records)
        self.records = records

    def reset(self, keep_token):
        record = self.find(keep_token)
        records = {hashlib.sha256(keep_token.encode()).hexdigest():record} if record else {}
        atomic(self.path, records)
        self.records = records

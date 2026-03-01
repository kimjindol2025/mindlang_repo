#!/usr/bin/env python3
from typing import Dict, List
import hashlib
import time

class RequestDeduplicationAdvanced:
    def __init__(self):
        self.fingerprints: Dict[str, Dict] = {}
        self.duplicates: List[Dict] = []
    
    def compute_fingerprint(self, request_data: str) -> str:
        return hashlib.sha256(request_data.encode()).hexdigest()
    
    def register_request(self, request_data: str) -> Dict:
        fp = self.compute_fingerprint(request_data)
        
        if fp in self.fingerprints:
            self.duplicates.append({"fingerprint": fp, "timestamp": time.time()})
            return {"duplicate": True, "fingerprint": fp}
        
        self.fingerprints[fp] = {"data": request_data, "first_seen": time.time()}
        return {"duplicate": False, "fingerprint": fp}
    
    def get_stats(self) -> Dict:
        return {"unique_requests": len(self.fingerprints), "duplicates_detected": len(self.duplicates)}

def main():
    print("🔍 Request Deduplication Advanced")
    dedup = RequestDeduplicationAdvanced()
    result1 = dedup.register_request("SELECT * FROM users")
    result2 = dedup.register_request("SELECT * FROM users")
    print(f"✅ First: {result1['duplicate']}, Second: {result2['duplicate']}, Stats: {dedup.get_stats()}")

if __name__ == "__main__":
    main()

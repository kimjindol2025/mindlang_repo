#!/usr/bin/env python3
from typing import Dict, List
import time

class VersionControlManager:
    def __init__(self):
        self.versions: Dict[str, List[Dict]] = {}
        self.tags: Dict[str, str] = {}
    
    def create_version(self, entity_id: str, content: str, version_num: int) -> Dict:
        if entity_id not in self.versions:
            self.versions[entity_id] = []
        
        version = {
            "version": version_num,
            "content": content,
            "created_at": time.time()
        }
        self.versions[entity_id].append(version)
        return version
    
    def tag_version(self, entity_id: str, version_num: int, tag: str) -> Dict:
        self.tags[f"{entity_id}:{tag}"] = version_num
        return {"entity": entity_id, "tag": tag, "version": version_num}
    
    def get_version(self, entity_id: str, version_num: int) -> Dict:
        if entity_id in self.versions:
            for v in self.versions[entity_id]:
                if v["version"] == version_num:
                    return v
        return None
    
    def get_stats(self) -> Dict:
        total_versions = sum(len(v) for v in self.versions.values())
        return {"entities": len(self.versions), "total_versions": total_versions, "tags": len(self.tags)}

def main():
    print("📚 Version Control Manager")
    vcm = VersionControlManager()
    vcm.create_version("doc-001", "Initial content", 1)
    vcm.tag_version("doc-001", 1, "v1.0")
    print(f"✅ Stats: {vcm.get_stats()}")

if __name__ == "__main__":
    main()

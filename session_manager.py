#!/usr/bin/env python3
from typing import Dict
import time
import hashlib

class SessionManager:
    def __init__(self, session_timeout: float = 3600):
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = session_timeout
    
    def create_session(self, user_id: str) -> Dict:
        session_id = hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": time.time(),
            "last_activity": time.time(),
            "data": {}
        }
        return {"session_id": session_id, "user_id": user_id}
    
    def get_session(self, session_id: str) -> Dict:
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if time.time() - session["last_activity"] < self.session_timeout:
                session["last_activity"] = time.time()
                return session
            else:
                del self.sessions[session_id]
        return None
    
    def destroy_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_stats(self) -> Dict:
        return {"active_sessions": len(self.sessions)}

def main():
    print("📱 Session Manager")
    mgr = SessionManager()
    session = mgr.create_session("user123")
    retrieved = mgr.get_session(session["session_id"])
    print(f"✅ Session: {retrieved is not None}, Stats: {mgr.get_stats()}")

if __name__ == "__main__":
    main()

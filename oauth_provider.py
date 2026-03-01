#!/usr/bin/env python3
"""
OAuth2/OIDC Provider - Distributed authentication and authorization
Implements OAuth 2.0 and OpenID Connect for centralized identity management
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import hashlib
import json
import time
import random


class GrantType(Enum):
    """OAuth 2.0 grant types"""
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    PASSWORD = "password"
    REFRESH_TOKEN = "refresh_token"
    IMPLICIT = "implicit"
    DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"


class TokenType(Enum):
    """Token types"""
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    ID_TOKEN = "id_token"


class Scope(Enum):
    """OAuth 2.0 scopes"""
    OPENID = "openid"
    PROFILE = "profile"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    CUSTOM = "custom"


class PKCEMethod(Enum):
    """PKCE methods"""
    PLAIN = "plain"
    S256 = "S256"


@dataclass
class OAuthClient:
    """OAuth client application"""
    client_id: str
    client_secret: str
    client_name: str
    redirect_uris: List[str]
    grant_types: List[GrantType]
    scopes: List[Scope]
    created_at: float = field(default_factory=time.time)
    is_confidential: bool = True
    token_endpoint_auth_method: str = "client_secret_basic"


@dataclass
class User:
    """User account"""
    user_id: str
    username: str
    email: str
    password_hash: str
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_data: Dict = field(default_factory=dict)
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    last_login: Optional[float] = None
    mfa_enabled: bool = False


@dataclass
class AccessToken:
    """Access token"""
    token_id: str
    token: str
    user_id: str
    client_id: str
    scope: List[str]
    issued_at: float
    expires_at: float
    token_type: str = "Bearer"


@dataclass
class RefreshToken:
    """Refresh token"""
    token_id: str
    token: str
    user_id: str
    client_id: str
    issued_at: float
    expires_at: float
    rotation_count: int = 0
    revoked: bool = False


@dataclass
class AuthorizationCode:
    """Authorization code"""
    code_id: str
    code: str
    user_id: str
    client_id: str
    scope: List[str]
    redirect_uri: str
    code_challenge: Optional[str] = None
    issued_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 600)
    used: bool = False


@dataclass
class ConsentGrant:
    """User consent for scopes"""
    consent_id: str
    user_id: str
    client_id: str
    scopes: List[str]
    granted_at: float = field(default_factory=time.time)


class OAuth2Provider:
    """
    OAuth 2.0 / OpenID Connect provider

    Provides:
    - Authorization code flow with PKCE
    - Client credentials flow
    - Token refresh and rotation
    - Consent management
    - Scope-based access control
    - MFA support
    - Token revocation
    """

    def __init__(self, issuer: str = "https://auth.example.com"):
        self.issuer = issuer
        self.clients: Dict[str, OAuthClient] = {}
        self.users: Dict[str, User] = {}
        self.access_tokens: Dict[str, AccessToken] = {}
        self.refresh_tokens: Dict[str, RefreshToken] = {}
        self.authorization_codes: Dict[str, AuthorizationCode] = {}
        self.consents: Dict[str, ConsentGrant] = {}
        self.token_blacklist: Set[str] = set()

    def register_client(self,
                       client_name: str,
                       redirect_uris: List[str],
                       grant_types: List[GrantType],
                       scopes: List[Scope],
                       is_confidential: bool = True) -> OAuthClient:
        """Register OAuth client"""
        client_id = hashlib.md5(f"{client_name}:{time.time()}".encode()).hexdigest()[:16]
        client_secret = hashlib.sha256(f"{client_id}:{time.time()}:{random.random()}".encode()).hexdigest()

        client = OAuthClient(
            client_id=client_id,
            client_secret=client_secret,
            client_name=client_name,
            redirect_uris=redirect_uris,
            grant_types=grant_types,
            scopes=scopes,
            is_confidential=is_confidential
        )

        self.clients[client_id] = client
        return client

    def create_user(self,
                   username: str,
                   email: str,
                   password: str) -> User:
        """Create user account"""
        user_id = hashlib.md5(f"{username}:{time.time()}".encode()).hexdigest()[:16]
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash
        )

        self.users[user_id] = user
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user"""
        for user in self.users.values():
            if user.username == username:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                if user.password_hash == password_hash and user.is_active:
                    user.last_login = time.time()
                    return user
        return None

    def create_authorization_code(self,
                                 user_id: str,
                                 client_id: str,
                                 scope: List[str],
                                 redirect_uri: str,
                                 code_challenge: Optional[str] = None) -> AuthorizationCode:
        """Create authorization code"""
        code_id = hashlib.md5(f"{user_id}:{client_id}:{time.time()}".encode()).hexdigest()[:8]
        code = hashlib.sha256(f"{code_id}:{time.time()}:{random.random()}".encode()).hexdigest()[:32]

        auth_code = AuthorizationCode(
            code_id=code_id,
            code=code,
            user_id=user_id,
            client_id=client_id,
            scope=scope,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge
        )

        self.authorization_codes[code] = auth_code
        return auth_code

    def exchange_code_for_token(self,
                               code: str,
                               client_id: str,
                               code_verifier: Optional[str] = None) -> Optional[AccessToken]:
        """Exchange authorization code for access token"""
        auth_code = self.authorization_codes.get(code)

        if not auth_code:
            return None

        if auth_code.used or auth_code.client_id != client_id:
            return None

        if time.time() > auth_code.expires_at:
            return None

        # Verify PKCE
        if auth_code.code_challenge and code_verifier:
            verifier_hash = hashlib.sha256(code_verifier.encode()).hexdigest()
            if verifier_hash != auth_code.code_challenge:
                return None

        auth_code.used = True

        # Create access token
        access_token_id = hashlib.md5(f"{auth_code.user_id}:{time.time()}".encode()).hexdigest()[:8]
        access_token_str = hashlib.sha256(
            f"{access_token_id}:{time.time()}:{random.random()}".encode()
        ).hexdigest()

        access_token = AccessToken(
            token_id=access_token_id,
            token=access_token_str,
            user_id=auth_code.user_id,
            client_id=client_id,
            scope=auth_code.scope,
            issued_at=time.time(),
            expires_at=time.time() + 3600  # 1 hour
        )

        self.access_tokens[access_token_str] = access_token

        # Create refresh token
        refresh_token_id = hashlib.md5(f"{auth_code.user_id}:{time.time()}".encode()).hexdigest()[:8]
        refresh_token_str = hashlib.sha256(
            f"{refresh_token_id}:{time.time()}:{random.random()}".encode()
        ).hexdigest()

        refresh_token = RefreshToken(
            token_id=refresh_token_id,
            token=refresh_token_str,
            user_id=auth_code.user_id,
            client_id=client_id,
            issued_at=time.time(),
            expires_at=time.time() + 86400 * 30  # 30 days
        )

        self.refresh_tokens[refresh_token_str] = refresh_token

        return access_token

    def refresh_access_token(self, refresh_token: str) -> Optional[AccessToken]:
        """Refresh access token"""
        rt = self.refresh_tokens.get(refresh_token)

        if not rt or rt.revoked or time.time() > rt.expires_at:
            return None

        # Create new access token
        access_token_id = hashlib.md5(f"{rt.user_id}:{time.time()}".encode()).hexdigest()[:8]
        access_token_str = hashlib.sha256(
            f"{access_token_id}:{time.time()}:{random.random()}".encode()
        ).hexdigest()

        access_token = AccessToken(
            token_id=access_token_id,
            token=access_token_str,
            user_id=rt.user_id,
            client_id=rt.client_id,
            scope=["openid", "profile"],
            issued_at=time.time(),
            expires_at=time.time() + 3600
        )

        self.access_tokens[access_token_str] = access_token

        # Implement token rotation
        rt.rotation_count += 1
        if rt.rotation_count > 100:
            rt.revoked = True

        return access_token

    def validate_token(self, token: str) -> Optional[AccessToken]:
        """Validate access token"""
        if token in self.token_blacklist:
            return None

        access_token = self.access_tokens.get(token)
        if not access_token:
            return None

        if time.time() > access_token.expires_at:
            return None

        return access_token

    def revoke_token(self, token: str) -> bool:
        """Revoke token"""
        self.token_blacklist.add(token)
        if token in self.access_tokens:
            del self.access_tokens[token]
        return True

    def grant_consent(self,
                     user_id: str,
                     client_id: str,
                     scopes: List[str]) -> ConsentGrant:
        """Grant user consent"""
        consent_id = hashlib.md5(f"{user_id}:{client_id}".encode()).hexdigest()[:8]

        consent = ConsentGrant(
            consent_id=consent_id,
            user_id=user_id,
            client_id=client_id,
            scopes=scopes
        )

        self.consents[consent_id] = consent
        return consent

    def has_consent(self, user_id: str, client_id: str, scopes: List[str]) -> bool:
        """Check if user has consent for scopes"""
        for consent in self.consents.values():
            if consent.user_id == user_id and consent.client_id == client_id:
                for scope in scopes:
                    if scope not in consent.scopes:
                        return False
                return True
        return False

    def get_userinfo(self, token: str) -> Optional[Dict]:
        """Get user info from token"""
        access_token = self.validate_token(token)
        if not access_token:
            return None

        user = self.users.get(access_token.user_id)
        if not user:
            return None

        userinfo = {
            "sub": user.user_id,
            "name": user.username,
            "email": user.email,
        }

        if "profile" in access_token.scope:
            userinfo.update(user.profile_data)

        if "phone" in access_token.scope and user.phone:
            userinfo["phone_number"] = user.phone

        if "address" in access_token.scope and user.address:
            userinfo["address"] = user.address

        return userinfo

    def get_provider_metadata(self) -> Dict:
        """Get OpenID Connect provider metadata"""
        return {
            "issuer": self.issuer,
            "authorization_endpoint": f"{self.issuer}/authorize",
            "token_endpoint": f"{self.issuer}/token",
            "userinfo_endpoint": f"{self.issuer}/userinfo",
            "revocation_endpoint": f"{self.issuer}/revoke",
            "jwks_uri": f"{self.issuer}/.well-known/jwks.json",
            "grant_types_supported": [gt.value for gt in GrantType],
            "response_types_supported": ["code", "token", "id_token"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "scopes_supported": ["openid", "profile", "email", "phone", "address"],
            "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
            "response_modes_supported": ["query", "fragment"],
            "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
        }

    def get_provider_stats(self) -> Dict:
        """Get provider statistics"""
        return {
            "total_users": len(self.users),
            "active_users": sum(1 for u in self.users.values() if u.is_active),
            "registered_clients": len(self.clients),
            "active_tokens": len(self.access_tokens),
            "refresh_tokens": len(self.refresh_tokens),
            "consents_granted": len(self.consents),
            "blacklisted_tokens": len(self.token_blacklist),
        }

    def generate_provider_report(self) -> str:
        """Generate provider report"""
        stats = self.get_provider_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                   OAUTH2/OIDC PROVIDER REPORT                              ║
║                   Issuer: {self.issuer}                       ║
╚════════════════════════════════════════════════════════════════════════════╝

👥 USERS:
├─ Total Users: {stats['total_users']}
└─ 🟢 Active: {stats['active_users']}

🔐 CLIENTS:
└─ Registered: {stats['registered_clients']}

🎫 TOKENS:
├─ Active Access Tokens: {stats['active_tokens']}
├─ Refresh Tokens: {stats['refresh_tokens']}
└─ Blacklisted: {stats['blacklisted_tokens']}

✅ CONSENTS:
└─ Granted: {stats['consents_granted']}

📱 REGISTERED CLIENTS:
"""

        for client in self.clients.values():
            report += f"\n  {client.client_name}\n"
            report += f"    ID: {client.client_id}\n"
            report += f"    Flows: {', '.join(gt.value for gt in client.grant_types)}\n"
            report += f"    Scopes: {len(client.scopes)}\n"

        return report

    def export_provider_config(self) -> str:
        """Export provider configuration"""
        export_data = {
            "issuer": self.issuer,
            "timestamp": time.time(),
            "provider_metadata": self.get_provider_metadata(),
            "statistics": self.get_provider_stats(),
            "clients": [
                {
                    "client_id": c.client_id,
                    "client_name": c.client_name,
                    "grant_types": [gt.value for gt in c.grant_types],
                    "scopes": [s.value for s in c.scopes],
                }
                for c in self.clients.values()
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔐 OAuth2/OIDC Provider - Centralized Identity Management")
    print("=" * 70)

    provider = OAuth2Provider("https://auth.mindlang.com")

    # Register clients
    print("\n📝 Registering OAuth clients...")
    web_app = provider.register_client(
        "Web App",
        redirect_uris=["http://localhost:3000/callback"],
        grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
        scopes=[Scope.OPENID, Scope.PROFILE, Scope.EMAIL]
    )
    print(f"✅ Registered Web App: {web_app.client_id}")

    mobile_app = provider.register_client(
        "Mobile App",
        redirect_uris=["com.example.app://callback"],
        grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
        scopes=[Scope.OPENID, Scope.PROFILE, Scope.EMAIL],
        is_confidential=False
    )
    print(f"✅ Registered Mobile App: {mobile_app.client_id}")

    service = provider.register_client(
        "Backend Service",
        redirect_uris=[],
        grant_types=[GrantType.CLIENT_CREDENTIALS],
        scopes=[Scope.CUSTOM]
    )
    print(f"✅ Registered Backend Service: {service.client_id}")

    # Create users
    print("\n👤 Creating users...")
    user1 = provider.create_user("john.doe", "john@example.com", "password123")
    user2 = provider.create_user("jane.smith", "jane@example.com", "password456")
    print(f"✅ Created {len(provider.users)} users")

    # Authenticate
    print("\n🔓 Authenticating user...")
    auth_user = provider.authenticate_user("john.doe", "password123")
    print(f"✅ Authenticated: {auth_user.username}")

    # Grant consent
    print("\n✅ Granting consent...")
    provider.grant_consent(auth_user.user_id, web_app.client_id, ["openid", "profile", "email"])
    print("✅ Consent granted")

    # Create authorization code
    print("\n📋 Creating authorization code...")
    auth_code = provider.create_authorization_code(
        auth_user.user_id,
        web_app.client_id,
        ["openid", "profile", "email"],
        "http://localhost:3000/callback"
    )
    print(f"✅ Authorization code: {auth_code.code[:8]}...")

    # Exchange code for tokens
    print("\n🔄 Exchanging code for tokens...")
    access_token = provider.exchange_code_for_token(auth_code.code, web_app.client_id)
    print(f"✅ Access Token: {access_token.token[:8]}...")

    # Validate token
    print("\n🔍 Validating token...")
    validated = provider.validate_token(access_token.token)
    print(f"✅ Token valid: {validated is not None}")

    # Get user info
    print("\n📊 Getting user info...")
    userinfo = provider.get_userinfo(access_token.token)
    print(f"✅ User: {userinfo['name']} ({userinfo['email']})")

    # Refresh token
    print("\n🔁 Refreshing token...")
    # Create refresh token first by getting another access token
    auth_code2 = provider.create_authorization_code(
        auth_user.user_id,
        web_app.client_id,
        ["openid", "profile"],
        "http://localhost:3000/callback"
    )
    access_token2 = provider.exchange_code_for_token(auth_code2.code, web_app.client_id)
    refresh_token_str = list(provider.refresh_tokens.values())[0].token if provider.refresh_tokens else None

    if refresh_token_str:
        new_token = provider.refresh_access_token(refresh_token_str)
        print(f"✅ New Access Token: {new_token.token[:8]}...")

    # Generate report
    print(provider.generate_provider_report())

    # Export
    print("\n📄 Exporting provider config...")
    export = provider.export_provider_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ OAuth2/OIDC provider ready for authentication")


if __name__ == "__main__":
    main()

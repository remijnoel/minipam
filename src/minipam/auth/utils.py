"""
JWT token utilities for authentication

Handles JWT token creation, validation, and parsing using the standard library.
"""

import os
import json
import time
import base64
import hashlib
import hmac
from typing import Optional, Dict, Any, Union
from .models import UserInfo, JWTPayload
from .base import AuthTokenError
from ..config_loader import get_jwt_config


class JWTHandler:
    """Handles JWT token operations"""
    
    def __init__(self):
        """Initialize JWT handler with configuration from config system"""
        # Get JWT configuration from config system (with environment variable overrides)
        jwt_config = get_jwt_config()
        
        self.secret = jwt_config.get("secret")
        self.algorithm = jwt_config.get("algorithm", "HS256")
        self.issuer = os.getenv("MINIPAM_JWT_ISSUER", "minipam")
        self.expiry_hours = jwt_config.get("expiry_hours", 8)
        
        if not self.secret:
            raise AuthTokenError("JWT secret is required in configuration")
        
        if self.algorithm not in ["HS256", "HS512"]:
            raise AuthTokenError(f"Unsupported JWT algorithm: {self.algorithm}")
    
    def create_token(self, user_info: UserInfo) -> str:
        """Create a JWT token for the given user
        
        Args:
            user_info: User information to encode in token
            
        Returns:
            JWT token string
            
        Raises:
            AuthTokenError: If token creation fails
        """
        try:
            now = int(time.time())
            exp = now + (self.expiry_hours * 3600)
            
            payload = JWTPayload.from_user_info(user_info, now, exp)
            return self._encode_jwt(payload.dict())
            
        except Exception as e:
            raise AuthTokenError(f"Failed to create JWT token: {str(e)}")
    
    def validate_token(self, token: str) -> UserInfo:
        """Validate and decode a JWT token
        
        Args:
            token: JWT token string to validate
            
        Returns:
            UserInfo object from the token
            
        Raises:
            AuthTokenError: If token is invalid or expired
        """
        try:
            payload_dict = self._decode_jwt(token)
            payload = JWTPayload(**payload_dict)
            
            # Check expiration
            if payload.exp < int(time.time()):
                raise AuthTokenError("Token has expired")
            
            # Check issuer
            if payload.iss != self.issuer:
                raise AuthTokenError("Invalid token issuer")
            
            return payload.to_user_info()
            
        except AuthTokenError:
            raise
        except Exception as e:
            raise AuthTokenError(f"Invalid token: {str(e)}")
    
    def _encode_jwt(self, payload: Dict[str, Any]) -> str:
        """Encode JWT token using HMAC
        
        Args:
            payload: Token payload dictionary
            
        Returns:
            JWT token string
        """
        # Create header
        header = {
            "alg": self.algorithm,
            "typ": "JWT"
        }
        
        # Encode header and payload
        header_b64 = self._base64url_encode(json.dumps(header, separators=(',', ':')))
        payload_b64 = self._base64url_encode(json.dumps(payload, separators=(',', ':')))
        
        # Create signature
        message = f"{header_b64}.{payload_b64}"
        signature = self._create_signature(message)
        
        return f"{message}.{signature}"
    
    def _decode_jwt(self, token: str) -> Dict[str, Any]:
        """Decode and verify JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload dictionary
            
        Raises:
            AuthTokenError: If token format or signature is invalid
        """
        try:
            parts = token.split('.')
            if len(parts) != 3:
                raise AuthTokenError("Invalid JWT format")
            
            header_b64, payload_b64, signature_b64 = parts
            
            # Verify signature
            message = f"{header_b64}.{payload_b64}"
            expected_signature = self._create_signature(message)
            
            if not hmac.compare_digest(signature_b64, expected_signature):
                raise AuthTokenError("Invalid token signature")
            
            # Decode header and payload
            header = json.loads(self._base64url_decode(header_b64))
            payload = json.loads(self._base64url_decode(payload_b64))
            
            # Verify algorithm
            if header.get("alg") != self.algorithm:
                raise AuthTokenError("Invalid token algorithm")
            
            return payload
            
        except json.JSONDecodeError:
            raise AuthTokenError("Invalid JSON in token")
        except Exception as e:
            raise AuthTokenError(f"Token decode error: {str(e)}")
    
    def _create_signature(self, message: str) -> str:
        """Create HMAC signature for JWT
        
        Args:
            message: Message to sign
            
        Returns:
            Base64URL encoded signature
        """
        if self.algorithm == "HS256":
            hash_func = hashlib.sha256
        elif self.algorithm == "HS512":
            hash_func = hashlib.sha512
        else:
            raise AuthTokenError(f"Unsupported algorithm: {self.algorithm}")
        
        signature = hmac.new(
            self.secret.encode('utf-8'),
            message.encode('utf-8'),
            hash_func
        ).digest()
        
        return self._base64url_encode(signature)
    
    def _base64url_encode(self, data: Union[bytes, str]) -> str:
        """Base64URL encode data
        
        Args:
            data: Data to encode
            
        Returns:
            Base64URL encoded string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encoded = base64.urlsafe_b64encode(data).decode('ascii')
        return encoded.rstrip('=')  # Remove padding
    
    def _base64url_decode(self, data: str) -> str:
        """Base64URL decode data
        
        Args:
            data: Base64URL encoded string
            
        Returns:
            Decoded string
        """
        # Add padding if needed
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += '=' * padding
        
        decoded = base64.urlsafe_b64decode(data.encode('ascii'))
        return decoded.decode('utf-8')


# Global JWT handler instance
jwt_handler: Optional[JWTHandler] = None


def get_jwt_handler() -> JWTHandler:
    """Get the global JWT handler instance
    
    Returns:
        JWTHandler instance
        
    Raises:
        AuthTokenError: If JWT handler is not initialized
    """
    global jwt_handler
    if jwt_handler is None:
        jwt_handler = JWTHandler()
    return jwt_handler


def create_access_token(user_info: UserInfo) -> str:
    """Create an access token for the user
    
    Args:
        user_info: User information
        
    Returns:
        JWT access token
    """
    return get_jwt_handler().create_token(user_info)


def validate_access_token(token: str) -> UserInfo:
    """Validate an access token
    
    Args:
        token: JWT token to validate
        
    Returns:
        User information from token
        
    Raises:
        AuthTokenError: If token is invalid
    """
    return get_jwt_handler().validate_token(token)

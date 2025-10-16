"""Broker Credential Manager for secure credential storage"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from freqtrade.exceptions import OperationalException


logger = logging.getLogger(__name__)

Base = declarative_base()


class BrokerCredentialModel(Base):
    """SQLAlchemy model for broker credentials"""
    __tablename__ = 'broker_credentials'
    
    id = Column(Integer, primary_key=True)
    broker_name = Column(String(50), unique=True, nullable=False)
    encrypted_credentials = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BrokerCredentialManager:
    """
    Manager for secure broker credential storage.
    
    Handles encryption/decryption of broker API credentials,
    provides methods for CRUD operations, and validates
    broker connections.
    """
    
    def __init__(self, config: dict):
        """
        Initialize BrokerCredentialManager.
        
        :param config: Freqtrade configuration
        """
        self._config = config
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key)
        
        # Initialize database
        db_url = config.get('broker_credentials_db_url', 'sqlite:///broker_credentials.db')
        self._engine = create_engine(db_url)
        Base.metadata.create_all(self._engine)
        
        Session = sessionmaker(bind=self._engine)
        self._session = Session()
        
        logger.info("BrokerCredentialManager initialized")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key from environment or file"""
        # Try environment variable first
        key_env = os.getenv('FREQTRADE_ENCRYPTION_KEY')
        if key_env:
            try:
                return key_env.encode()
            except Exception:
                pass
        
        # Try key file
        key_file = os.path.expanduser('~/.freqtrade_encryption_key')
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read encryption key file: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
            logger.info(f"Generated new encryption key and saved to {key_file}")
        except Exception as e:
            logger.warning(f"Failed to save encryption key: {e}")
        
        return key
    
    def store_credentials(self, broker_name: str, credentials: Dict) -> bool:
        """
        Store encrypted broker credentials.
        
        :param broker_name: Name of the broker
        :param credentials: Dictionary with credential data
        :return: True if successful
        """
        try:
            # Encrypt credentials
            credentials_json = json.dumps(credentials)
            encrypted_data = self._cipher.encrypt(credentials_json.encode()).decode()
            
            # Check if broker already exists
            existing = self._session.query(BrokerCredentialModel).filter_by(
                broker_name=broker_name
            ).first()
            
            if existing:
                # Update existing
                existing.encrypted_credentials = encrypted_data
                existing.updated_at = datetime.utcnow()
                existing.is_active = True
            else:
                # Create new
                credential_model = BrokerCredentialModel(
                    broker_name=broker_name,
                    encrypted_credentials=encrypted_data
                )
                self._session.add(credential_model)
            
            self._session.commit()
            logger.info(f"Stored credentials for broker: {broker_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credentials for {broker_name}: {e}")
            self._session.rollback()
            return False
    
    def retrieve_credentials(self, broker_name: str) -> Optional[Dict]:
        """
        Retrieve and decrypt broker credentials.
        
        :param broker_name: Name of the broker
        :return: Decrypted credentials dictionary or None
        """
        try:
            credential_model = self._session.query(BrokerCredentialModel).filter_by(
                broker_name=broker_name,
                is_active=True
            ).first()
            
            if not credential_model:
                return None
            
            # Decrypt credentials
            encrypted_data = credential_model.encrypted_credentials.encode()
            decrypted_data = self._cipher.decrypt(encrypted_data).decode()
            credentials = json.loads(decrypted_data)
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to retrieve credentials for {broker_name}: {e}")
            return None
    
    def delete_credentials(self, broker_name: str) -> bool:
        """
        Delete broker credentials.
        
        :param broker_name: Name of the broker
        :return: True if successful
        """
        try:
            credential_model = self._session.query(BrokerCredentialModel).filter_by(
                broker_name=broker_name
            ).first()
            
            if credential_model:
                credential_model.is_active = False
                credential_model.updated_at = datetime.utcnow()
                self._session.commit()
                logger.info(f"Deleted credentials for broker: {broker_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete credentials for {broker_name}: {e}")
            self._session.rollback()
            return False
    
    def list_brokers(self) -> List[Dict]:
        """
        List all configured brokers.
        
        :return: List of broker information
        """
        try:
            brokers = self._session.query(BrokerCredentialModel).filter_by(
                is_active=True
            ).all()
            
            result = []
            for broker in brokers:
                result.append({
                    'id': broker.id,
                    'broker_name': broker.broker_name,
                    'created_at': broker.created_at.isoformat(),
                    'updated_at': broker.updated_at.isoformat(),
                    'is_active': broker.is_active
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list brokers: {e}")
            return []
    
    def validate_credentials(self, broker_name: str) -> Tuple[bool, str]:
        """
        Validate broker credentials by testing connection.
        
        :param broker_name: Name of the broker
        :return: Tuple of (is_valid, error_message)
        """
        try:
            credentials = self.retrieve_credentials(broker_name)
            if not credentials:
                return False, "Credentials not found"
            
            # Test connection based on broker type
            if broker_name.lower() == 'zerodha':
                return self._test_zerodha_connection(credentials)
            elif broker_name.lower() == 'smartapi':
                return self._test_smartapi_connection(credentials)
            elif broker_name.lower() == 'openalgo':
                return self._test_openalgo_connection(credentials)
            elif broker_name.lower() == 'paperbroker':
                return True, "Paper broker always valid"
            else:
                return False, f"Unknown broker: {broker_name}"
                
        except Exception as e:
            logger.error(f"Failed to validate credentials for {broker_name}: {e}")
            return False, str(e)
    
    def _test_zerodha_connection(self, credentials: Dict) -> Tuple[bool, str]:
        """Test Zerodha Kite Connect credentials"""
        try:
            from kiteconnect import KiteConnect
            
            api_key = credentials.get('api_key')
            access_token = credentials.get('access_token')
            
            if not api_key:
                return False, "API key missing"
            
            kite = KiteConnect(api_key=api_key)
            
            if access_token:
                kite.set_access_token(access_token)
                # Test with profile call
                profile = kite.profile()
                return True, f"Connected as {profile.get('user_name', 'Unknown')}"
            else:
                return False, "Access token missing - please complete OAuth flow"
                
        except ImportError:
            return False, "kiteconnect package not installed"
        except Exception as e:
            return False, f"Connection failed: {e}"
    
    def _test_smartapi_connection(self, credentials: Dict) -> Tuple[bool, str]:
        """Test SmartAPI credentials"""
        try:
            from SmartApi import SmartConnect
            
            api_key = credentials.get('api_key')
            username = credentials.get('username')
            password = credentials.get('password')
            
            if not all([api_key, username, password]):
                return False, "Missing required credentials"
            
            smart_api = SmartConnect(api_key=api_key)
            # Note: Full test would require TOTP, so just validate format
            return True, "Credentials format valid"
            
        except ImportError:
            return False, "smartapi-python package not installed"
        except Exception as e:
            return False, f"Validation failed: {e}"
    
    def _test_openalgo_connection(self, credentials: Dict) -> Tuple[bool, str]:
        """Test OpenAlgo credentials"""
        try:
            import requests
            
            api_key = credentials.get('api_key')
            host = credentials.get('host', 'http://127.0.0.1:5000')
            
            if not api_key:
                return False, "API key missing"
            
            # Test with a simple API call
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{host}/api/v1/profile", headers=headers, timeout=5)
            
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
                
        except Exception as e:
            return False, f"Connection failed: {e}"
    
    def rotate_encryption_key(self) -> bool:
        """
        Rotate encryption key (re-encrypt all credentials with new key).
        
        :return: True if successful
        """
        try:
            # Get all active credentials
            brokers = self._session.query(BrokerCredentialModel).filter_by(
                is_active=True
            ).all()
            
            # Decrypt with old key
            old_credentials = {}
            for broker in brokers:
                try:
                    encrypted_data = broker.encrypted_credentials.encode()
                    decrypted_data = self._cipher.decrypt(encrypted_data).decode()
                    old_credentials[broker.broker_name] = json.loads(decrypted_data)
                except Exception as e:
                    logger.error(f"Failed to decrypt credentials for {broker.broker_name}: {e}")
                    return False
            
            # Generate new key
            new_key = Fernet.generate_key()
            new_cipher = Fernet(new_key)
            
            # Re-encrypt with new key
            for broker in brokers:
                if broker.broker_name in old_credentials:
                    credentials_json = json.dumps(old_credentials[broker.broker_name])
                    new_encrypted_data = new_cipher.encrypt(credentials_json.encode()).decode()
                    broker.encrypted_credentials = new_encrypted_data
                    broker.updated_at = datetime.utcnow()
            
            # Save new key
            key_file = os.path.expanduser('~/.freqtrade_encryption_key')
            with open(key_file, 'wb') as f:
                f.write(new_key)
            
            # Update cipher
            self._encryption_key = new_key
            self._cipher = new_cipher
            
            # Commit changes
            self._session.commit()
            
            logger.info("Successfully rotated encryption key")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate encryption key: {e}")
            self._session.rollback()
            return False
    
    def close(self):
        """Close database session"""
        if self._session:
            self._session.close()

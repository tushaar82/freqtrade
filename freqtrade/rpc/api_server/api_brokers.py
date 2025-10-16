"""API endpoints for broker management"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from freqtrade.data.broker_credentials import BrokerCredentialManager
from freqtrade.exceptions import OperationalException
from freqtrade.rpc.api_server.deps import get_config, get_rpc_optional
from freqtrade.rpc.rpc import RPC, RPCException


logger = logging.getLogger(__name__)

# Create the router
router = APIRouter()


@router.get('/brokers', response_model=List[Dict[str, Any]], tags=['brokers'])
def list_brokers(config=Depends(get_config), rpc: RPC = Depends(get_rpc_optional)):
    """
    List all configured brokers.
    """
    try:
        credential_manager = BrokerCredentialManager(config)
        brokers = credential_manager.list_brokers()
        credential_manager.close()
        
        # Add connection status for each broker
        for broker in brokers:
            try:
                is_valid, message = credential_manager.validate_credentials(broker['broker_name'])
                broker['connection_status'] = 'connected' if is_valid else 'disconnected'
                broker['status_message'] = message
            except Exception as e:
                broker['connection_status'] = 'error'
                broker['status_message'] = str(e)
        
        return brokers
        
    except Exception as e:
        logger.error(f"Failed to list brokers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/brokers', tags=['brokers'])
def add_broker(
    broker_data: Dict[str, Any],
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Add new broker credentials.
    
    Expected format:
    {
        "broker_name": "zerodha",
        "credentials": {
            "api_key": "your_api_key",
            "api_secret": "your_api_secret",
            "redirect_url": "https://127.0.0.1:8080",
            "request_token": "your_request_token"
        }
    }
    """
    try:
        broker_name = broker_data.get('broker_name')
        credentials = broker_data.get('credentials', {})
        
        if not broker_name:
            raise HTTPException(status_code=400, detail="broker_name is required")
        
        if not credentials:
            raise HTTPException(status_code=400, detail="credentials are required")
        
        # Validate broker name
        supported_brokers = ['zerodha', 'smartapi', 'openalgo', 'paperbroker']
        if broker_name.lower() not in supported_brokers:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported broker. Supported brokers: {supported_brokers}"
            )
        
        credential_manager = BrokerCredentialManager(config)
        success = credential_manager.store_credentials(broker_name, credentials)
        
        if success:
            # Test connection
            is_valid, message = credential_manager.validate_credentials(broker_name)
            credential_manager.close()
            
            return {
                "status": "success",
                "message": f"Broker {broker_name} added successfully",
                "connection_test": {
                    "valid": is_valid,
                    "message": message
                }
            }
        else:
            credential_manager.close()
            raise HTTPException(status_code=500, detail="Failed to store credentials")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add broker: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/brokers/{broker_name}', tags=['brokers'])
def update_broker(
    broker_name: str,
    credentials: Dict[str, Any],
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Update broker credentials.
    """
    try:
        credential_manager = BrokerCredentialManager(config)
        
        # Check if broker exists
        existing_creds = credential_manager.retrieve_credentials(broker_name)
        if not existing_creds:
            credential_manager.close()
            raise HTTPException(status_code=404, detail=f"Broker {broker_name} not found")
        
        # Update credentials
        success = credential_manager.store_credentials(broker_name, credentials)
        
        if success:
            # Test connection
            is_valid, message = credential_manager.validate_credentials(broker_name)
            credential_manager.close()
            
            return {
                "status": "success",
                "message": f"Broker {broker_name} updated successfully",
                "connection_test": {
                    "valid": is_valid,
                    "message": message
                }
            }
        else:
            credential_manager.close()
            raise HTTPException(status_code=500, detail="Failed to update credentials")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update broker {broker_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/brokers/{broker_name}', tags=['brokers'])
def delete_broker(
    broker_name: str,
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Delete broker credentials.
    """
    try:
        credential_manager = BrokerCredentialManager(config)
        success = credential_manager.delete_credentials(broker_name)
        credential_manager.close()
        
        if success:
            return {
                "status": "success",
                "message": f"Broker {broker_name} deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Broker {broker_name} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete broker {broker_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/brokers/{broker_name}/status', tags=['brokers'])
def get_broker_status(
    broker_name: str,
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Check broker connection status.
    """
    try:
        credential_manager = BrokerCredentialManager(config)
        is_valid, message = credential_manager.validate_credentials(broker_name)
        credential_manager.close()
        
        return {
            "broker_name": broker_name,
            "status": "connected" if is_valid else "disconnected",
            "message": message,
            "timestamp": "2025-10-16T04:59:41+05:30"  # Current timestamp
        }
        
    except Exception as e:
        logger.error(f"Failed to check status for broker {broker_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/brokers/{broker_name}/test', tags=['brokers'])
def test_broker_connection(
    broker_name: str,
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Test broker connection with stored credentials.
    """
    try:
        credential_manager = BrokerCredentialManager(config)
        is_valid, message = credential_manager.validate_credentials(broker_name)
        credential_manager.close()
        
        return {
            "broker_name": broker_name,
            "test_result": "success" if is_valid else "failed",
            "message": message,
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except Exception as e:
        logger.error(f"Failed to test broker {broker_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/brokers/{broker_name}/balance', tags=['brokers'])
def get_broker_balance(
    broker_name: str,
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Get broker account balance.
    """
    try:
        if not rpc:
            raise HTTPException(status_code=503, detail="Bot is not running")
        
        # This would need to be implemented in the RPC layer
        # For now, return a placeholder response
        return {
            "broker_name": broker_name,
            "balance": {
                "available_cash": 0.0,
                "used_margin": 0.0,
                "total_balance": 0.0,
                "currency": "INR"
            },
            "message": "Balance retrieval not fully implemented",
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get balance for broker {broker_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/brokers/{broker_name}/positions', tags=['brokers'])
def get_broker_positions(
    broker_name: str,
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Get broker positions.
    """
    try:
        if not rpc:
            raise HTTPException(status_code=503, detail="Bot is not running")
        
        # This would need to be implemented in the RPC layer
        # For now, return a placeholder response
        return {
            "broker_name": broker_name,
            "positions": [],
            "message": "Position retrieval not fully implemented",
            "timestamp": "2025-10-16T04:59:41+05:30"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get positions for broker {broker_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/brokers/rotate-key', tags=['brokers'])
def rotate_encryption_key(
    config=Depends(get_config),
    rpc: RPC = Depends(get_rpc_optional)
):
    """
    Rotate encryption key for broker credentials.
    """
    try:
        credential_manager = BrokerCredentialManager(config)
        success = credential_manager.rotate_encryption_key()
        credential_manager.close()
        
        if success:
            return {
                "status": "success",
                "message": "Encryption key rotated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to rotate encryption key")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rotate encryption key: {e}")
        raise HTTPException(status_code=500, detail=str(e))

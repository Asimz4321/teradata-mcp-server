"""
BAR (Backup and Restore) Tools for Teradata DSA MCP Server

"""

import logging
import string
import json
from typing import Optional, List, Dict
import os

logger = logging.getLogger("teradata_mcp_server")

# Setup logging to file (always add file handler)
log_dir = os.path.join(os.path.dirname(__file__), '../../../logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'bar_tools.log')
file_handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)
logger.info('Logging initialized to %s', log_file)
logger.info('TEST LOG ENTRY: bar_tools.py imported and logging is active.')

from teradata_mcp_server.tools.utils import create_response
from .dsa_client import dsa_client

logger = logging.getLogger("teradata_mcp_server")


#------------------ Disk File System Operations ------------------#

def list_disk_file_systems() -> str:
    """List all configured disk file systems in DSA
    
    Lists all disk file systems configured for backup operations, showing:
    - File system paths
    - Maximum files allowed per file system
    - Configuration status
    
    Returns:
        Formatted summary of all disk file systems with their configurations
    """
    try:
        logger.info("Listing disk file systems via DSA API")
        
        # Make request to DSA API
        response = dsa_client._make_request(
            method="GET",
            endpoint="dsa/components/backup-applications/disk-file-system"
        )
        
        logger.debug(f"DSA API response: {response}")
        
        results = []
        results.append("🗂️ DSA Disk File Systems")
        results.append("=" * 50)
        
        if response.get('status') == 'LIST_DISK_FILE_SYSTEMS_SUCCESSFUL':
            file_systems = response.get('fileSystems', [])
            
            if file_systems:
                results.append(f"📊 Total File Systems: {len(file_systems)}")
                results.append("")
                
                for i, fs in enumerate(file_systems, 1):
                    results.append(f"🗂️ File System #{i}")
                    results.append(f"   📁 Path: {fs.get('fileSystemPath', 'N/A')}")
                    results.append(f"   📄 Max Files: {fs.get('maxFiles', 'N/A')}")
                    results.append("")
            else:
                results.append("📋 No disk file systems configured")
                
            results.append("=" * 50)
            results.append(f"✅ Status: {response.get('status')}")
            results.append(f"🔍 Found Component: {response.get('foundComponent', False)}")
            results.append(f"✔️ Valid: {response.get('valid', False)}")
            
        else:
            results.append(f"❌ Failed to list disk file systems")
            results.append(f"📊 Status: {response.get('status', 'Unknown')}")
            if response.get('validationlist'):
                validation = response['validationlist']
                if validation.get('serverValidationList'):
                    for error in validation['serverValidationList']:
                        results.append(f"❌ Error: {error.get('message', 'Unknown error')}")
        
        return "\n".join(results)
        
    except Exception as e:
        logger.error(f"Failed to list disk file systems: {str(e)}")
        return f"❌ Error listing disk file systems: {str(e)}"


def config_disk_file_system(file_system_path: str, max_files: int) -> str:
    """Configure a disk file system for DSA backup operations
    
    Adds a new disk file system to the existing list or updates an existing one.
    This allows DSA to use the file system for backup storage operations.
    
    Args:
        file_system_path: Full path to the file system directory (e.g., "/var/opt/teradata/backup")
        max_files: Maximum number of files allowed in this file system (must be > 0)
        
    Returns:
        Formatted result of the configuration operation with status and any validation messages
    """
    try:
        logger.info(f"Configuring disk file system: {file_system_path} with max files: {max_files}")
        
        # First, get the existing file systems
        try:
            existing_response = dsa_client._make_request(
                method="GET",
                endpoint="dsa/components/backup-applications/disk-file-system"
            )
            
            existing_file_systems = []
            if existing_response.get('status') == 'LIST_DISK_FILE_SYSTEMS_SUCCESSFUL':
                existing_file_systems = existing_response.get('fileSystems', [])
                logger.info(f"Found {len(existing_file_systems)} existing file systems")
            else:
                logger.info("No existing file systems found or unable to retrieve them")
                
        except Exception as e:
            logger.warning(f"Could not retrieve existing file systems: {e}")
            existing_file_systems = []
        
        # Check if the new file system path already exists and update it, or add it
        file_systems_to_configure = []
        path_exists = False
        
        for fs in existing_file_systems:
            if fs.get('fileSystemPath') == file_system_path:
                # Update existing file system
                file_systems_to_configure.append({
                    "fileSystemPath": file_system_path,
                    "maxFiles": max_files
                })
                path_exists = True
                logger.info(f"Updating existing file system: {file_system_path}")
            else:
                # Keep existing file system unchanged
                file_systems_to_configure.append(fs)
        
        # If path doesn't exist, add the new file system
        if not path_exists:
            file_systems_to_configure.append({
                "fileSystemPath": file_system_path,
                "maxFiles": max_files
            })
            logger.info(f"Adding new file system: {file_system_path}")
        
        # Prepare request data with all file systems (existing + new/updated)
        request_data = {
            "fileSystems": file_systems_to_configure
        }
        
        logger.info(f"Configuring {len(file_systems_to_configure)} file systems total")
        
        # Make request to DSA API
        response = dsa_client._make_request(
            method="POST",
            endpoint="dsa/components/backup-applications/disk-file-system",
            data=request_data
        )
        
        logger.debug(f"DSA API response: {response}")
        
        results = []
        results.append("🗂️ DSA Disk File System Configuration")
        results.append("=" * 50)
        results.append(f"📁 File System Path: {file_system_path}")
        results.append(f"📄 Max Files: {max_files}")
        results.append(f"📊 Total File Systems: {len(file_systems_to_configure)}")
        results.append(f"🔄 Operation: {'Update' if path_exists else 'Add'}")
        results.append("")
        
        if response.get('status') == 'CONFIG_DISK_FILE_SYSTEM_SUCCESSFUL':
            results.append("✅ Disk file system configured successfully")
            results.append(f"📊 Status: {response.get('status')}")
            results.append(f"✔️ Valid: {response.get('valid', False)}")
            
        else:
            results.append("❌ Failed to configure disk file system")
            results.append(f"📊 Status: {response.get('status', 'Unknown')}")
            results.append(f"✔️ Valid: {response.get('valid', False)}")
            
            # Show validation errors if any
            if response.get('validationlist'):
                validation = response['validationlist']
                results.append("")
                results.append("🔍 Validation Details:")
                
                if validation.get('serverValidationList'):
                    for error in validation['serverValidationList']:
                        results.append(f"❌ Server Error: {error.get('message', 'Unknown error')}")
                        results.append(f"   Code: {error.get('code', 'N/A')}")
                        results.append(f"   Status: {error.get('valStatus', 'N/A')}")
                
                if validation.get('clientValidationList'):
                    for error in validation['clientValidationList']:
                        results.append(f"❌ Client Error: {error.get('message', 'Unknown error')}")
        
        results.append("")
        results.append("=" * 50)
        results.append("✅ Disk file system configuration operation completed")
        
        return "\n".join(results)
        
    except Exception as e:
        logger.error(f"Failed to configure disk file system: {str(e)}")
        return f"❌ Error configuring disk file system '{file_system_path}': {str(e)}"


def delete_disk_file_systems() -> str:
    """Delete all disk file system configurations from DSA
    
    Removes all disk file system configurations from DSA. This operation will fail
    if any file systems are currently in use by backup operations or file target groups.
    
    Returns:
        Formatted result of the deletion operation with status and any validation messages
        
    Warning:
        This operation removes ALL disk file system configurations. Make sure no
        backup operations or file target groups are using these file systems.
    """
    try:
        logger.info("Deleting all disk file system configurations via DSA API")
        
        # Make request to DSA API
        response = dsa_client._make_request(
            method="DELETE",
            endpoint="dsa/components/backup-applications/disk-file-system"
        )
        
        logger.debug(f"DSA API response: {response}")
        
        results = []
        results.append("🗂️ DSA Disk File System Deletion")
        results.append("=" * 50)
        
        if response.get('status') == 'DELETE_COMPONENT_SUCCESSFUL':
            results.append("✅ All disk file systems deleted successfully")
            results.append(f"📊 Status: {response.get('status')}")
            results.append(f"✔️ Valid: {response.get('valid', False)}")
            
        else:
            results.append("❌ Failed to delete disk file systems")
            results.append(f"📊 Status: {response.get('status', 'Unknown')}")
            results.append(f"✔️ Valid: {response.get('valid', False)}")
            
            # Show validation errors if any
            if response.get('validationlist'):
                validation = response['validationlist']
                results.append("")
                results.append("🔍 Validation Details:")
                
                if validation.get('serverValidationList'):
                    for error in validation['serverValidationList']:
                        results.append(f"❌ Server Error: {error.get('message', 'Unknown error')}")
                        results.append(f"   Code: {error.get('code', 'N/A')}")
                        results.append(f"   Status: {error.get('valStatus', 'N/A')}")
                
                if validation.get('clientValidationList'):
                    for error in validation['clientValidationList']:
                        results.append(f"❌ Client Error: {error.get('message', 'Unknown error')}")
                
                # If deletion failed due to dependencies, provide guidance
                if any('in use by' in error.get('message', '') for error in validation.get('serverValidationList', [])):
                    results.append("")
                    results.append("💡 Helpful Notes:")
                    results.append("   • Remove all backup jobs using these file systems first")
                    results.append("   • Delete any file target groups that reference these file systems")
                    results.append("   • Use list_disk_file_systems() to see current configurations")
        
        results.append("")
        results.append("=" * 50)
        results.append("✅ Disk file system deletion operation completed")
        
        return "\n".join(results)
        
    except Exception as e:
        logger.error(f"Failed to delete disk file systems: {str(e)}")
        return f"❌ Error deleting disk file systems: {str(e)}"


def remove_disk_file_system(file_system_path: str) -> str:
    """Remove a specific disk file system from DSA configuration
    
    Removes a specific disk file system from the existing list by reconfiguring
    the remaining file systems. This operation will fail if the file system is
    currently in use by backup operations or file target groups.
    
    Args:
        file_system_path: Full path to the file system directory to remove (e.g., "/var/opt/teradata/backup")
        
    Returns:
        Formatted result of the removal operation with status and any validation messages
        
    Warning:
        This operation will fail if the file system is in use by any backup operations
        or file target groups. Remove those dependencies first.
    """
    try:
        logger.info(f"Removing disk file system: {file_system_path}")
        
        # First, get the existing file systems
        try:
            existing_response = dsa_client._make_request(
                method="GET",
                endpoint="dsa/components/backup-applications/disk-file-system"
            )
            
            existing_file_systems = []
            if existing_response.get('status') == 'LIST_DISK_FILE_SYSTEMS_SUCCESSFUL':
                existing_file_systems = existing_response.get('fileSystems', [])
                logger.info(f"Found {len(existing_file_systems)} existing file systems")
            else:
                logger.warning("No existing file systems found or unable to retrieve them")
                return f"❌ Could not retrieve existing file systems to remove '{file_system_path}'"
                
        except Exception as e:
            logger.error(f"Could not retrieve existing file systems: {e}")
            return f"❌ Error retrieving existing file systems: {str(e)}"
        
        # Check if the file system to remove exists
        path_exists = False
        file_systems_to_keep = []
        
        for fs in existing_file_systems:
            if fs.get('fileSystemPath') == file_system_path:
                path_exists = True
                logger.info(f"Found file system to remove: {file_system_path}")
            else:
                # Keep this file system
                file_systems_to_keep.append(fs)
        
        # If path doesn't exist, return error
        if not path_exists:
            available_paths = [fs.get('fileSystemPath', 'N/A') for fs in existing_file_systems]
            results = []
            results.append("🗂️ DSA Disk File System Removal")
            results.append("=" * 50)
            results.append(f"❌ File system '{file_system_path}' not found")
            results.append("")
            results.append("📋 Available file systems:")
            if available_paths:
                for path in available_paths:
                    results.append(f"   • {path}")
            else:
                results.append("   (No file systems configured)")
            results.append("")
            results.append("=" * 50)
            return "\n".join(results)
        
        # Prepare request data with remaining file systems
        request_data = {
            "fileSystems": file_systems_to_keep
        }
        
        logger.info(f"Removing '{file_system_path}', keeping {len(file_systems_to_keep)} file systems")
        
        # Make request to DSA API to reconfigure with remaining file systems
        response = dsa_client._make_request(
            method="POST",
            endpoint="dsa/components/backup-applications/disk-file-system",
            data=request_data
        )
        
        logger.debug(f"DSA API response: {response}")
        
        results = []
        results.append("🗂️ DSA Disk File System Removal")
        results.append("=" * 50)
        results.append(f"📁 Removed File System: {file_system_path}")
        results.append(f"📊 Remaining File Systems: {len(file_systems_to_keep)}")
        results.append("")
        
        if response.get('status') == 'CONFIG_DISK_FILE_SYSTEM_SUCCESSFUL':
            results.append("✅ Disk file system removed successfully")
            results.append(f"📊 Status: {response.get('status')}")
            results.append(f"✔️ Valid: {response.get('valid', False)}")
            
            if file_systems_to_keep:
                results.append("")
                results.append("📋 Remaining file systems:")
                for fs in file_systems_to_keep:
                    path = fs.get('fileSystemPath', 'N/A')
                    max_files = fs.get('maxFiles', 'N/A')
                    results.append(f"   • {path} (Max Files: {max_files})")
            else:
                results.append("")
                results.append("📋 No file systems remaining (all removed)")
            
        else:
            results.append("❌ Failed to remove disk file system")
            results.append(f"📊 Status: {response.get('status', 'Unknown')}")
            results.append(f"✔️ Valid: {response.get('valid', False)}")
            
            # Show validation errors if any
            if response.get('validationlist'):
                validation = response['validationlist']
                results.append("")
                results.append("🔍 Validation Details:")
                
                if validation.get('serverValidationList'):
                    for error in validation['serverValidationList']:
                        results.append(f"❌ Server Error: {error.get('message', 'Unknown error')}")
                        results.append(f"   Code: {error.get('code', 'N/A')}")
                        results.append(f"   Status: {error.get('valStatus', 'N/A')}")
                
                if validation.get('clientValidationList'):
                    for error in validation['clientValidationList']:
                        results.append(f"❌ Client Error: {error.get('message', 'Unknown error')}")
        
        results.append("")
        results.append("=" * 50)
        results.append("✅ Disk file system removal operation completed")
        
        return "\n".join(results)
        
    except Exception as e:
        logger.error(f"Failed to remove disk file system: {str(e)}")
        return f"❌ Error removing disk file system '{file_system_path}': {str(e)}"


def manage_dsa_disk_file_systems(
    operation: str,
    file_system_path: Optional[str] = None,
    max_files: Optional[int] = None
) -> str:
    """Unified DSA Disk File System Management Tool
    
    This comprehensive tool handles all DSA disk file system operations including
    listing, configuring, and removing file system configurations.
    
    Args:
        operation: The operation to perform
        file_system_path: Path to the file system (for config and remove operations)
        max_files: Maximum number of files allowed (for config operation)
    
    Available Operations:
        - "list" - List all configured disk file systems
        - "config" - Configure a new disk file system
        - "delete_all" - Remove all file system configurations
        - "remove" - Remove a specific file system configuration
    
    Returns:
        Result of the requested operation
    """
    
    logger.info(f"DSA Disk File System Management - Operation: {operation}")
    
    try:
        # List operation
        if operation == "list":
            return list_disk_file_systems()
            
        # Config operation
        elif operation == "config":
            if not file_system_path:
                return "❌ Error: file_system_path is required for config operation"
            if max_files is None:
                return "❌ Error: max_files is required for config operation"
            return config_disk_file_system(file_system_path, max_files)
            
        # Delete all operation
        elif operation == "delete_all":
            return delete_disk_file_systems()
            
        # Remove specific operation
        elif operation == "remove":
            if not file_system_path:
                return "❌ Error: file_system_path is required for remove operation"
            return remove_disk_file_system(file_system_path)
            
        else:
            available_operations = [
                "list", "config", "delete_all", "remove"
            ]
            return f"❌ Error: Unknown operation '{operation}'. Available operations: {', '.join(available_operations)}"
            
    except Exception as e:
        logger.error(f"DSA Disk File System Management error - Operation: {operation}, Error: {str(e)}")
        return f"❌ Error during {operation}: {str(e)}"


""" 
#PA255044 ->  START -- AWS S3 Configuration Tool
""" 
#------------------ AWS S3 Backup Solution Configuration and Operations ------------------#


def list_aws_s3_backup_configurations () -> str:
    """List the configured AWS S3 object store systems in DSA
    
    Lists all configured AWS S3 storage target systems that are currently available configured for the backup operations, showing:
    - Bucket names
    - Prefix numbers, names and devices configured
    - Configuration status
    
    Returns:
        Formatted summary of all S3 file systems with their configurations
    """
    
    try:
        logger.info("Listing AWS S3 target systems via DSA API")

        # Make request to DSA API
        response = dsa_client._make_request(
            method="GET",
            endpoint="dsa/components/backup-applications/aws-s3"
        )
        
        # Add debug log for full API response
        logger.debug("[DEBUG] Full DSA API response from aws-s3 endpoint: %r", response)
        
        results = []
        results.append("🗂️ DSA AWS S3 Backup Solution Systems Available")
        results.append("=" * 50)
        
        if response.get('status') == 'LIST_AWS_APP_SUCCESSFUL':
            # Extract bucketsByRegion from nested aws[0]['configAwsRest']['bucketsByRegion']
            bucketsByRegion = []
            aws_list = response.get('aws', [])
            if aws_list and isinstance(aws_list, list):
                configAwsRest = aws_list[0].get('configAwsRest', {})
                bucketsByRegion = configAwsRest.get('bucketsByRegion', [])

            # Handle if bucketsByRegion is a dict (single region) or list
            if isinstance(bucketsByRegion, dict):
                bucketsByRegion = [bucketsByRegion]

            bucket_count = 0
            if bucketsByRegion:
                for i, region in enumerate(bucketsByRegion, 1):
                    region_name = region.get('region', 'N/A')
                    results.append(f"🗂️ Region #{i}: {region_name}")
                    buckets = region.get('buckets', [])
                    if isinstance(buckets, dict):
                        buckets = [buckets]
                    if buckets:
                        for j, bucket in enumerate(buckets, 1):
                            bucket_count += 1
                            bucket_name = bucket.get('bucketName', 'N/A')
                            results.append(f"   📁 Bucket #{j}: {bucket_name}")
                            prefix_list = bucket.get('prefixList', [])
                            if isinstance(prefix_list, dict):
                                prefix_list = [prefix_list]
                            if prefix_list:
                                for k, prefix in enumerate(prefix_list, 1):
                                    prefix_name = prefix.get('prefixName', 'N/A')
                                    storage_devices = prefix.get('storageDevices', 'N/A')
                                    results.append(f"      🔖 Prefix #{k}: {prefix_name}")
                                    results.append(f"         Storage Devices: {storage_devices}")
                            else:
                                results.append(f"      🔖 No prefixes configured")
                    else:
                        results.append(f"   📁 No buckets configured in this region")
                    results.append("")
                results.insert(1, f"📊 Total Buckets Configured: {bucket_count}")
            else:
                results.append("📋 No AWS backup Solutions Configured")

            results.append("=" * 50)
            results.append(f"✅ Status: {response.get('status')}")
            results.append(f"🔍 Found Component: {response.get('foundComponent', False)}")
            results.append(f"✔️ Valid: {response.get('valid', False)}")
            
        else:
            results.append(f"❌ Failed to list AWS S3 Backup Solutions Configured")
            results.append(f"📊 Status: {response.get('status', 'Unknown')}")
            if response.get('validationlist'):
                validation = response['validationlist']
                if validation.get('serverValidationList'):
                    for error in validation['serverValidationList']:
                        results.append(f"❌ Error: {error.get('message', 'Unknown error')}")
        
        return "\n".join(results)
        
    except Exception as e:
        logger.error(f"Failed to list AWS S3 Backup Solutions Configured: {str(e)}")
        return f"❌ Error listing AWS S3 Backup Solutions Configured: {str(e)}"


def manage_AWS_S3_backup_configurations(
    operation: str,
    accessId: Optional[str] = None,
    accessKey: Optional[str] = None,
    bucketsByRegion: Optional[object] = None,
    bucketName: Optional[str] = None,
    acctName: Optional[str] = None
) -> str:
    """Unified DSA AWS S3 Backup Configuration Management Tool

    This comprehensive tool handles all DSA AWS S3 backup configuration operations including
    listing, configuring, and removing backup configurations.
    
    Args:
        operation: The operation to perform
        accessId: AWS Access ID
        accessKey: AWS Access Key
        bucketsByRegion: Buckets by region configuration (object: dict or list)
        bucketName: AWS Bucket Name
        acctName: AWS Account Name
    
    Available Operations:
        - "list" - List all configured AWS S3 backup solutions
        - "config" - Configure a new AWS S3 backup solution
        - "delete_all" - Remove all AWS S3 backup solution configurations
        - "remove" - Remove a specific AWS S3 backup solution configuration

    Returns:
        Result of the requested operation
    """

    logger.info(f"DSA AWS S3 Backup Solution Management - Operation: {operation}")
    
    try:
        # List operation
        if operation == "list":
            return list_aws_s3_backup_configurations()
        # Config operation
        elif operation == "config":
            if not accessId:
                return "❌ Error: accessId is required for config operation"
            if not accessKey:
                return "❌ Error: accessKey is required for config operation"
            if not bucketsByRegion:
                return "❌ Error: bucketsByRegion is required for config operation"
            if not acctName:
                return "❌ Error: acctName is required for config operation"
            if not bucketName:
                return "❌ Error: bucketName is required for config operation"
            # bucketsByRegion is now expected as an object (dict or list)
            request_data = {
                "configAwsRest": {
                    "accessId": accessId,
                    "accessKey": accessKey,
                    "bucketsByRegion": bucketsByRegion,
                    "bucketName": bucketName,
                    "acctName": acctName,
                    "viewpoint": True,
                    "viewpointBucketRegion": True
                }
            }
            try:
                response = dsa_client._make_request(
                    method="POST",
                    endpoint="dsa/components/backup-applications/aws-s3",
                    data=request_data
                )
                return f"✅ AWS backup solution configuration operation completed\nResponse: {response}"
            except Exception as e:
                return f"❌ Error configuring AWS backup solution: {str(e)}"
        # Delete all operation
        elif operation == "delete_all":
            return "❌ Error: 'delete_all' operation is not implemented yet for AWS S3 Configuration"
        # Remove specific operation
        elif operation == "remove":
            return "❌ Error: 'remove' operation is not implemented yet for AWS S3 Configuration"
        else:
            available_operations = [
                "list", "config", "delete_all", "remove"
            ]
            return f"❌ Error: Unknown operation '{operation}'. Available operations: {', '.join(available_operations)}"
    except Exception as e:
        logger.error(f"DSA AWS S3 Configuration Management error - Operation: {operation}, Error: {str(e)}")
        return f"❌ Error during {operation}: {str(e)}"


#------------------ Media Server Operations ------------------#

def manage_dsa_media_servers(
    operation: str,
    server_name: Optional[str] = None,
    port: Optional[int] = None,
    ip_addresses: Optional[str] = None,
    pool_shared_pipes: Optional[int] = 50,
    virtual: Optional[bool] = False
) -> str:
    """Unified media server management for all media server operations
    
    This comprehensive function handles all media server operations in the DSA system,
    including listing, getting details, adding, deleting, and managing consumers.
    """
    # Validate operation
    valid_operations = [
        "list", "get", "add", "delete", 
        "list_consumers", "list_consumers_by_server"
    ]
    
    if operation not in valid_operations:
        return f"❌ Invalid operation '{operation}'. Valid operations: {', '.join(valid_operations)}"
    
    try:
        # Route to the appropriate operation
        if operation == "list":
            return _list_media_servers()
        
        elif operation == "get":
            if not server_name:
                return "❌ server_name is required for 'get' operation"
            return _get_media_server(server_name)
        
        elif operation == "add":
            if not server_name:
                return "❌ server_name is required for 'add' operation"
            if not port:
                return "❌ port is required for 'add' operation"
            if not ip_addresses:
                return "❌ ip_addresses is required for 'add' operation"
            
            try:
                import json
                ip_list = json.loads(ip_addresses)
                return _add_media_server(server_name, port, ip_list, pool_shared_pipes or 50)
            except json.JSONDecodeError as e:
                return f"❌ Invalid IP addresses format: {str(e)}\nExpected JSON format: '[{{\"ipAddress\": \"IP\", \"netmask\": \"MASK\"}}]'"
        
        elif operation == "delete":
            if not server_name:
                return "❌ server_name is required for 'delete' operation"
            return _delete_media_server(server_name, virtual or False)
        
        elif operation == "list_consumers":
            return _list_media_server_consumers()
        
        elif operation == "list_consumers_by_server":
            if not server_name:
                return "❌ server_name is required for 'list_consumers_by_server' operation"
            return _list_media_server_consumers_by_name(server_name)
    
    except Exception as e:
        logger.error(f"Failed to execute media server operation '{operation}': {str(e)}")
        return f"❌ Error executing media server operation '{operation}': {str(e)}"


def _list_media_servers() -> str:
    """List all media servers from the DSA system"""
    try:
        # Make request to list media servers
        response = dsa_client._make_request("GET", "dsa/components/mediaservers")
        
        if not response.get("valid", False):
            error_messages = []
            validation_list = response.get("validationlist", {})
            if validation_list:
                client_errors = validation_list.get("clientValidationList", [])
                server_errors = validation_list.get("serverValidationList", [])
                
                for error in client_errors + server_errors:
                    error_messages.append(f"Code {error.get('code', 'N/A')}: {error.get('message', 'Unknown error')}")
            
            if error_messages:
                return f"❌ Failed to list media servers:\n" + "\n".join(error_messages)
            else:
                return f"❌ Failed to list media servers: {response.get('status', 'Unknown error')}"
        
        # Return the full response for complete transparency
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to list media servers: {str(e)}")
        return f"❌ Error listing media servers: {str(e)}"


def _get_media_server(server_name: str) -> str:
    """Get details of a specific media server by name"""
    try:
        # Make request to get specific media server
        endpoint = f"dsa/components/mediaservers/{server_name}"
        response = dsa_client._make_request("GET", endpoint)
        
        if not response.get("valid", False):
            error_messages = []
            validation_list = response.get("validationlist", {})
            if validation_list:
                client_errors = validation_list.get("clientValidationList", [])
                server_errors = validation_list.get("serverValidationList", [])
                
                for error in client_errors + server_errors:
                    error_messages.append(f"Code {error.get('code', 'N/A')}: {error.get('message', 'Unknown error')}")
            
            if error_messages:
                return f"❌ Failed to get media server '{server_name}':\n" + "\n".join(error_messages)
            else:
                return f"❌ Failed to get media server '{server_name}': {response.get('status', 'Unknown error')}"
        
        # Return the full response for complete transparency
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to get media server '{server_name}': {str(e)}")
        return f"❌ Error getting media server '{server_name}': {str(e)}"


def _add_media_server(
    server_name: str,
    port: int,
    ip_list: List[Dict[str, str]],
    pool_shared_pipes: int = 50
) -> str:
    """Add a new media server to the DSA system"""
    try:
        # Validate inputs
        if not server_name or not server_name.strip():
            return "❌ Server name is required and cannot be empty"
        
        if not (1 <= port <= 65535):
            return f"❌ Port must be between 1 and 65535"
        
        if not ip_list or not isinstance(ip_list, list):
            return "❌ At least one IP address is required"
        
        # Validate IP addresses format
        for ip_info in ip_list:
            if not isinstance(ip_info, dict) or 'ipAddress' not in ip_info or 'netmask' not in ip_info:
                return "❌ Each IP address must be a dictionary with 'ipAddress' and 'netmask' keys"
        
        # Prepare request payload
        payload = {
            "serverName": server_name.strip(),
            "port": port,
            "ipInfo": ip_list
        }
        
        # Make request to add media server
        response = dsa_client._make_request(
            "POST", 
            "dsa/components/mediaservers", 
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "*/*"}
        )
        
        if not response.get("valid", False):
            error_messages = []
            validation_list = response.get("validationlist", {})
            if validation_list:
                client_errors = validation_list.get("clientValidationList", [])
                server_errors = validation_list.get("serverValidationList", [])
                
                for error in client_errors + server_errors:
                    error_messages.append(f"Code {error.get('code', 'N/A')}: {error.get('message', 'Unknown error')}")
            
            if error_messages:
                return f"❌ Failed to add media server '{server_name}':\n" + "\n".join(error_messages)
            else:
                return f"❌ Failed to add media server '{server_name}': {response.get('status', 'Unknown error')}"
        
        # Return the full response for complete transparency
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to add media server '{server_name}': {str(e)}")
        return f"❌ Error adding media server '{server_name}': {str(e)}"


def _delete_media_server(server_name: str, virtual: bool = False) -> str:
    """Delete a media server from the DSA system"""
    try:
        # Prepare request parameters
        params = {}
        if virtual:
            params["virtual"] = "true"
        
        # Make request to delete media server
        endpoint = f"dsa/components/mediaservers/{server_name}"
        response = dsa_client._make_request("DELETE", endpoint, params=params)
        
        if not response.get("valid", False):
            error_messages = []
            validation_list = response.get("validationlist", {})
            if validation_list:
                client_errors = validation_list.get("clientValidationList", [])
                server_errors = validation_list.get("serverValidationList", [])
                
                for error in client_errors + server_errors:
                    error_messages.append(f"Code {error.get('code', 'N/A')}: {error.get('message', 'Unknown error')}")
            
            if error_messages:
                return f"❌ Failed to delete media server '{server_name}':\n" + "\n".join(error_messages)
            else:
                return f"❌ Failed to delete media server '{server_name}': {response.get('status', 'Unknown error')}"
        
        # Return the full response for complete transparency
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to delete media server '{server_name}': {str(e)}")
        return f"❌ Error deleting media server '{server_name}': {str(e)}"


def _list_media_server_consumers() -> str:
    """List all media server consumers from the DSA system"""
    try:
        # Make request to list media server consumers
        response = dsa_client._make_request("GET", "dsa/components/mediaservers/listconsumers")
        
        if not response.get("valid", False):
            error_messages = []
            validation_list = response.get("validationlist", {})
            if validation_list:
                client_errors = validation_list.get("clientValidationList", [])
                server_errors = validation_list.get("serverValidationList", [])
                
                for error in client_errors + server_errors:
                    error_messages.append(f"Code {error.get('code', 'N/A')}: {error.get('message', 'Unknown error')}")
            
            if error_messages:
                return f"❌ Failed to list media server consumers:\n" + "\n".join(error_messages)
            else:
                return f"❌ Failed to list media server consumers: {response.get('status', 'Unknown error')}"
        
        # Return the full response for complete transparency
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to list media server consumers: {str(e)}")
        return f"❌ Error listing media server consumers: {str(e)}"


def _list_media_server_consumers_by_name(server_name: str) -> str:
    """List consumers for a specific media server by name"""
    try:
        # Make request to list consumers for specific media server
        endpoint = f"dsa/components/mediaservers/listconsumers/{server_name.strip()}"
        response = dsa_client._make_request("GET", endpoint)
        
        if not response.get("valid", False):
            error_messages = []
            validation_list = response.get("validationlist", {})
            if validation_list:
                client_errors = validation_list.get("clientValidationList", [])
                server_errors = validation_list.get("serverValidationList", [])
                
                for error in client_errors + server_errors:
                    error_messages.append(f"Code {error.get('code', 'N/A')}: {error.get('message', 'Unknown error')}")
            
            if error_messages:
                return f"❌ Failed to list consumers for media server '{server_name}':\n" + "\n".join(error_messages)
            else:
                return f"❌ Failed to list consumers for media server '{server_name}': {response.get('status', 'Unknown error')}"
        
        # Return the full response for complete transparency
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Failed to list consumers for media server '{server_name}': {str(e)}")
        return f"❌ Error listing consumers for media server '{server_name}': {str(e)}"


#------------------ Tool Handler for MCP ------------------#

def handle_bar_manageDsaDiskFileSystem(
    conn: any,  # Not used for DSA operations, but required by MCP framework
    operation: str,
    file_system_path: str = None,
    max_files: int = None,
    *args,
    **kwargs
):
    """
    Handle DSA disk file system operations for the MCP server
    
    This tool provides unified management of DSA disk file system configurations
    for backup and restore operations.
    
    Args:
        conn: Database connection (not used for DSA operations)
        operation: The operation to perform (list, config, delete_all, remove)
        file_system_path: Path to the file system (for config and remove operations)
        max_files: Maximum number of files allowed (for config operation)
    
    Returns:
        ResponseType: formatted response with operation results + metadata
    """
    logger.debug(f"Tool: handle_bar_manageDsaDiskFileSystem: Args: operation: {operation}, file_system_path: {file_system_path}, max_files: {max_files}")
    
    try:
        # Run the synchronous operation
        result = manage_dsa_disk_file_systems(
            operation=operation,
            file_system_path=file_system_path,
            max_files=max_files
        )
        
        metadata = {
            "tool_name": "bar_manageDsaDiskFileSystem",
            "operation": operation,
            "file_system_path": file_system_path,
            "max_files": max_files,
            "success": True
        }
        
        logger.debug(f"Tool: handle_bar_manageDsaDiskFileSystem: metadata: {metadata}")
        return create_response(result, metadata)
        
    except Exception as e:
        logger.error(f"Error in handle_bar_manageDsaDiskFileSystem: {e}")
        error_result = f"❌ Error in DSA disk file system operation: {str(e)}"
        metadata = {
            "tool_name": "bar_manageDsaDiskFileSystem",
            "operation": operation,
            "error": str(e),
            "success": False
        }
        return create_response(error_result, metadata)



def handle_bar_manageAWSS3Operations(
    conn: any,  # Not used for DSA operations, but required by MCP framework
    operation: str,
    accessId: str = None,
    accessKey: str = None,
    bucketsByRegion: object = None,
    bucketName: str = None,
    acctName: str = None,
    *args,
    **kwargs
):
    """
    Handle DSA AWS S3 backup solution configuration operations for the MCP server

    This tool provides unified management of DSA AWS S3 backup solution configuration
    that is  required for backup and restore operations.
    
    Args:
        conn: Database connection (not used for DSA operations)
        operation: The operation to perform (list, config). The  delete_all, remove and will be implemented later
        accessId: AWS access ID (for config operation)
        accessKey: AWS access key (for config operation)
        bucketsByRegion: List of S3 buckets by region (for config operation)
        acctName: AWS account name (for config operation)

    Returns:
        ResponseType: formatted response with operation results + metadata
    """
    logger.info("handle_bar_manageAWSS3Operations called with operation=%s, accessId=%s, acctName=%s", operation, accessId, acctName)
    logger.debug(f"Tool: handle_bar_manageAWSS3Operations: Args: operation: {operation}, accessId: {accessId}, accessKey: {accessKey}, bucketsByRegion: {bucketsByRegion}, acctName: {acctName}")
    logger.debug(f"[DEBUG] bucketsByRegion type: {type(bucketsByRegion)} value: {bucketsByRegion}")
    try:
        # Run the synchronous operation
        result = manage_AWS_S3_backup_configurations(
            operation=operation,
            accessId=accessId,
            accessKey=accessKey,
            bucketsByRegion=bucketsByRegion,
            bucketName="tdedsabucket01",  # Hardcoded for now, will be dynamic later
            acctName=acctName
        )
        metadata = {
            "tool_name": "bar_manageAWSS3Operations",
            "operation": operation,
            "accessId": accessId,
            "accessKey": accessKey,
            "bucketsByRegion": bucketsByRegion,
            "bucketName": bucketName,
            "acctName": acctName,
            "success": True
        }
        logger.debug(f"Tool: handle_bar_manageAWSS3Operations: metadata: {metadata}")
        return create_response(result, metadata)
    except Exception as e:
        logger.error(f"Error in handle_bar_manageAWSS3Operations: {e}")
        error_result = f"❌ Error in DSA AWS S3 operation: {str(e)}"
        metadata = {
            "tool_name": "bar_manageAWSS3Operations",
            "operation": operation,
            "error": str(e),
            "success": False
        }
        return create_response(error_result, metadata)


def handle_bar_manageMediaServer(
    conn: any,  # Not used for DSA operations, but required by MCP framework
    operation: str,
    server_name: str = None,
    port: int = None,
    ip_addresses: str = None,
    pool_shared_pipes: int = 50,
    virtual: bool = False,
    *args,
    **kwargs
):
    """
    Unified media server management tool for all DSA media server operations.
    
    This comprehensive tool handles all media server operations in the DSA system,
    including listing, getting details, adding, deleting, and managing consumers.
    
    Arguments:
        operation - The operation to perform. Valid values:
                   "list" - List all media servers
                   "get" - Get details of a specific media server  
                   "add" - Add a new media server
                   "delete" - Delete a media server
                   "list_consumers" - List all media server consumers
                   "list_consumers_by_server" - List consumers for a specific server
        server_name - Name of the media server (required for get, add, delete, list_consumers_by_server)
        port - Port number for the media server (required for add operation, 1-65535)
        ip_addresses - JSON string containing IP address configuration for add operation, e.g.:
                      '[{"ipAddress": "192.168.1.100", "netmask": "255.255.255.0"}]'
        pool_shared_pipes - Number of shared pipes in the pool (for add operation, 1-99, default: 50)
        virtual - Whether to perform a virtual deletion (for delete operation, default: False)
    
    Returns:
        ResponseType: formatted response with media server operation results + metadata
    """
    logger.debug(f"Tool: handle_bar_manageMediaServer: Args: operation: {operation}, server_name: {server_name}, port: {port}")
    
    try:
        # Validate operation
        valid_operations = [
            "list", "get", "add", "delete", 
            "list_consumers", "list_consumers_by_server"
        ]
        
        if operation not in valid_operations:
            error_result = f"❌ Invalid operation '{operation}'. Valid operations: {', '.join(valid_operations)}"
            metadata = {
                "tool_name": "bar_manageMediaServer",
                "operation": operation,
                "error": "Invalid operation",
                "success": False
            }
            return create_response(error_result, metadata)
        
        # Execute the media server operation
        result = manage_dsa_media_servers(
            operation=operation,
            server_name=server_name,
            port=port,
            ip_addresses=ip_addresses,
            pool_shared_pipes=pool_shared_pipes,
            virtual=virtual
        )
        
        metadata = {
            "tool_name": "bar_manageMediaServer",
            "operation": operation,
            "server_name": server_name,
            "success": True
        }
        logger.debug(f"Tool: handle_bar_manageMediaServer: metadata: {metadata}")
        return create_response(result, metadata)
    except Exception as e:
        logger.error(f"Error in handle_bar_manageMediaServer: {e}")
        error_result = f"❌ Error in DSA media server operation: {str(e)}"
        metadata = {
            "tool_name": "bar_manageMediaServer",
            "operation": operation,
            "error": str(e),
            "success": False
        }
        return create_response(error_result, metadata)
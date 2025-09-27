"""
Supabase Storage client for managing patches, logs, and artifacts.

This module handles uploading and managing blob storage for bugfix artifacts.
"""

import os
from typing import Optional, Dict, Any
from supabase import create_client, Client


class StorageClient:
    """Client for Supabase Storage operations."""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """Initialize the storage client.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key are required")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.bucket_name = "bugfix-artifacts"
    
    def upload_patch(self, patch_content: str, bugfix_id: str) -> Optional[str]:
        """Upload a patch file to Supabase Storage.
        
        Args:
            patch_content: The patch content as string
            bugfix_id: Unique identifier for the bugfix
            
        Returns:
            Public URL of the uploaded patch file
        """
        try:
            file_path = f"patches/{bugfix_id}.patch"
            
            result = self.client.storage.from_(self.bucket_name).upload(
                file_path,
                patch_content.encode('utf-8'),
                {"content-type": "text/plain"}
            )
            
            if result:
                # Get the public URL
                public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
                return public_url
            
        except Exception as e:
            print(f"Error uploading patch for {bugfix_id}: {e}")
        
        return None
    
    def upload_log(self, log_content: str, bugfix_id: str) -> Optional[str]:
        """Upload a log file to Supabase Storage.
        
        Args:
            log_content: The log content as string
            bugfix_id: Unique identifier for the bugfix
            
        Returns:
            Public URL of the uploaded log file
        """
        try:
            file_path = f"logs/{bugfix_id}.log"
            
            result = self.client.storage.from_(self.bucket_name).upload(
                file_path,
                log_content.encode('utf-8'),
                {"content-type": "text/plain"}
            )
            
            if result:
                # Get the public URL
                public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
                return public_url
            
        except Exception as e:
            print(f"Error uploading log for {bugfix_id}: {e}")
        
        return None
    
    def upload_artifact(self, artifact_content: bytes, bugfix_id: str, 
                       file_extension: str = "bin") -> Optional[str]:
        """Upload an artifact file to Supabase Storage.
        
        Args:
            artifact_content: The artifact content as bytes
            bugfix_id: Unique identifier for the bugfix
            file_extension: File extension for the artifact
            
        Returns:
            Public URL of the uploaded artifact file
        """
        try:
            file_path = f"artifacts/{bugfix_id}.{file_extension}"
            
            result = self.client.storage.from_(self.bucket_name).upload(
                file_path,
                artifact_content
            )
            
            if result:
                # Get the public URL
                public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
                return public_url
            
        except Exception as e:
            print(f"Error uploading artifact for {bugfix_id}: {e}")
        
        return None
    
    def download_file(self, url: str) -> Optional[bytes]:
        """Download a file from Supabase Storage.
        
        Args:
            url: Public URL of the file to download
            
        Returns:
            File content as bytes
        """
        try:
            # Extract file path from URL
            file_path = url.split('/')[-2] + '/' + url.split('/')[-1]
            
            result = self.client.storage.from_(self.bucket_name).download(file_path)
            return result
            
        except Exception as e:
            print(f"Error downloading file from {url}: {e}")
        
        return None
    
    def delete_file(self, url: str) -> bool:
        """Delete a file from Supabase Storage.
        
        Args:
            url: Public URL of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract file path from URL
            file_path = url.split('/')[-2] + '/' + url.split('/')[-1]
            
            result = self.client.storage.from_(self.bucket_name).remove([file_path])
            return len(result) > 0
            
        except Exception as e:
            print(f"Error deleting file from {url}: {e}")
        
        return False

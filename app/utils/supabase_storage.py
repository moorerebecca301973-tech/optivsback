# app/utils/supabase_storage.py
import os
from typing import Optional, BinaryIO
from supabase import create_client, Client
from app.core.config import settings
import uuid
from fastapi import UploadFile, HTTPException, status


# Initialize the Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Constants for the storage bucket
KYC_BUCKET_NAME = "kyc-documents"  # You'll need to create this bucket in Supabase Storage


async def upload_file_to_supabase(
    file: UploadFile, 
    user_id: str, 
    document_type: str
) -> str:
    """
    Uploads a file to Supabase Storage in the KYC bucket.
    Organizes files by user_id and document_type.
    
    Args:
        file: The FastAPI UploadFile object
        user_id: UUID of the user
        document_type: Type of document ('id_front', 'id_back', 'selfie')
    
    Returns:
        str: The public URL of the uploaded file
    
    Raises:
        HTTPException: If the upload fails
    """
    try:
        # Generate a unique filename to prevent collisions
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ".bin"
        unique_filename = f"{user_id}/{document_type}_{uuid.uuid4()}{file_extension}"
        
        # Read file content
        content = await file.read()
        
        # Upload to Supabase Storage
        response = supabase.storage.from_(KYC_BUCKET_NAME).upload(
            path=unique_filename,
            file=content,
            file_options={"content-type": file.content_type}
        )
        
        # Get public URL
        url_response = supabase.storage.from_(KYC_BUCKET_NAME).get_public_url(unique_filename)
        
        return url_response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {str(e)}"
        )


async def delete_file_from_supabase(file_url: str) -> bool:
    """
    Deletes a file from Supabase Storage based on its URL.
    
    Args:
        file_url: The public URL of the file to delete
    
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        # Extract the file path from the URL
        # Supabase URLs are typically: https://project-ref.supabase.co/storage/v1/object/public/bucket-name/path/to/file
        parts = file_url.split(f"/object/public/{KYC_BUCKET_NAME}/")
        if len(parts) != 2:
            return False
            
        file_path = parts[1]
        
        # Delete the file
        supabase.storage.from_(KYC_BUCKET_NAME).remove([file_path])
        
        return True
        
    except Exception as e:
        # Log the error but don't raise exception as this might be called in cleanup
        print(f"Error deleting file from Supabase Storage: {str(e)}")
        return False


async def generate_signed_url(file_url: str, expires_in: int = 3600) -> Optional[str]:
    """
    Generates a signed URL for temporary access to a private file.
    
    Args:
        file_url: The public URL of the file
        expires_in: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        Optional[str]: Signed URL or None if generation fails
    """
    try:
        # Extract the file path from the URL
        parts = file_url.split(f"/object/public/{KYC_BUCKET_NAME}/")
        if len(parts) != 2:
            return None
            
        file_path = parts[1]
        
        # Generate signed URL
        signed_url = supabase.storage.from_(KYC_BUCKET_NAME).create_signed_url(
            file_path, expires_in=expires_in
        )
        
        return signed_url
        
    except Exception as e:
        print(f"Error generating signed URL: {str(e)}")
        return None
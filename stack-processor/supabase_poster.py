#!/usr/bin/env python3
"""
Supabase Poster for Stack Overflow Data

Uploads processed Stack Overflow data from converted.json to Supabase database.
Based on the TypeScript storeToolHandler implementation.
"""

import json
import os
import hashlib
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import re

try:
    from decouple import config
except ImportError:
    print("Please install python-decouple: pip install python-decouple")
    exit(1)

try:
    from supabase import create_client, Client
    from supabase.lib.client_options import ClientOptions
except ImportError:
    print("Please install supabase: pip install supabase")
    exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SupabaseConfig:
    """Configuration for Supabase connection"""
    url: str
    key: str
    
    @classmethod
    def from_env(cls) -> 'SupabaseConfig':
        try:
            url = config('SUPABASE_URL')
            key = config('SUPABASE_ANON_KEY')
        except Exception as e:
            raise ValueError(
                f"Please check your .env file contains SUPABASE_URL and SUPABASE_ANON_KEY. Error: {e}"
            )
        
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_ANON_KEY cannot be empty. Please check your .env file."
            )
        
        return cls(url=url, key=key)


class SupabasePoster:
    """Handles uploading data to Supabase"""
    
    def __init__(self, config: SupabaseConfig):
        self.config = config
        self.supabase: Client = create_client(config.url, config.key)
        
    def redact_secrets(self, text: str) -> str:
        """Redact sensitive information from text"""
        if not text:
            return text
            
        # Patterns for common secrets
        patterns = [
            # API keys
            (r'(?i)(api[_-]?key|apikey)[\s:=]+[\'"]?([a-z0-9_-]{20,})[\'"]?', r'\1=***'),
            # Tokens
            (r'(?i)(token|access[_-]?token)[\s:=]+[\'"]?([a-z0-9_-]{20,})[\'"]?', r'\1=***'),
            # Passwords
            (r'(?i)(password|passwd|pwd)[\s:=]+[\'"]?([^\s\'"]{8,})[\'"]?', r'\1=***'),
            # Database URLs with credentials
            (r'(?i)(mongodb|postgres|mysql)://([^:]+):([^@]+)@', r'\1://***:***@'),
            # Email addresses (partial redaction)
            (r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'***@\2'),
        ]
        
        result = text
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)
            
        return result
    
    def compute_content_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content for deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def chunk_text(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """Split text into chunks for embedding"""
        if not text or len(text) <= max_chunk_size:
            return [text] if text else []
            
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            
            if current_size + word_size > max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks
    
    async def check_duplicate(self, content_hash: str) -> Optional[str]:
        """Check if entry already exists by content hash"""
        try:
            response = self.supabase.table('entries').select('id').eq('content_hash', content_hash).limit(1).maybe_single().execute()
            
            if response.data:
                return response.data['id']
            return None
            
        except Exception as e:
            logger.warning(f"Error checking for duplicate: {e}")
            return None
    
    async def insert_entry(self, entry_data: Dict[str, Any]) -> str:
        """Insert entry using RPC function"""
        try:
            # Map entry data to RPC parameters
            rpc_params = {
                'p_type': entry_data.get('type'),
                'p_title': entry_data.get('title'),
                'p_body': entry_data.get('body'),
                'p_stack_trace': entry_data.get('stack_trace'),
                'p_code': entry_data.get('code'),
                'p_repro_steps': entry_data.get('repro_steps'),
                'p_root_cause': entry_data.get('root_cause'),
                'p_resolution': entry_data.get('resolution'),
                'p_severity': entry_data.get('severity'),
                'p_tags': entry_data.get('tags', []),
                'p_project': entry_data.get('metadata', {}).get('project'),
                'p_repo': entry_data.get('metadata', {}).get('repo'),
                'p_commit': entry_data.get('metadata', {}).get('commit'),
                'p_branch': entry_data.get('metadata', {}).get('branch'),
                'p_os': entry_data.get('metadata', {}).get('os'),
                'p_runtime': entry_data.get('metadata', {}).get('runtime'),
                'p_language': entry_data.get('metadata', {}).get('language'),
                'p_framework': entry_data.get('metadata', {}).get('framework'),
                'p_resolved': entry_data.get('type') == 'solution' or (entry_data.get('resolution') and entry_data.get('resolution').strip()),
                'p_content_hash': entry_data.get('content_hash')
            }
            
            response = self.supabase.rpc('rpc_insert_entry', rpc_params).execute()
            
            if response.data:
                return str(response.data)
            else:
                raise Exception("RPC returned no data")
                
        except Exception as e:
            logger.error(f"Error inserting entry: {e}")
            raise
    
    async def link_related_entries(self, entry_id: str, related_ids: List[str]) -> None:
        """Link related entries"""
        if not related_ids:
            return
            
        try:
            link_rows = []
            for related_id in related_ids:
                link_rows.append({
                    'from_entry_id': entry_id,
                    'to_entry_id': related_id,
                    'relation': 'relates_to'
                })
            
            response = self.supabase.table('links').upsert(
                link_rows,
                on_conflict='from_entry_id,to_entry_id,relation'
            ).execute()
            
            logger.info(f"Linked {len(related_ids)} related entries to {entry_id}")
            
        except Exception as e:
            logger.warning(f"Error linking related entries: {e}")
    
    async def insert_embeddings(self, entry_id: str, chunks: List[str], embeddings: List[List[float]]) -> None:
        """Insert text chunks and embeddings"""
        if not chunks or not embeddings:
            return
            
        try:
            chunk_ids = list(range(len(chunks)))
            
            rpc_params = {
                'p_entry_id': entry_id,
                'p_chunk_ids': chunk_ids,
                'p_chunk_texts': chunks,
                'p_embeddings': embeddings
            }
            
            response = self.supabase.rpc('rpc_insert_embeddings', rpc_params).execute()
            logger.info(f"Inserted {len(chunks)} chunks with embeddings for entry {entry_id}")
            
        except Exception as e:
            logger.warning(f"Error inserting embeddings: {e}")
    
    def generate_mock_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """Generate mock embeddings (replace with actual embedding service)"""
        # This is a placeholder - in production you'd use OpenAI, Cohere, etc.
        embeddings = []
        for chunk in chunks:
            # Generate a simple hash-based mock embedding
            hash_val = hashlib.md5(chunk.encode()).hexdigest()
            embedding = [float(int(hash_val[i:i+2], 16)) / 255.0 for i in range(0, min(len(hash_val), 32), 2)]
            # Pad or trim to standard size (e.g., 384 dimensions)
            while len(embedding) < 384:
                embedding.extend(embedding[:min(384-len(embedding), len(embedding))])
            embeddings.append(embedding[:384])
        return embeddings
    
    async def store_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Store a single entry in Supabase"""
        try:
            # Redact sensitive information
            body = self.redact_secrets(entry.get('body', ''))
            code = self.redact_secrets(entry.get('code', ''))
            stack_trace = self.redact_secrets(entry.get('stack_trace', ''))
            repro_steps = self.redact_secrets(entry.get('repro_steps', ''))
            resolution = self.redact_secrets(entry.get('resolution', ''))
            
            # Compute content hash for deduplication
            payload_for_hash = '\n\n'.join([
                entry.get('type', ''),
                entry.get('title', ''),
                body,
                code,
                stack_trace,
                repro_steps,
                resolution
            ])
            content_hash = self.compute_content_hash(payload_for_hash)
            
            # Check for duplicates
            duplicate_id = await self.check_duplicate(content_hash)
            if duplicate_id:
                logger.info(f"Entry already exists: {duplicate_id}")
                return {'id': duplicate_id, 'duplicate_of': duplicate_id, 'created': False}
            
            # Prepare entry data
            entry_data = {
                **entry,
                'body': body or None,
                'code': code or None,
                'stack_trace': stack_trace or None,
                'repro_steps': repro_steps or None,
                'resolution': resolution or None,
                'content_hash': content_hash
            }
            
            # Insert entry
            entry_id = await self.insert_entry(entry_data)
            logger.info(f"Inserted entry: {entry_id}")
            
            # Link related entries
            if entry.get('related_ids'):
                await self.link_related_entries(entry_id, entry['related_ids'])
            
            # Process embeddings
            text_to_chunk = '\n\n'.join(filter(None, [body, code, stack_trace, repro_steps, resolution]))
            if text_to_chunk.strip():
                chunks = self.chunk_text(text_to_chunk)
                if chunks:
                    # Generate embeddings (mock implementation)
                    embeddings = self.generate_mock_embeddings(chunks)
                    await self.insert_embeddings(entry_id, chunks, embeddings)
            
            return {'id': entry_id, 'created': True}
            
        except Exception as e:
            logger.error(f"Error storing entry '{entry.get('title', 'unknown')}': {e}")
            raise
    
    async def upload_from_json(self, json_file: Path) -> Dict[str, int]:
        """Upload all entries from converted.json file"""
        logger.info(f"Loading data from {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        logger.info(f"Found {len(entries)} entries to process")
        
        results = {
            'total': len(entries),
            'created': 0,
            'duplicates': 0,
            'errors': 0
        }
        
        for i, entry in enumerate(entries):
            try:
                logger.info(f"Processing entry {i+1}/{len(entries)}: {entry.get('title', 'unknown')[:50]}...")
                
                result = await self.store_entry(entry)
                
                if result.get('created'):
                    results['created'] += 1
                else:
                    results['duplicates'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to process entry {i+1}: {e}")
                results['errors'] += 1
                continue
        
        logger.info(f"Upload complete: {results}")
        return results


async def main():
    """Main function to upload data to Supabase"""
    try:
        # Load configuration
        config = SupabaseConfig.from_env()
        
        # Initialize poster
        poster = SupabasePoster(config)
        
        # Find converted.json file
        json_file = Path(__file__).parent / 'converted.json'
        if not json_file.exists():
            logger.error(f"File not found: {json_file}")
            return
        
        # Upload data
        results = await poster.upload_from_json(json_file)
        
        print(f"\n🎉 Upload Results:")
        print(f"Total entries: {results['total']}")
        print(f"Created: {results['created']}")
        print(f"Duplicates: {results['duplicates']}")
        print(f"Errors: {results['errors']}")
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise


if __name__ == '__main__':
    print("🚀 Starting Supabase upload...")
    asyncio.run(main())

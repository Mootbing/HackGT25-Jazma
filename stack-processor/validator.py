#!/usr/bin/env python3
"""
Data Validator

Validates that the converted Stack Overflow data matches the expected schema format.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path


def validate_entry(entry: Dict[str, Any], index: int) -> List[str]:
    """Validate a single entry against the schema"""
    errors = []
    
    # Required fields
    if 'type' not in entry:
        errors.append(f"Entry {index}: Missing required field 'type'")
    elif entry['type'] not in ['bug', 'solution', 'doc']:
        errors.append(f"Entry {index}: Invalid type '{entry['type']}', must be bug/solution/doc")
    
    if 'title' not in entry:
        errors.append(f"Entry {index}: Missing required field 'title'")
    elif not isinstance(entry['title'], str):
        errors.append(f"Entry {index}: 'title' must be a string")
    
    # Optional fields with type checking
    if 'body' in entry and not isinstance(entry['body'], str):
        errors.append(f"Entry {index}: 'body' must be a string")
    
    if 'stack_trace' in entry and not isinstance(entry['stack_trace'], str):
        errors.append(f"Entry {index}: 'stack_trace' must be a string")
    
    if 'code' in entry and not isinstance(entry['code'], str):
        errors.append(f"Entry {index}: 'code' must be a string")
    
    if 'repro_steps' in entry and not isinstance(entry['repro_steps'], str):
        errors.append(f"Entry {index}: 'repro_steps' must be a string")
    
    if 'root_cause' in entry and not isinstance(entry['root_cause'], str):
        errors.append(f"Entry {index}: 'root_cause' must be a string")
    
    if 'resolution' in entry and not isinstance(entry['resolution'], str):
        errors.append(f"Entry {index}: 'resolution' must be a string")
    
    if 'severity' in entry:
        if entry['severity'] not in ['low', 'medium', 'high', 'critical']:
            errors.append(f"Entry {index}: Invalid severity '{entry['severity']}', must be low/medium/high/critical")
    
    if 'tags' in entry:
        if not isinstance(entry['tags'], list):
            errors.append(f"Entry {index}: 'tags' must be an array")
        elif not all(isinstance(tag, str) for tag in entry['tags']):
            errors.append(f"Entry {index}: All tags must be strings")
    
    if 'metadata' in entry:
        if not isinstance(entry['metadata'], dict):
            errors.append(f"Entry {index}: 'metadata' must be an object")
        else:
            # Validate metadata fields
            metadata = entry['metadata']
            string_fields = ['project', 'repo', 'commit', 'branch', 'os', 'runtime', 'language', 'framework']
            for field in string_fields:
                if field in metadata and not isinstance(metadata[field], str):
                    errors.append(f"Entry {index}: metadata.{field} must be a string")
    
    if 'idempotency_key' in entry and not isinstance(entry['idempotency_key'], str):
        errors.append(f"Entry {index}: 'idempotency_key' must be a string")
    
    if 'related_ids' in entry:
        if not isinstance(entry['related_ids'], list):
            errors.append(f"Entry {index}: 'related_ids' must be an array")
        elif not all(isinstance(rid, str) for rid in entry['related_ids']):
            errors.append(f"Entry {index}: All related_ids must be strings")
    
    return errors


def validate_converted_data(file_path: str) -> None:
    """Validate the entire converted dataset"""
    print(f"Validating {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("ERROR: Root element must be an array")
            return
        
        total_errors = []
        
        for i, entry in enumerate(data):
            if not isinstance(entry, dict):
                total_errors.append(f"Entry {i}: Must be an object")
                continue
            
            entry_errors = validate_entry(entry, i)
            total_errors.extend(entry_errors)
        
        print(f"Validation complete!")
        print(f"Total entries: {len(data)}")
        print(f"Total errors: {len(total_errors)}")
        
        if total_errors:
            print("\nFirst 10 errors:")
            for error in total_errors[:10]:
                print(f"  - {error}")
            if len(total_errors) > 10:
                print(f"  ... and {len(total_errors) - 10} more errors")
        else:
            print("✅ All entries are valid!")
            
        # Print some statistics
        types = {}
        severities = {}
        has_code = 0
        has_resolution = 0
        
        for entry in data:
            entry_type = entry.get('type', 'unknown')
            types[entry_type] = types.get(entry_type, 0) + 1
            
            severity = entry.get('severity', 'none')
            severities[severity] = severities.get(severity, 0) + 1
            
            if entry.get('code'):
                has_code += 1
            
            if entry.get('resolution'):
                has_resolution += 1
        
        print(f"\n📊 Statistics:")
        print(f"Types: {types}")
        print(f"Severities: {severities}")
        print(f"Entries with code: {has_code}")
        print(f"Entries with resolution: {has_resolution}")
        
    except FileNotFoundError:
        print(f"ERROR: File {file_path} not found")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON - {e}")
    except Exception as e:
        print(f"ERROR: {e}")


def main():
    """Main entry point"""
    converted_file = Path(__file__).parent / "converted.json"
    validate_converted_data(str(converted_file))


if __name__ == "__main__":
    main()
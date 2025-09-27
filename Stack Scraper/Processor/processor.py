#!/usr/bin/env python3
"""
Stack Overflow Data Processor

Converts questions.jsonl (Stack Overflow questions and answers) to the format
expected by the bug tracking system schema.
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import hashlib


@dataclass
class StackOverflowQuestion:
    """Represents a Stack Overflow question"""
    id: int
    title: str
    body: str
    tags: List[str]
    score: int
    view_count: int
    creation_date: str
    owner_display_name: Optional[str]
    accepted_answer_id: Optional[int]


@dataclass  
class StackOverflowAnswer:
    """Represents a Stack Overflow answer"""
    id: int
    parent_id: int
    body: str
    score: int
    creation_date: str
    owner_display_name: Optional[str]


def extract_code_from_html(html_content: str) -> str:
    """Extract code blocks from HTML content"""
    # Find all <pre><code>...</code></pre> blocks
    code_pattern = r'<pre><code>(.*?)</code></pre>'
    code_blocks = re.findall(code_pattern, html_content, re.DOTALL)
    
    # Also find standalone <code>...</code> blocks
    inline_code_pattern = r'<code>(.*?)</code>'
    inline_code = re.findall(inline_code_pattern, html_content)
    
    all_code = code_blocks + inline_code
    return '\n\n'.join(all_code) if all_code else ""


def strip_html_tags(html_content: str) -> str:
    """Remove HTML tags and decode HTML entities"""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', html_content)
    
    # Decode common HTML entities
    clean = clean.replace('&lt;', '<')
    clean = clean.replace('&gt;', '>')
    clean = clean.replace('&amp;', '&')
    clean = clean.replace('&quot;', '"')
    clean = clean.replace('&#39;', "'")
    
    # Clean up extra whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    return clean


def parse_tags(tags_str: str) -> List[str]:
    """Parse tags from Stack Overflow format like '<php><arrays><mapping>'"""
    if not tags_str:
        return []
    
    # Extract tags between < and >
    tag_matches = re.findall(r'<([^>]+)>', tags_str)
    return tag_matches


def determine_language_from_tags(tags: List[str]) -> Optional[str]:
    """Determine programming language from tags"""
    language_mapping = {
        'javascript': 'javascript',
        'python': 'python',
        'java': 'java',
        'php': 'php',
        'c#': 'csharp',
        'c++': 'cpp',
        'c': 'c',
        'ruby': 'ruby',
        'go': 'go',
        'rust': 'rust',
        'swift': 'swift',
        'kotlin': 'kotlin',
        'scala': 'scala',
        'sql': 'sql',
        'html': 'html',
        'css': 'css',
        'typescript': 'typescript',
        'r': 'r',
        'matlab': 'matlab',
        'perl': 'perl',
        'shell': 'shell',
        'bash': 'bash',
        'powershell': 'powershell'
    }
    
    for tag in tags:
        if tag.lower() in language_mapping:
            return language_mapping[tag.lower()]
    
    return None


def determine_framework_from_tags(tags: List[str]) -> Optional[str]:
    """Determine framework from tags"""
    framework_mapping = {
        'react': 'react',
        'vue.js': 'vue',
        'angular': 'angular',
        'django': 'django',
        'flask': 'flask',
        'express': 'express',
        'spring': 'spring',
        'laravel': 'laravel',
        'rails': 'rails',
        'jquery': 'jquery',
        'node.js': 'nodejs',
        'asp.net': 'aspnet',
        '.net': 'dotnet',
        'xamarin': 'xamarin',
        'flutter': 'flutter',
        'ionic': 'ionic'
    }
    
    for tag in tags:
        if tag.lower() in framework_mapping:
            return framework_mapping[tag.lower()]
    
    return None


def convert_question_to_entry(question: StackOverflowQuestion, answers: List[StackOverflowAnswer]) -> Dict[str, Any]:
    """Convert a Stack Overflow question with answers to the bug tracking format"""
    
    # Extract code from question body
    question_code = extract_code_from_html(question.body)
    question_body_clean = strip_html_tags(question.body)
    
    # Find the accepted answer (highest scoring solution)
    best_answer = None
    if answers:
        if question.accepted_answer_id:
            best_answer = next((ans for ans in answers if ans.id == question.accepted_answer_id), None)
        if not best_answer:
            # If no accepted answer, take the highest scoring one
            best_answer = max(answers, key=lambda x: x.score)
    
    # Extract solution from best answer
    resolution = ""
    solution_code = ""
    if best_answer:
        resolution = strip_html_tags(best_answer.body)
        solution_code = extract_code_from_html(best_answer.body)
    
    # Determine programming context
    language = determine_language_from_tags(question.tags)
    framework = determine_framework_from_tags(question.tags)
    
    # Determine entry type and severity based on score and view count
    entry_type = "solution" if best_answer else "bug"
    
    # Determine severity based on score and view count
    severity = "low"
    if question.score >= 50 or question.view_count >= 10000:
        severity = "high"
    elif question.score >= 10 or question.view_count >= 1000:
        severity = "medium"
    
    # Build the entry
    entry = {
        "type": entry_type,
        "title": question.title,
        "body": question_body_clean,
        "code": question_code if question_code else None,
        "resolution": resolution if resolution else None,
        "severity": severity,
        "tags": question.tags,
        "metadata": {
            "language": language,
            "framework": framework,
            "stackoverflow_question_id": str(question.id),
            "stackoverflow_score": question.score,
            "stackoverflow_view_count": question.view_count,
            "stackoverflow_creation_date": question.creation_date,
            "stackoverflow_owner": question.owner_display_name,
        },
        "idempotency_key": f"stackoverflow-{question.id}",
        "related_ids": []  # Could link to similar questions in the future
    }
    
    # Add solution code if we have it and it's different from question code
    if solution_code and solution_code != question_code:
        if entry["code"]:
            entry["code"] += f"\n\n# Solution Code:\n{solution_code}"
        else:
            entry["code"] = solution_code
    
    # Remove None values to keep the JSON clean
    entry = {k: v for k, v in entry.items() if v is not None}
    if "metadata" in entry:
        entry["metadata"] = {k: v for k, v in entry["metadata"].items() if v is not None}
    
    return entry


def process_jsonl_file(input_file: str, output_file: str):
    """Process the questions.jsonl file and convert to the new format"""
    
    print(f"Processing {input_file}...")
    
    # Read all lines and group questions with their answers
    questions_map: Dict[int, StackOverflowQuestion] = {}
    answers_map: Dict[int, List[StackOverflowAnswer]] = {}
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 100 == 0:
                print(f"Processed {line_num} lines...")
                
            try:
                data = json.loads(line.strip())
                
                if data.get('PostTypeId') == 1:  # Question
                    question = StackOverflowQuestion(
                        id=data['Id'],
                        title=data['Title'],
                        body=data['Body'],
                        tags=parse_tags(data.get('Tags', '')),
                        score=data.get('Score', 0),
                        view_count=data.get('ViewCount', 0),
                        creation_date=data.get('CreationDate', ''),
                        owner_display_name=data.get('OwnerDisplayName'),
                        accepted_answer_id=data.get('AcceptedAnswerId')
                    )
                    questions_map[question.id] = question
                    
                elif data.get('PostTypeId') == 2:  # Answer
                    answer = StackOverflowAnswer(
                        id=data['Id'],
                        parent_id=data['ParentId'],
                        body=data['Body'],
                        score=data.get('Score', 0),
                        creation_date=data.get('CreationDate', ''),
                        owner_display_name=data.get('OwnerDisplayName')
                    )
                    
                    if answer.parent_id not in answers_map:
                        answers_map[answer.parent_id] = []
                    answers_map[answer.parent_id].append(answer)
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"Error processing line {line_num}: {e}")
                continue
    
    print(f"Found {len(questions_map)} questions and {sum(len(answers) for answers in answers_map.values())} answers")
    
    # Convert to the new format
    converted_entries = []
    
    for question_id, question in questions_map.items():
        answers = answers_map.get(question_id, [])
        entry = convert_question_to_entry(question, answers)
        converted_entries.append(entry)
    
    # Write the converted data
    print(f"Writing {len(converted_entries)} entries to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(converted_entries, f, indent=2, ensure_ascii=False)
    
    print(f"Conversion complete! Output saved to {output_file}")
    
    # Print some statistics
    print(f"\nConversion Statistics:")
    print(f"Total entries: {len(converted_entries)}")
    
    type_counts = {}
    severity_counts = {}
    language_counts = {}
    
    for entry in converted_entries:
        entry_type = entry.get('type', 'unknown')
        type_counts[entry_type] = type_counts.get(entry_type, 0) + 1
        
        severity = entry.get('severity', 'unknown')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        language = entry.get('metadata', {}).get('language', 'unknown')
        language_counts[language] = language_counts.get(language, 0) + 1
    
    print(f"Types: {type_counts}")
    print(f"Severities: {severity_counts}")
    print(f"Top languages: {dict(sorted(language_counts.items(), key=lambda x: x[1], reverse=True)[:10])}")


def main():
    """Main entry point"""
    input_file = Path(__file__).parent / "questions.jsonl"
    output_file = Path(__file__).parent / "converted.json"
    
    if not input_file.exists():
        print(f"Input file {input_file} not found!")
        return
    
    try:
        process_jsonl_file(str(input_file), str(output_file))
    except Exception as e:
        print(f"Error during processing: {e}")
        raise


if __name__ == "__main__":
    main()

"""
Input validation utilities
"""
import re
from typing import List, Tuple


def sanitize_query(query: str) -> str:
    """Sanitize search query"""
    # Remove potentially dangerous characters
    query = query.strip()
    # Allow only alphanumeric, spaces, and common punctuation
    query = re.sub(r'[^\w\s\-\'\.\,\:\!\?]', '', query)
    return query[:200]  # Limit length


def parse_batch_file(content: str) -> List[str]:
    """Parse batch file content into list of queries"""
    lines = content.strip().split('\n')
    queries = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):  # Skip comments
            queries.append(sanitize_query(line))
    return queries[:100]  # Limit to 100 items


def validate_export_filename(filename: str) -> str:
    """Validate and sanitize export filename"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.strip()
    return filename[:100] if filename else "export"


def format_runtime(minutes: int) -> str:
    """Format runtime in minutes to human readable format"""
    if not minutes:
        return "N/A"
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def format_currency(amount: int) -> str:
    """Format currency amount"""
    if not amount:
        return "N/A"
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    return f"${amount:,}"

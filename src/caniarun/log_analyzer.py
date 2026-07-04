import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Define valid performance levels (case-insensitive for robustness)
VALID_LEVELS = [
    "smooth as butter",
    "dope run",
    "meh usable",
    "laggy vibes",
    "trash mode"
]

@dataclass
class ParsedLogLine:
    is_valid: bool
    raw_line: str
    level: Optional[str] = None
    timestamp: Optional[datetime] = None
    message: Optional[str] = None
    issues: List[str] = field(default_factory=list)

@dataclass
class AnalysisReport:
    total_processed: int
    malformed_count: int
    level_counts: Dict[str, int]
    issue_counts: Dict[str, int]
    health_status: str

def parse_log_line(line: str) -> Optional[ParsedLogLine]:
    """
    Parses a log line, validates it, and extracts information.
    Returns None if the line is empty or a comment (should be ignored).
    Returns a ParsedLogLine with is_valid=False if malformed.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None
        
    # Expected pattern: [emoji Level] YYYY-MM-DD HH:MM:SS Message...
    # The emoji can be one or more characters, we'll match everything inside the brackets.
    # We use a permissive regex inside the brackets and strict regex for the timestamp.
    pattern = r'^\[(.*?)\] (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.+)$'
    match = re.match(pattern, line)
    
    if not match:
        return ParsedLogLine(is_valid=False, raw_line=line)
        
    raw_level, ts_str, message = match.groups()
    
    # 1. Validate Timestamp
    try:
        timestamp = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ParsedLogLine(is_valid=False, raw_line=line)
        
    # 2. Validate Performance Level
    # Extract just the text part of the level, ignoring emojis
    # We'll just check if any of the VALID_LEVELS substrings are in the raw_level (case-insensitive)
    matched_level = None
    lower_raw_level = raw_level.lower()
    for valid in VALID_LEVELS:
        if valid in lower_raw_level:
            # Map back to standard emoji representation
            mapping = {
                "smooth as butter": "🧈 Smooth as butter",
                "dope run": "🔥 Dope run",
                "meh usable": "😐 Meh usable",
                "laggy vibes": "🐌 Laggy vibes",
                "trash mode": "🗑️ Trash mode"
            }
            matched_level = mapping[valid]
            break
            
    if not matched_level:
        return ParsedLogLine(is_valid=False, raw_line=line)
        
    # 3. Extract issues
    issues = []
    if "GPU incompatible" in message: issues.append("GPU Incompatible")
    if "RAM tight" in message: issues.append("Excessive RAM Usage")
    if "exceeds all memory" in message: issues.append("Crash Risk")
    if "CPU offloading" in message: issues.append("CPU Offloading")
    if "low bandwidth" in message: issues.append("Low Bandwidth")
    if "cannot-run" in message and "Crash Risk" not in issues: issues.append("Crash Risk")
    if "Trash mode" in matched_level and not issues: issues.append("Crash Risk") # Fallback
    
    return ParsedLogLine(
        is_valid=True,
        raw_line=line,
        level=matched_level,
        timestamp=timestamp,
        message=message,
        issues=issues
    )

def categorize_issues(parsed_lines: List[ParsedLogLine]) -> Dict[str, int]:
    """Counts occurrences of each issue category."""
    counts = {
        "GPU Incompatible": 0,
        "Excessive RAM Usage": 0,
        "Crash Risk": 0,
        "CPU Offloading": 0,
        "Low Bandwidth": 0
    }
    
    for line in parsed_lines:
        if not line.is_valid:
            continue
        for issue in line.issues:
            if issue in counts:
                counts[issue] += 1
                
    return counts

def compute_health(level_counts: Dict[str, int]) -> str:
    """Determine overall system health based on the most frequent performance level."""
    if not level_counts:
        return "Unknown"
        
    most_frequent = max(level_counts.items(), key=lambda x: x[1])
    return most_frequent[0]

def analyze_log_file(filepath: str) -> AnalysisReport:
    """Reads a log file and produces an AnalysisReport."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    parsed_lines = []
    for line in lines:
        parsed = parse_log_line(line)
        if parsed is not None:
            parsed_lines.append(parsed)
            
    total = len(parsed_lines)
    malformed = sum(1 for p in parsed_lines if not p.is_valid)
    
    level_counts = {
        "🧈 Smooth as butter": 0,
        "🔥 Dope run": 0,
        "😐 Meh usable": 0,
        "🐌 Laggy vibes": 0,
        "🗑️ Trash mode": 0
    }
    
    for p in parsed_lines:
        if p.is_valid and p.level in level_counts:
            level_counts[p.level] += 1
            
    issue_counts = categorize_issues(parsed_lines)
    health = compute_health(level_counts) if total > malformed else "Unknown"
    
    return AnalysisReport(
        total_processed=total,
        malformed_count=malformed,
        level_counts=level_counts,
        issue_counts=issue_counts,
        health_status=health
    )

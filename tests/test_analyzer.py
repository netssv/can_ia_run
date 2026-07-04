import pytest
import os
from caniarun.log_analyzer import parse_log_line, analyze_log_file

def test_parse_valid_line():
    line = "[🧈 Smooth as butter] 2026-07-03 12:44:02 Llama 3 8B @ Q4_K_M — 4.5 GB VRAM, no issues"
    parsed = parse_log_line(line)
    
    assert parsed is not None
    assert parsed.is_valid is True
    assert parsed.level == "🧈 Smooth as butter"
    assert parsed.timestamp.year == 2026
    
def test_parse_case_insensitive_no_emoji():
    line = "[Smooth as butter] 2026-07-03 12:44:02 AI running smoothly, no issues"
    parsed = parse_log_line(line)
    
    assert parsed is not None
    assert parsed.is_valid is True
    assert parsed.level == "🧈 Smooth as butter" # Should map back to standard

def test_parse_malformed_lines():
    # Bad timestamp
    assert parse_log_line("[🔥 Dope run] 2025/01/10 14:50:00 msg").is_valid is False
    
    # Invalid level
    assert parse_log_line("[Not a real level] 2026-07-03 12:44:02 msg").is_valid is False
    
    # Missing brackets
    assert parse_log_line("Smooth as butter 2026-07-03 12:44:02 msg").is_valid is False
    
def test_ignore_comments_and_empty():
    assert parse_log_line("# This is a comment") is None
    assert parse_log_line("   ") is None

def test_issue_categorization():
    line = "[🐌 Laggy vibes] 2026-07-03 12:44:02 Llama 3 70B — RAM tight, CPU offloading, low bandwidth"
    parsed = parse_log_line(line)
    
    assert "Excessive RAM Usage" in parsed.issues
    assert "CPU Offloading" in parsed.issues
    assert "Low Bandwidth" in parsed.issues
    
def test_analyze_clean_file():
    path = os.path.join(os.path.dirname(__file__), "sample_clean.log")
    report = analyze_log_file(path)
    
    assert report.total_processed == 5
    assert report.malformed_count == 0
    assert report.level_counts["🧈 Smooth as butter"] == 1
    assert report.level_counts["🗑️ Trash mode"] == 1
    
    # Issues from clean log: RAM tight x2, CPU offloading x1, Crash Risk x1
    assert report.issue_counts["Excessive RAM Usage"] == 2
    assert report.issue_counts["CPU Offloading"] == 1
    assert report.issue_counts["Crash Risk"] == 1
    
def test_analyze_dirty_file():
    path = os.path.join(os.path.dirname(__file__), "sample_dirty.log")
    report = analyze_log_file(path)
    
    # Valid lines: Smooth as butter, Trash Mode, Laggy vibes, Meh usable (4 lines)
    assert report.total_processed == 7 # Total non-empty, non-comment lines
    assert report.malformed_count == 3 # 3 broken lines
    
    assert report.level_counts["🧈 Smooth as butter"] == 1
    assert report.level_counts["🗑️ Trash mode"] == 1

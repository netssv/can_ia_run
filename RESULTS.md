# Log Analyzer — Integration Results & Reflection

This document contains the required deliverables for the Python Log Analysis Script requirement.

## 1. Technical Reflection

### What parts were suggested or supported by AI?
I utilized AI capabilities primarily for two tasks:
- **Regular Expressions:** I used AI support to quickly draft the core regex `r'^\[(.*?)\] (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.+)$'` which captures the emoji block, the precise timestamp layout, and the trailing message. I validated and confirmed this regex before implementing it.
- **Rich Output Formatting:** I used AI to remember the exact syntax for rendering progress bars in the console (`█` and `░` characters) and formatting the Rich `Table` and `Panel` classes.

### What parts were my own decisions?
- **Validation Criteria:** I explicitly defined that any line lacking the `[ ]` brackets, a perfectly formatted ISO timestamp, or a known performance level (case-insensitive) is mathematically categorized as `is_valid=False`. 
- **Error Handling of Lines:** Rather than crashing the parser or raising Exceptions on malformed lines, I made the deliberate decision to wrap the line in a `ParsedLogLine` with `is_valid=False` and count them towards a `malformed_count`. This ensures the script is robust enough to process noisy logs without interruption.
- **Categorization Definitions:** I defined the 5 core categories of system limits:
  1. **GPU Incompatible**: Detected if hardware has `vram_gb=None` or log says `GPU incompatible`.
  2. **Excessive RAM Usage**: Detected if log says `RAM tight`.
  3. **Crash Risk**: Detected if log says `exceeds all memory` or `cannot-run` or falls into `Trash mode` with no other issues.
  4. **CPU Offloading**: Detected if log says `CPU offloading`.
  5. **Low Bandwidth**: Detected if log says `low bandwidth` (specifically mapped to < 10 tok/s).

### Example of AI Correction
An AI suggestion initially proposed using `.split(" ")` to separate the performance level, timestamp, and message. I rejected this approach because performance levels contain spaces (e.g., "Smooth as butter") and the timestamp contains spaces. The `split(" ")` would have created an unpredictable number of tokens. I decided to override the suggestion and use the structured Regular Expression instead to guarantee exact group extraction.

### Final Reflection
Using AI as a support tool accelerated the boilerplate (regex generation and UI layout) but could not substitute for architectural decision-making. Defining *what constitutes a malformed line* and *how to categorize a hardware limit* required human domain knowledge about how LLMs consume VRAM and bandwidth. AI is a fantastic copilot for syntax, but the business logic and fault-tolerance boundaries remain entirely the engineer's responsibility.

---

## 2. Test Evidence (Expected vs Actual Results)

We ran the analyzer on two test files: `tests/sample_clean.log` and `tests/sample_dirty.log`.

### Test 1: `sample_clean.log`
**Description:** A perfectly generated log from the `log_emitter.py`. Contains 5 model evaluations.
- **Expected:** 5 events processed, 0 malformed lines. 
- **Actual:** `Total Processed: 5`, `Malformed: 0`. 
- **Issues Detected:** 2 Excessive RAM Usage, 1 CPU Offloading, 1 Crash Risk. The results matched the expectations perfectly because all 5 lines adhered strictly to the regex pattern and contained valid timestamps and recognized performance levels.

### Test 2: `sample_dirty.log`
**Description:** A hand-modified log containing broken lines, bad timestamps, random text, and unknown performance levels.
- **Expected:** The analyzer should skip the comment line, skip the blank line, process the 4 valid lines (even with case-insensitive levels like `[Smooth as Butter]`), and flag exactly 3 lines as malformed (one for broken timestamp, one for bad format, one for unhandled performance level).
- **Actual:** `Total Processed: 7`, `Malformed: 3`. 
- **Match Reason:** The analyzer perfectly executed the validation criteria. The line `[🔥 Dope run] 2025/01/10 14:50:00 Bad timestamp format` was flagged because it uses `/` instead of `-`, failing the regex match. The random text line failed to match the `[ ]` prefix. The case-insensitive levels (`Smooth as Butter` and `Trash Mode`) were successfully normalized and processed.

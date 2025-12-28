# Quick Run Usage Guide

## Command Line Flags

### `--quick`
**Quick mode**: Only process the first 10 diaries of each year.

- Useful for testing changes to prompts or settings
- Processes a representative sample from each year
- Maintains chronological order within each year

**Example:**
```bash
uv run generate_diary.py --quick
```

### `--overwrite`
**Overwrite mode**: Regenerate everything, ignoring `progress.json`.

- Forces regeneration of all diaries, even if they already exist
- Useful when you've changed prompts, model, or resume information
- Does not skip any dates based on previous progress

**Example:**
```bash
uv run generate_diary.py --overwrite
```

### Combined Usage

**Quick run with overwrite** (most common for testing):
```bash
uv run generate_diary.py --quick --overwrite
```

This combination:
- Processes first 10 diaries per year (quick mode)
- Regenerates them even if they exist (overwrite mode)
- Perfect for rapid iteration when testing prompt changes

## Other Existing Flags

### `--test`
Test mode - only process first 3 days total (across all years).

**Example:**
```bash
uv run generate_diary.py --test
```

### `--input`
Specify custom input file path (default: `data/conversations_by_date.json`).

**Example:**
```bash
uv run generate_diary.py --input my_conversations.json
```

### `--config`
Specify custom config file path (default: `config.yaml`).

**Example:**
```bash
uv run generate_diary.py --config my_config.yaml
```

## Usage Examples

### 1. Development/Testing Workflow
When tweaking prompts or resume generation:
```bash
# Quick test with 10 diaries per year, regenerate them
uv run generate_diary.py --quick --overwrite
```

### 2. Full Regeneration
When you've updated the resume or made significant prompt changes:
```bash
# Regenerate all diaries from scratch
uv run generate_diary.py --overwrite
```

### 3. Quick Preview
Check how diaries look with current settings:
```bash
# Generate first 10 per year (skip if they exist)
uv run generate_diary.py --quick
```

### 4. Normal Run
Continue from where you left off:
```bash
# Process only new dates not in progress.json
uv run generate_diary.py
```

### 5. Very Quick Test
Fastest way to test if everything works:
```bash
# Just 3 days total
uv run generate_diary.py --test
```

## Quick Mode Details

When using `--quick`, the system:

1. **Loads all conversations** from the input JSON
2. **Groups dates by year** (e.g., 2022, 2023, 2024, 2025)
3. **Selects first 10 dates** from each year chronologically
4. **Processes only those dates**

Example output:
```
⚡ Running in quick mode (first 10 diaries per year)...
📅 Preparing to generate diaries for 40 days...

Generating diaries: 100%|████████████| 40/40 [01:23<00:00,  2.09s/it]

✅ Quick mode completed! Processed 40 diaries.
```

## Overwrite Mode Details

When using `--overwrite`, the system:

1. **Ignores `progress.json`** - all dates are considered "not processed"
2. **Regenerates diary files** - overwrites existing `.md` files
3. **Still updates `progress.json`** - tracks completion normally

This is useful when:
- You've changed the prompt structure
- You've updated the annual resume generation
- You've switched to a different LLM model
- You want to regenerate summaries with new context

## Tips

### Fastest Iteration Cycle
For rapid development and testing:
```bash
# 1. Make changes to prompts/code
# 2. Test with quick mode
uv run generate_diary.py --quick --overwrite

# 3. Check output in output/diaries/
# 4. Repeat as needed
```

### When to Use Full Regeneration
```bash
# After finalizing prompt changes
uv run generate_diary.py --overwrite

# After updating resume information
uv run generate_diary.py --overwrite
```

### Resume Normal Operation
After testing with `--quick` or `--overwrite`:
```bash
# Process remaining dates normally
uv run generate_diary.py
```

## Performance Estimates

Based on typical processing speeds:

- **Quick mode** (~40 diaries): ~1-2 minutes
- **Test mode** (3 diaries): ~10-20 seconds
- **Full generation** (hundreds of diaries): Varies by total count
- **Overwrite all** (hundreds of diaries): Same as full generation

## Output Location

All generated diaries are saved to:
```
output/diaries/
├── 2022/
│   ├── 2022-01-15-日记标题.md
│   └── 2022-年度总结.md
├── 2023/
├── 2024/
└── 2025/
```

Annual summaries are generated after all diaries for each year.

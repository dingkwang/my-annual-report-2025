#!/usr/bin/env python3
"""
Main script to generate diaries from OpenAI conversation exports
"""

import argparse
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

from diary_generator import DiaryGenerator
from parse_conversations import parse_conversations


def main():
    parser = argparse.ArgumentParser(description="Generate diaries from OpenAI conversation exports")
    parser.add_argument(
        "zip_or_json",
        nargs="?",
        type=str,
        default=None,
        help="Path to ZIP file containing conversations.json or path to conversations_by_date.json"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="(Deprecated) Use positional argument instead. Path to conversations_by_date.json file"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode - only process first 3 days"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode - only process first 10 diaries of each year"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite mode - regenerate everything, ignore progress.json"
    )

    args = parser.parse_args()

    # Determine input file
    input_file = None
    conversations_by_date_json = None
    temp_dir = None
    
    # Priority: positional argument > --input flag > default
    source_file = args.zip_or_json or args.input or "data/conversations_by_date.json"
    
    # Check if it's a zip file
    if source_file.endswith('.zip'):
        if not Path(source_file).exists():
            print(f"❌ Error: ZIP file '{source_file}' not found!")
            sys.exit(1)
        
        print(f"📦 Extracting conversations from ZIP file: {source_file}")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Extract conversations.json from zip
        with zipfile.ZipFile(source_file, 'r') as zip_ref:
            # Find conversations.json in the zip
            conversations_json = None
            for name in zip_ref.namelist():
                if name.endswith('conversations.json'):
                    conversations_json = name
                    break
            
            if not conversations_json:
                print("❌ Error: conversations.json not found in ZIP file!")
                sys.exit(1)
            
            # Extract it
            zip_ref.extract(conversations_json, temp_dir)
            conversations_json_path = Path(temp_dir) / conversations_json
        
        print(f"✅ Extracted conversations.json")
        print(f"📊 Parsing conversations and grouping by date...")
        
        # Parse conversations.json to create conversations_by_date
        conversations_by_date = parse_conversations(conversations_json_path)
        
        # Save to temporary file
        conversations_by_date_json = Path(temp_dir) / "conversations_by_date.json"
        with open(conversations_by_date_json, 'w', encoding='utf-8') as f:
            json.dump(conversations_by_date, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created conversations_by_date.json with {len(conversations_by_date)} dates")
        input_file = str(conversations_by_date_json)
    else:
        # It's a JSON file (or default path)
        input_file = source_file
        if not Path(input_file).exists():
            print(f"❌ Error: Input file '{input_file}' not found!")
            sys.exit(1)

    # Load config early to check SSL cert configuration
    import yaml
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Error: Config file '{args.config}' not found!")
        # Clean up temp directory if it was created
        if temp_dir and Path(temp_dir).exists():
            import shutil
            shutil.rmtree(temp_dir)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        # Clean up temp directory if it was created
        if temp_dir and Path(temp_dir).exists():
            import shutil
            shutil.rmtree(temp_dir)
        sys.exit(1)

    # Check API configuration (config already loaded above for SSL cert check)
    if config['llm']['base_url'] == "YOUR_BASE_URL_HERE":
        print("❌ Error: Please update the LLM configuration in config.yaml")
        # Clean up temp directory if it was created
        if temp_dir and Path(temp_dir).exists():
            import shutil
            shutil.rmtree(temp_dir)
        sys.exit(1)

    # Initialize generator
    print("🚀 Initializing Diary Generator...")
    generator = DiaryGenerator(args.config)

    # Test mode - limit to first 3 days
    if args.test:
        print("\n🧪 Running in test mode (first 3 days only)...")
        with open(input_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)

        # Get first 3 dates
        test_dates = sorted(all_data.keys())[:30]
        test_data = {date: all_data[date] for date in test_dates}

        # Save test data temporarily
        test_file = "test_conversations.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False)

        # Generate diaries for test data
        generator.generate_all_diaries(test_file, overwrite=args.overwrite)

        # Clean up
        os.remove(test_file)
        if temp_dir and Path(temp_dir).exists():
            import shutil
            shutil.rmtree(temp_dir)

        print("\n✅ Test completed! Check the output/diaries folder for results.")
        print("   If satisfied, run without --test flag to process all data.")
    elif args.quick:
        # Quick mode - first 10 diaries per year
        print("\n⚡ Running in quick mode (first 10 diaries per year)...")
        with open(input_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)

        # Group by year and take first 10 from each
        from collections import defaultdict
        by_year = defaultdict(list)
        for date in sorted(all_data.keys()):
            year = date.split("-")[0]
            by_year[year].append(date)

        # Take first 10 from each year
        quick_dates = []
        for year in sorted(by_year.keys()):
            quick_dates.extend(by_year[year][:10])

        quick_data = {date: all_data[date] for date in quick_dates}

        # Save quick data temporarily
        quick_file = "quick_conversations.json"
        with open(quick_file, 'w', encoding='utf-8') as f:
            json.dump(quick_data, f, ensure_ascii=False)

        # Generate diaries for quick data
        if args.overwrite:
            print("🔄 Overwrite mode enabled - regenerating all diaries")
        generator.generate_all_diaries(quick_file, overwrite=args.overwrite)

        # Clean up
        os.remove(quick_file)
        if temp_dir and Path(temp_dir).exists():
            import shutil
            shutil.rmtree(temp_dir)

        print(f"\n✅ Quick mode completed! Processed {len(quick_dates)} diaries.")
        print("   Check the output/diaries folder for results.")
    else:
        # Generate all diaries
        if args.overwrite:
            print("\n🔄 Overwrite mode enabled - regenerating all diaries")
        generator.generate_all_diaries(input_file, overwrite=args.overwrite)
        
        # Clean up temp directory
        if temp_dir and Path(temp_dir).exists():
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
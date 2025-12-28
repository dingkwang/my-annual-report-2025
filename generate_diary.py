#!/usr/bin/env python3
"""
Main script to generate diaries from OpenAI conversation exports
"""

import argparse
import os
import sys
from pathlib import Path

from diary_generator import DiaryGenerator

try:
    from corp_cert import ensure_corp_cert_bundle
except ImportError:
    # If corp_cert.py doesn't exist (e.g., in public repo), define a no-op version
    def ensure_corp_cert_bundle() -> str:
        return ""


def main():
    parser = argparse.ArgumentParser(description="Generate diaries from OpenAI conversation exports")
    parser.add_argument(
        "--input",
        type=str,
        default="data/conversations_by_date.json",
        help="Path to conversations_by_date.json file"
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

    # Load config early to check SSL cert configuration
    import yaml
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Error: Config file '{args.config}' not found!")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)

    # Setup SSL certificate only if configured
    ssl_cert_path = config.get('llm', {}).get('ssl_cert')
    if ssl_cert_path:
        # SSL cert is configured, try to ensure it exists
        try:
            actual_cert_path = ensure_corp_cert_bundle()
            if actual_cert_path:
                print(f"🔐 Using SSL certificate: {actual_cert_path}")
            else:
                print(f"⚠️  SSL cert configured but corp_cert.py not available")
        except Exception as e:
            print(f"⚠️  Failed to setup SSL certificate: {e}")
            print("   Continuing without SSL certificate...")
    else:
        print("ℹ️  No SSL certificate configured, using default SSL settings")

    # Check if input file exists
    if not Path(args.input).exists():
        print(f"❌ Error: Input file '{args.input}' not found!")
        sys.exit(1)

    # Check API configuration (config already loaded above for SSL cert check)
    if config['llm']['base_url'] == "YOUR_BASE_URL_HERE":
        print("❌ Error: Please update the LLM configuration in config.yaml")
        print("   Set your base_url and api_key for grok-4-1-fast-non-reasoning")
        sys.exit(1)

    # Initialize generator
    print("🚀 Initializing Diary Generator...")
    generator = DiaryGenerator(args.config)

    # Test mode - limit to first 3 days
    if args.test:
        print("\n🧪 Running in test mode (first 3 days only)...")
        import json
        with open(args.input, 'r', encoding='utf-8') as f:
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

        print("\n✅ Test completed! Check the output/diaries folder for results.")
        print("   If satisfied, run without --test flag to process all data.")
    elif args.quick:
        # Quick mode - first 10 diaries per year
        print("\n⚡ Running in quick mode (first 10 diaries per year)...")
        import json
        with open(args.input, 'r', encoding='utf-8') as f:
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

        print(f"\n✅ Quick mode completed! Processed {len(quick_dates)} diaries.")
        print("   Check the output/diaries folder for results.")
    else:
        # Generate all diaries
        if args.overwrite:
            print("\n🔄 Overwrite mode enabled - regenerating all diaries")
        generator.generate_all_diaries(args.input, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
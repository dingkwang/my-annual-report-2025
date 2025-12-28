#!/usr/bin/env python3
"""
Test script for annual resume generation functionality
"""

import json
import yaml
from diary_generator import DiaryGenerator

def test_annual_resume():
    """Test annual resume generation and usage"""

    print("=" * 60)
    print("Testing Annual Resume Functionality")
    print("=" * 60)

    # Test 1: Check if _annual_resume exists in config
    print("\n1. Checking if _annual_resume exists in config.yaml...")
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if "_annual_resume" in config:
        print("✓ _annual_resume found in config.yaml")
        print("Content:")
        for year, desc in config["_annual_resume"].items():
            print(f"  {year}: {desc}")
    else:
        print("✗ _annual_resume NOT found in config.yaml")

    # Test 2: Initialize DiaryGenerator (should generate if missing)
    print("\n2. Initializing DiaryGenerator...")
    try:
        generator = DiaryGenerator()
        print("✓ DiaryGenerator initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize DiaryGenerator: {str(e)}")
        return

    # Test 3: Verify _has_annual_resume() method
    print("\n3. Testing _has_annual_resume() method...")
    has_resume = generator._has_annual_resume()
    print(f"   Result: {has_resume}")
    if has_resume:
        print("✓ _annual_resume is present and valid")
    else:
        print("✗ _annual_resume is missing or invalid")

    # Test 4: Test date-aware resume for different years
    print("\n4. Testing date-aware resume generation...")
    test_dates = ["2022-06-15", "2023-09-20", "2024-12-01", "2025-11-15"]

    for date in test_dates:
        print(f"\n   Date: {date}")
        resume = generator._get_date_aware_resume(date)
        print(f"   Resume context:")
        for line in resume.split("\n"):
            print(f"     {line}")

    # Test 5: Verify config.yaml was updated
    print("\n5. Verifying config.yaml was updated...")
    with open("config.yaml", "r", encoding="utf-8") as f:
        updated_config = yaml.safe_load(f)

    if "_annual_resume" in updated_config:
        print("✓ _annual_resume section exists in config.yaml")
        required_keys = ["2021_and_before", "2022", "2023", "2024", "2025"]
        missing_keys = [k for k in required_keys if k not in updated_config["_annual_resume"]]
        if not missing_keys:
            print("✓ All required year keys are present")
        else:
            print(f"✗ Missing keys: {missing_keys}")
    else:
        print("✗ _annual_resume section NOT found in config.yaml")

    # Test 6: Check that prompt building works
    print("\n6. Testing prompt building with date-aware resume...")
    try:
        test_date = "2023-05-15"
        processed_convs = "测试对话内容"
        messages = generator._build_prompt(test_date, processed_convs)

        # Check that resume is in the system prompt
        system_prompt = messages[0]["content"]
        if "2021及之前" in system_prompt:
            print("✓ Date-aware resume included in system prompt")
            # Verify it doesn't include future years
            if "2024" not in system_prompt and "2025" not in system_prompt:
                print("✓ Future years correctly excluded for 2023 date")
            else:
                print("✗ Future years incorrectly included!")
        else:
            print("✗ Resume not found in system prompt")

        # Check that customer_requirements is included
        if "requirements" in generator.example_config:
            reqs = generator.example_config["requirements"]
            if reqs in system_prompt:
                print("✓ Customer requirements included in prompt")
            else:
                print("✗ Customer requirements not found in prompt")

    except Exception as e:
        print(f"✗ Failed to build prompt: {str(e)}")

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_annual_resume()

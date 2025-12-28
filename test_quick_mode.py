#!/usr/bin/env python3
"""
Test script for quick mode functionality
"""

import json
from collections import defaultdict

def test_quick_mode_logic():
    """Test that quick mode correctly selects first 10 diaries per year"""

    # Create sample data with dates from multiple years
    sample_data = {}
    years = ["2022", "2023", "2024", "2025"]

    for year in years:
        # Create 20 dates per year (more than the 10 limit)
        for i in range(1, 21):
            date = f"{year}-01-{i:02d}"
            sample_data[date] = {"messages": []}

    print("Sample data created:")
    print(f"Total dates: {len(sample_data)}")

    # Simulate quick mode logic
    by_year = defaultdict(list)
    for date in sorted(sample_data.keys()):
        year = date.split("-")[0]
        by_year[year].append(date)

    print("\nDates per year:")
    for year in sorted(by_year.keys()):
        print(f"  {year}: {len(by_year[year])} dates")

    # Take first 10 from each year
    quick_dates = []
    for year in sorted(by_year.keys()):
        selected = by_year[year][:10]
        quick_dates.extend(selected)
        print(f"\n{year} - Selected first 10:")
        for date in selected:
            print(f"  {date}")

    print(f"\nTotal quick mode dates: {len(quick_dates)}")
    print(f"Expected: {len(years) * 10}")

    if len(quick_dates) == len(years) * 10:
        print("✅ Quick mode logic works correctly!")
    else:
        print("❌ Quick mode logic failed!")

    # Verify first and last dates are correct for each year
    print("\nVerifying date selection:")
    for year in years:
        year_dates = [d for d in quick_dates if d.startswith(year)]
        first = year_dates[0]
        last = year_dates[-1]
        print(f"  {year}: {first} to {last}")

        if first == f"{year}-01-01" and last == f"{year}-01-10":
            print(f"    ✅ Correct range for {year}")
        else:
            print(f"    ❌ Wrong range for {year}")

if __name__ == "__main__":
    test_quick_mode_logic()

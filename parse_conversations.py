#!/usr/bin/env python3
"""
Parse OpenAI conversations.json and group by date.
"""

import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path


def extract_message_text(message_data):
    """Extract text content from a message."""
    if not message_data or 'message' not in message_data:
        return None

    msg = message_data['message']
    if not msg or 'content' not in msg:
        return None

    content = msg['content']
    author = msg.get('author', {}).get('role', 'unknown')
    create_time = msg.get('create_time')

    # Extract text based on content type
    text = None
    if content.get('content_type') == 'text':
        parts = content.get('parts', [])
        if parts:
            text = '\n'.join(str(part) for part in parts if part)
    elif content.get('content_type') == 'multimodal_text':
        parts = content.get('parts', [])
        text_parts = []
        for part in parts:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict):
                # Handle image_asset_pointer or other types
                if part.get('content_type') == 'image_asset_pointer':
                    text_parts.append('[Image]')
                elif 'text' in part:
                    text_parts.append(part['text'])
        text = '\n'.join(text_parts)
    elif content.get('content_type') == 'code':
        text = content.get('text', '')

    if text and text.strip():
        return {
            'author': author,
            'text': text.strip(),
            'create_time': create_time
        }
    return None


def parse_conversations(json_file):
    """Parse conversations.json and group by date."""
    print(f"Loading {json_file}...")

    with open(json_file, 'r', encoding='utf-8') as f:
        conversations = json.load(f)

    print(f"Found {len(conversations)} conversations")

    # Group by date
    conversations_by_date = defaultdict(list)

    for conv in conversations:
        title = conv.get('title', 'Untitled')
        create_time = conv.get('create_time')
        update_time = conv.get('update_time')

        if not create_time:
            continue

        # Convert timestamp to date
        date = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d')

        # Extract messages from mapping
        mapping = conv.get('mapping', {})
        messages = []

        for node_id, node_data in mapping.items():
            msg = extract_message_text(node_data)
            if msg:
                messages.append(msg)

        if messages:
            conversations_by_date[date].append({
                'title': title,
                'create_time': create_time,
                'update_time': update_time,
                'messages': messages
            })

    return conversations_by_date


def write_markdown_output(conversations_by_date, output_file):
    """Write conversations grouped by date to a markdown file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        # Sort dates in descending order (most recent first)
        sorted_dates = sorted(conversations_by_date.keys(), reverse=True)

        f.write("# OpenAI Conversations by Date\n\n")
        f.write(f"Total days: {len(sorted_dates)}\n\n")

        for date in sorted_dates:
            convs = conversations_by_date[date]
            # Sort conversations by create_time
            convs.sort(key=lambda x: x['create_time'])

            f.write(f"## {date}\n\n")
            f.write(f"**Total conversations: {len(convs)}**\n\n")

            for i, conv in enumerate(convs, 1):
                create_dt = datetime.fromtimestamp(conv['create_time'])
                f.write(f"### {i}. {conv['title']}\n")
                f.write(f"*Time: {create_dt.strftime('%H:%M:%S')}*\n\n")

                for msg in conv['messages']:
                    # Skip system messages and empty content
                    if msg['author'] == 'system':
                        continue

                    author_label = "**User:**" if msg['author'] == 'user' else "**Assistant:**"
                    f.write(f"{author_label}\n")
                    f.write(f"{msg['text']}\n\n")

                f.write("---\n\n")

    print(f"Output written to {output_file}")


def write_json_output(conversations_by_date, output_file):
    """Write conversations grouped by date to a JSON file."""
    # Convert to serializable format
    output = {}
    for date, convs in conversations_by_date.items():
        output[date] = convs

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"JSON output written to {output_file}")


def print_summary(conversations_by_date):
    """Print summary statistics."""
    sorted_dates = sorted(conversations_by_date.keys(), reverse=True)
    total_conversations = sum(len(convs) for convs in conversations_by_date.values())

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total days with conversations: {len(sorted_dates)}")
    print(f"Total conversations: {total_conversations}")
    print(f"Date range: {sorted_dates[-1]} to {sorted_dates[0]}")
    print("\nTop 10 most active days:")

    days_by_count = [(date, len(convs)) for date, convs in conversations_by_date.items()]
    days_by_count.sort(key=lambda x: x[1], reverse=True)

    for date, count in days_by_count[:10]:
        print(f"  {date}: {count} conversations")


if __name__ == '__main__':
    input_file = Path(__file__).parent / 'data' / 'conversations.json'
    output_md = Path(__file__).parent / 'data' / 'conversations_by_date.md'
    output_json = Path(__file__).parent / 'data' / 'conversations_by_date.json'

    # Parse conversations
    conversations_by_date = parse_conversations(input_file)

    # Write outputs
    write_markdown_output(conversations_by_date, output_md)
    write_json_output(conversations_by_date, output_json)

    # Print summary
    print_summary(conversations_by_date)

    print("\nDone!")

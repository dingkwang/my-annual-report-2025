#!/usr/bin/env python3
"""
Web interface for Diary Generator
"""

import json
import os
import tempfile
import yaml
import zipfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename
from diary_generator import DiaryGenerator
from parse_conversations import parse_conversations

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# Handle file too large error
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': '文件太大！请确保 ZIP 文件小于 500MB'}), 413

# Store generation status
generation_status = {}

@app.route('/')
def index():
    """Main page with configuration form"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Handle diary generation request"""
    session_id = request.form.get('session_id', 'default')
    
    # Get configuration from form
    config = {
        'llm': {
            'model': request.form.get('model', 'nvidia/nemotron-3-nano-30b'),
            'base_url': request.form.get('base_url', 'https://openrouter.ai/api/v1'),
            'api_key': request.form.get('api_key', ''),
            'temperature': float(request.form.get('temperature', 0.3))
        },
        'output': {
            'base_dir': f'output/web_sessions/{session_id}/diaries'
        },
        'diary_settings': {
            'min_conversation_length': 10
        },
        'logging': {
            'level': 'INFO',
            'file': f'log/web_{session_id}.log'
        }
    }
    
    # Add optional annual resume if provided
    resume_parts = {}
    for year_key in ['2021_and_before', '2022', '2023', '2024', '2025']:
        value = request.form.get(f'resume_{year_key}', '').strip()
        if value:
            resume_parts[year_key] = value
    
    if resume_parts:
        config['_annual_resume'] = resume_parts
    
    # Get uploaded file
    if 'zip_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['zip_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.zip'):
        return jsonify({'error': 'File must be a ZIP file'}), 400
    
    # Get mode
    mode = request.form.get('mode', 'quick')
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    zip_path = Path(app.config['UPLOAD_FOLDER']) / filename
    file.save(zip_path)
    
    # Create temporary config file
    config_path = Path(app.config['UPLOAD_FOLDER']) / f'config_{session_id}.yaml'
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)
    
    # Extract and parse conversations
    temp_dir = Path(app.config['UPLOAD_FOLDER']) / f'extract_{session_id}'
    temp_dir.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Find conversations.json
        conversations_json = None
        for name in zip_ref.namelist():
            if name.endswith('conversations.json'):
                conversations_json = name
                break
        
        if not conversations_json:
            return jsonify({'error': 'conversations.json not found in ZIP'}), 400
        
        zip_ref.extract(conversations_json, temp_dir)
        conversations_json_path = temp_dir / conversations_json
    
    # Parse conversations
    conversations_by_date = parse_conversations(conversations_json_path)
    
    # Filter by mode
    if mode == 'quick':
        from collections import defaultdict
        by_year = defaultdict(list)
        for date in sorted(conversations_by_date.keys()):
            year = date.split("-")[0]
            by_year[year].append(date)
        
        quick_dates = []
        for year in sorted(by_year.keys()):
            quick_dates.extend(by_year[year][:10])
        
        conversations_by_date = {date: conversations_by_date[date] for date in quick_dates}
    
    # Save conversations
    conversations_path = temp_dir / 'conversations_by_date.json'
    with open(conversations_path, 'w', encoding='utf-8') as f:
        json.dump(conversations_by_date, f, ensure_ascii=False, indent=2)
    
    # Load example config
    example_path = Path('example_diary.json')
    if not example_path.exists():
        return jsonify({'error': 'example_diary.json not found'}), 500
    
    # Initialize generator
    try:
        generator = DiaryGenerator(str(config_path), str(example_path))
        
        # Generate diaries
        generation_status[session_id] = {
            'status': 'processing',
            'total': len(conversations_by_date),
            'completed': 0
        }
        
        generator.generate_all_diaries(str(conversations_path), overwrite=True)
        
        # Collect results
        output_dir = Path(config['output']['base_dir'])
        diary_files = []
        
        for year_dir in sorted(output_dir.glob('*')):
            if year_dir.is_dir():
                for diary_file in sorted(year_dir.glob('????-??-??-*.md')):
                    if '年度总结' not in diary_file.name:
                        date = diary_file.name[:10]
                        title = diary_file.stem[11:]  # Remove date prefix
                        diary_files.append({
                            'date': date,
                            'title': title,
                            'path': str(diary_file.relative_to(output_dir.parent))
                        })
                
                # Add annual summary
                summary_files = list(year_dir.glob('*-年度总结.md'))
                if summary_files:
                    summary_file = summary_files[0]
                    year = year_dir.name
                    diary_files.append({
                        'date': f'{year}-12-31',
                        'title': f'{year}年度总结',
                        'path': str(summary_file.relative_to(output_dir.parent)),
                        'is_summary': True
                    })
        
        generation_status[session_id] = {
            'status': 'completed',
            'total': len(diary_files),
            'completed': len(diary_files),
            'diaries': diary_files,
            'output_dir': str(output_dir)
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'total': len(diary_files),
            'diaries': diary_files
        })
        
    except Exception as e:
        generation_status[session_id] = {
            'status': 'error',
            'error': str(e)
        }
        return jsonify({'error': str(e)}), 500

@app.route('/status/<session_id>')
def get_status(session_id):
    """Get generation status"""
    status = generation_status.get(session_id, {'status': 'not_found'})
    return jsonify(status)

@app.route('/diary/<path:filepath>')
def view_diary(filepath):
    """View a diary file"""
    base_dir = Path('output/web_sessions')
    file_path = base_dir / filepath
    
    if not file_path.exists():
        return "Diary not found", 404
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple markdown to HTML conversion
    import html
    content = html.escape(content)
    content = content.replace('\n', '<br>')
    
    return render_template('diary.html', content=content, filepath=filepath)

@app.route('/download/<session_id>')
def download_results(session_id):
    """Download all generated diaries as ZIP"""
    output_dir = Path(f'output/web_sessions/{session_id}/diaries')
    
    if not output_dir.exists():
        return "Results not found", 404
    
    # Create ZIP file
    zip_path = Path(app.config['UPLOAD_FOLDER']) / f'{session_id}_diaries.zip'
    
    import shutil
    shutil.make_archive(
        str(zip_path.with_suffix('')),
        'zip',
        output_dir
    )
    
    return send_file(zip_path, as_attachment=True, download_name=f'diaries_{session_id}.zip')

if __name__ == '__main__':
    # Create necessary directories
    Path('output/web_sessions').mkdir(parents=True, exist_ok=True)
    Path('log').mkdir(exist_ok=True)
    
    print("🌐 Starting Diary Generator Web Interface...")
    print("📍 Open http://localhost:5000 in your browser")
    
    app.run(debug=True, host='0.0.0.0', port=5005)


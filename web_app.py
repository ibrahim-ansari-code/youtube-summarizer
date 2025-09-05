#!/usr/bin/env python3

import os
import sys
import threading
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import uuid

# add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from youtube_summarizer.crew import YouTubeSummarizer
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

socketio = SocketIO(app, cors_allowed_origins="*")

# keep track of running jobs
active_jobs = {}

class WebProgressCallback:
    # sends progress updates via websocket
    def __init__(self, job_id, socketio_instance):
        self.job_id = job_id
        self.socketio = socketio_instance
        
    def update_progress(self, step, message, progress_percent=None):
        data = {
            'job_id': self.job_id,
            'step': step,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if progress_percent is not None:
            data['progress'] = progress_percent
            
        self.socketio.emit('progress_update', data, room=self.job_id)
        logger.info(f"Progress update: {step} - {message}")

def run_summarization(job_id, youtube_url, language=None, publish_to_gdocs=False, gdocs_title=None):
    # run the actual summarization in background
    progress_callback = WebProgressCallback(job_id, socketio)
    
    try:
        progress_callback.update_progress("starting", "Starting summarization pipeline...", 5)
        
        # setup inputs
        inputs = {
            "youtube_url": youtube_url,
            "language": language,
            "publish_to_gdocs": publish_to_gdocs,
            "gdocs_title": gdocs_title,
        }
        
        # Initialize and run crew
        progress_callback.update_progress("initializing", "Initializing AI agents...", 15)
        crew = YouTubeSummarizer().crew()
        
        progress_callback.update_progress("extracting", "Extracting video transcript...", 25)
        progress_callback.update_progress("processing", "Processing and cleaning transcript...", 45)
        progress_callback.update_progress("summarizing", "Generating AI summary...", 65)
        progress_callback.update_progress("reviewing", "Reviewing summary quality...", 75)
        
        result = crew.kickoff(inputs=inputs)
        
        progress_callback.update_progress("reading_files", "Reading generated files...", 90)
        
        # Read the generated files
        transcript_content = ""
        summary_content = ""
        
        try:
            with open("transcript.md", "r", encoding="utf-8") as f:
                transcript_content = f.read()
        except FileNotFoundError:
            transcript_content = "Transcript file not found."
            
        try:
            with open("SUMMARY.md", "r", encoding="utf-8") as f:
                summary_content = f.read()
        except FileNotFoundError:
            summary_content = "Summary file not found."
        
        # Emit completion
        progress_callback.update_progress("completed", "Summarization completed successfully", 100)
        
        # Send results
        socketio.emit('job_completed', {
            'job_id': job_id,
            'success': True,
            'transcript': transcript_content,
            'summary': summary_content,
            'result': str(result) if result else "Completed successfully"
        }, room=job_id)
        
    except Exception as e:
        logger.error(f"Error in summarization job {job_id}: {str(e)}")
        socketio.emit('job_error', {
            'job_id': job_id,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, room=job_id)
    
    finally:
        # Clean up job
        if job_id in active_jobs:
            del active_jobs[job_id]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video():
    data = request.get_json()
    
    if not data or 'youtube_url' not in data:
        return jsonify({'error': 'YouTube URL is required'}), 400
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Store job info
    active_jobs[job_id] = {
        'url': data['youtube_url'],
        'status': 'queued',
        'created_at': datetime.now()
    }
    
    # Start background processing
    thread = threading.Thread(
        target=run_summarization,
        args=(job_id, data['youtube_url'], data.get('language'), data.get('publish_to_gdocs', False), data.get('gdocs_title'))
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'message': 'Processing started',
        'status': 'queued'
    })

@socketio.on('connect')
def on_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def on_disconnect():
    logger.info('Client disconnected')

@socketio.on('join_job')
def on_join_job(data):
    from flask_socketio import join_room
    job_id = data.get('job_id')
    if job_id:
        join_room(job_id)
        session['job_id'] = job_id
        logger.info(f'Client joined job room: {job_id}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting YouTube Summarizer Web App on port {port}...")
    
    # Determine if we're in production
    is_production = os.environ.get('RENDER') or os.environ.get('PORT')
    
    # Run the app
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=port, 
        debug=not is_production,
        allow_unsafe_werkzeug=True
    )

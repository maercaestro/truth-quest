from flask import Flask, request, jsonify
from flask_cors import CORS
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI
import yt_dlp
import requests
import re
import os
import tempfile
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, firestore
from functools import wraps
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Firebase Admin SDK
try:
    firebase_admin.initialize_app()
    db = firestore.client()
    print("Firebase Admin SDK initialized successfully")
except Exception as e:
    print(f"Firebase Admin SDK initialization error: {e}")
    print("Make sure GOOGLE_APPLICATION_CREDENTIALS environment variable is set")
    db = None

# YouTube API configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube_api = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY) if YOUTUBE_API_KEY else None

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Brave Search API configuration
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')

# FFmpeg path
FFMPEG_PATH = '/opt/homebrew/bin/ffmpeg'

# Usage limits
DAILY_LIMIT = 10  # 10 analyses per day for free users
MONTHLY_LIMIT = 100  # 100 analyses per month for free users

def check_usage_limits(user_uid):
    """Check if user has exceeded their usage limits"""
    if not db:
        return True, "Database not available"
    
    try:
        # Get user's usage document
        user_ref = db.collection('usage').document(user_uid)
        user_doc = user_ref.get()
        
        now = datetime.utcnow()
        today = now.date()
        current_month = f"{now.year}-{now.month:02d}"
        
        if user_doc.exists:
            data = user_doc.to_dict()
            
            # Check daily limit
            last_used_date = data.get('last_used_date', '')
            daily_count = data.get('daily_count', 0)
            
            if last_used_date == str(today):
                if daily_count >= DAILY_LIMIT:
                    return False, f"Daily limit of {DAILY_LIMIT} analyses reached. Try again tomorrow."
            
            # Check monthly limit
            current_month_data = data.get('current_month', '')
            monthly_count = data.get('monthly_count', 0)
            
            if current_month_data == current_month:
                if monthly_count >= MONTHLY_LIMIT:
                    return False, f"Monthly limit of {MONTHLY_LIMIT} analyses reached. Limit resets next month."
        
        return True, None
    except Exception as e:
        print(f"Usage check error: {e}")
        return True, None  # Allow on error

def increment_usage(user_uid):
    """Increment user's usage count"""
    if not db:
        return
    
    try:
        user_ref = db.collection('usage').document(user_uid)
        user_doc = user_ref.get()
        
        now = datetime.utcnow()
        today = str(now.date())
        current_month = f"{now.year}-{now.month:02d}"
        
        if user_doc.exists:
            data = user_doc.to_dict()
            
            # Update daily count
            if data.get('last_used_date') == today:
                daily_count = data.get('daily_count', 0) + 1
            else:
                daily_count = 1
            
            # Update monthly count
            if data.get('current_month') == current_month:
                monthly_count = data.get('monthly_count', 0) + 1
            else:
                monthly_count = 1
            
            user_ref.update({
                'last_used_date': today,
                'daily_count': daily_count,
                'current_month': current_month,
                'monthly_count': monthly_count,
                'last_used_at': firestore.SERVER_TIMESTAMP
            })
        else:
            # Create new usage document
            user_ref.set({
                'last_used_date': today,
                'daily_count': 1,
                'current_month': current_month,
                'monthly_count': 1,
                'created_at': firestore.SERVER_TIMESTAMP,
                'last_used_at': firestore.SERVER_TIMESTAMP
            })
    except Exception as e:
        print(f"Usage increment error: {e}")

def verify_token(f):
    """Decorator to verify Firebase ID token and check usage limits"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            # Verify the token
            decoded_token = auth.verify_id_token(id_token)
            user_uid = decoded_token['uid']
            
            # Check usage limits
            allowed, error_message = check_usage_limits(user_uid)
            if not allowed:
                return jsonify({'error': error_message, 'limit_exceeded': True}), 429
            
            # Add user info to request
            request.user = {
                'uid': user_uid,
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False)
            }
            
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Token verification error: {e}")
            return jsonify({'error': 'Invalid or expired token', 'details': str(e)}), 401
    
    return decorated_function

def fetch_transcript_youtube_oauth(video_id, oauth_token):
    """
    METHOD 1: Fetch transcript using user's YouTube OAuth token
    This allows access to captions that require authentication
    """
    print(f'\n🎬 === YouTube OAuth Method ===')
    
    if not oauth_token:
        print(f'  ❌ No OAuth token provided, skipping...')
        return None
    
    if oauth_token == 'null' or oauth_token == 'undefined':
        print(f'  ❌ Invalid OAuth token value: {oauth_token}')
        return None
        
    try:
        from google.oauth2.credentials import Credentials
        
        print(f'  🔑 Token available, attempting OAuth...')
        print(f'  📹 Video ID: {video_id}')
        
        # Create credentials from OAuth token
        credentials = Credentials(token=oauth_token)
        print(f'  ✅ Credentials object created')
        
        # Build YouTube API client with user credentials
        youtube_oauth = build('youtube', 'v3', credentials=credentials)
        print(f'  ✅ YouTube API client built with OAuth')
        
        # List available captions
        print(f'  📋 Fetching caption list...')
        captions_response = youtube_oauth.captions().list(
            part='snippet',
            videoId=video_id
        ).execute()
        
        if not captions_response.get('items'):
            print('  ⚠️ No captions available via OAuth')
            return None
        
        print(f'  ✅ Found {len(captions_response["items"])} caption tracks')
        
        # Find English caption or first available
        caption_track = None
        for item in captions_response['items']:
            if item['snippet']['language'] == 'en':
                caption_track = item
                break
        if not caption_track:
            caption_track = captions_response['items'][0]
        
        caption_id = caption_track['id']
        print(f'  📝 Found caption track: {caption_track["snippet"]["language"]}')
        
        # Download caption content
        caption_content = youtube_oauth.captions().download(
            id=caption_id,
            tfmt='srt'
        ).execute()
        
        # Parse SRT format
        import re
        # Remove timing lines and sequence numbers
        text = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', caption_content.decode('utf-8'))
        text = re.sub(r'\d+\n', '', text)
        text = ' '.join(text.split('\n'))
        
        # Get video metadata
        video_response = youtube_oauth.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        ).execute()
        
        if video_response.get('items'):
            video_info = video_response['items'][0]
            metadata = {
                'title': video_info['snippet']['title'],
                'uploader': video_info['snippet']['channelTitle'],
                'duration': parse_duration(video_info['contentDetails']['duration']),
                'view_count': int(video_info['statistics'].get('viewCount', 0))
            }
        else:
            metadata = {}
        
        print(f'  ✅ YouTube OAuth transcript fetched: {len(text)} chars')
        return {'text': text, **metadata}
        
    except Exception as e:
        print(f'  ❌ YouTube OAuth failed: {str(e)}')
        return None

def parse_duration(duration_str):
    """Parse ISO 8601 duration to seconds"""
    import re
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
    return 0

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([^&\s]+)',
        r'(?:youtube\.com\/embed\/)([^?\s]+)',
        r'(?:youtube\.com\/v\/)([^?\s]+)',
        r'(?:youtu\.be\/)([^?\s]+)',
        r'(?:youtube\.com\/shorts\/)([^?\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def fetch_transcript_whisper(video_id):
    """Fetch transcript using OpenAI Whisper API"""
    if not openai_client:
        raise Exception('OpenAI API key not configured')
    
    print(f'DEBUG: Downloading audio for video: {video_id}')
    
    # Create temporary directory for audio file
    temp_dir = tempfile.mkdtemp()
    audio_file_path = os.path.join(temp_dir, 'audio.mp3')
    
    try:
        # Download audio using yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(temp_dir, 'audio.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': FFMPEG_PATH,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
        
        # Check file size (Whisper has 25MB limit)
        file_size = os.path.getsize(audio_file_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f'DEBUG: Audio file size: {file_size_mb:.2f} MB')
        
        if file_size_mb > 25:
            raise Exception(f'Audio file too large ({file_size_mb:.2f} MB). Whisper API limit is 25 MB.')
        
        # Transcribe using Whisper
        print('DEBUG: Sending to Whisper API for transcription...')
        with open(audio_file_path, 'rb') as audio_file:
            transcript_response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
        
        print(f'DEBUG: Whisper transcription complete. Language detected: {transcript_response.language}')
        
        # Extract segments
        segments = []
        full_text_parts = []
        
        for segment in transcript_response.segments:
            # Segment is an object, not a dict - access attributes directly
            text = segment.text.strip() if hasattr(segment, 'text') else ''
            if text:
                start_time = segment.start if hasattr(segment, 'start') else 0
                end_time = segment.end if hasattr(segment, 'end') else 0
                
                segments.append({
                    'text': text,
                    'start': start_time,
                    'duration': end_time - start_time
                })
                full_text_parts.append(text)
        
        full_text = ' '.join(full_text_parts)
        
        return {
            'full': full_text,
            'segments': segments,
            'method': 'whisper',
            'language': transcript_response.language,
            'title': info.get('title', 'Unknown Title'),
            'uploader': info.get('uploader', 'Unknown Uploader'),
            'duration': info.get('duration', 0),
            'view_count': info.get('view_count', 0)
        }
        
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            os.rmdir(temp_dir)
            print('DEBUG: Cleaned up temporary files')
        except Exception as e:
            print(f'DEBUG: Error cleaning up temp files: {e}')

def fetch_transcript_youtube_api(video_id):
    """Fetch transcript using YouTube Data API v3 with detailed debugging"""
    if not youtube_api:
        raise Exception('YouTube API key not configured')
    
    print(f'DEBUG: Using YouTube API key: {YOUTUBE_API_KEY[:10]}...')
    print(f'DEBUG: Attempting to fetch captions for video ID: {video_id}')
    
    try:
        # Get caption tracks for the video
        print('DEBUG: Calling captions().list()...')
        captions_response = youtube_api.captions().list(
            part='snippet',
            videoId=video_id
        ).execute()
        
        print(f'DEBUG: Captions response: {captions_response}')
        
        if not captions_response.get('items'):
            raise Exception('No captions available')
        
        # Find English caption track (prefer manual, then auto-generated)
        caption_id = None
        for item in captions_response['items']:
            lang = item['snippet']['language']
            track_kind = item['snippet'].get('trackKind', 'standard')
            
            print(f'DEBUG: Found caption - Language: {lang}, Kind: {track_kind}, ID: {item["id"]}')
            
            if lang == 'en':
                if track_kind == 'standard':
                    caption_id = item['id']
                    break
                elif not caption_id:  # Use auto-generated as fallback
                    caption_id = item['id']
        
        if not caption_id and captions_response['items']:
            # Use first available caption
            caption_id = captions_response['items'][0]['id']
        
        if not caption_id:
            raise Exception('No suitable captions found')
        
        print(f'DEBUG: Selected caption ID: {caption_id}')
        print('DEBUG: Calling captions().download()...')
        
        # Download the caption
        caption = youtube_api.captions().download(
            id=caption_id,
            tfmt='srt'  # SubRip format
        ).execute()
        
        print(f'DEBUG: Downloaded caption length: {len(caption)} bytes')
        
        # Parse SRT format to extract text
        segments = []
        full_text_parts = []
        
        # Simple SRT parser
        blocks = caption.decode('utf-8').strip().split('\n\n')
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                # lines[0] = sequence number
                # lines[1] = timestamp
                # lines[2:] = text
                text = ' '.join(lines[2:])
                full_text_parts.append(text)
                
                # Parse timestamp
                timestamp = lines[1].split(' --> ')[0]
                h, m, s = timestamp.replace(',', '.').split(':')
                start_time = float(h) * 3600 + float(m) * 60 + float(s)
                
                segments.append({
                    'text': text,
                    'start': start_time,
                    'duration': 0  # SRT doesn't directly provide duration
                })
        
        full_text = ' '.join(full_text_parts)
        
        return {
            'full': full_text,
            'segments': segments,
            'method': 'youtube_api'
        }
        
    except HttpError as e:
        print(f'DEBUG: HttpError occurred')
        print(f'DEBUG: Status code: {e.resp.status}')
        print(f'DEBUG: Error details: {e.error_details}')
        print(f'DEBUG: Response: {e.resp}')
        
        if e.resp.status == 403:
            # Check if it's actually a login issue or quota
            error_reason = e.error_details[0].get('reason', 'unknown') if e.error_details else 'unknown'
            print(f'DEBUG: Error reason: {error_reason}')
            
            if error_reason == 'required':
                raise Exception(f'YouTube API authentication error: {e.error_details}. This usually means the API requires OAuth instead of just API key for captions access.')
            else:
                raise Exception('YouTube API quota exceeded or access forbidden')
        elif e.resp.status == 404:
            raise Exception('Video not found or captions not available')
        else:
            raise Exception(f'YouTube API error: {e.error_details}')

def fetch_transcript_ytdlp(video_id):
    """Fetch transcript using yt-dlp"""
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
        
        # Get subtitles
        subtitles = info.get('subtitles', {})
        automatic_captions = info.get('automatic_captions', {})
        
        # Try to get manual subtitles first, then automatic
        transcript_data = None
        if 'en' in subtitles:
            transcript_data = subtitles['en']
        elif 'en' in automatic_captions:
            transcript_data = automatic_captions['en']
        else:
            # Try any available language
            if subtitles:
                lang = list(subtitles.keys())[0]
                transcript_data = subtitles[lang]
            elif automatic_captions:
                lang = list(automatic_captions.keys())[0]
                transcript_data = automatic_captions[lang]
        
        if not transcript_data:
            raise Exception('No subtitles available for this video')
        
        # Find the json3 format (contains text data)
        json_url = None
        for fmt in transcript_data:
            if fmt.get('ext') == 'json3':
                json_url = fmt.get('url')
                break
        
        if not json_url:
            raise Exception('Could not find subtitle data')
        
        # Fetch and parse the subtitle JSON
        import urllib.request
        import json
        
        with urllib.request.urlopen(json_url) as response:
            subtitle_json = json.loads(response.read().decode('utf-8'))
        
        # Extract text from events
        segments = []
        full_text_parts = []
        
        for event in subtitle_json.get('events', []):
            if 'segs' in event:
                text = ''.join([seg.get('utf8', '') for seg in event['segs']])
                if text.strip():
                    segments.append({
                        'text': text,
                        'start': event.get('tStartMs', 0) / 1000,
                        'duration': event.get('dDurationMs', 0) / 1000
                    })
                    full_text_parts.append(text)
        
        full_text = ' '.join(full_text_parts)
        
        return {
            'full': full_text,
            'segments': segments,
            'method': 'yt-dlp',
            'title': info.get('title', 'Unknown Title'),
            'uploader': info.get('uploader', 'Unknown Uploader'),
            'duration': info.get('duration', 0),
            'view_count': info.get('view_count', 0)
        }

@app.route('/api/transcription', methods=['POST'])
def get_transcription():
    try:
        data = request.get_json()
        youtube_url = data.get('youtubeUrl')
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400
        
        video_id = extract_video_id(youtube_url)
        
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        print(f'Fetching transcription for video: {video_id}')
        
        transcript = None
        error_messages = []
        
        # Try yt-dlp captions first (fast and free)
        try:
            print('Fetching transcript via yt-dlp captions...')
            transcript = fetch_transcript_ytdlp(video_id)
            print(f'✓ Successfully fetched via yt-dlp with {len(transcript["segments"])} segments')
        except Exception as e:
            error_messages.append(f'yt-dlp: {str(e)}')
            print(f'✗ yt-dlp failed: {str(e)}')
        
        # Fallback to Whisper API if yt-dlp failed (accurate but uses API credits)
        if not transcript and openai_client:
            try:
                print('=' * 60)
                print('ATTEMPTING OPENAI WHISPER TRANSCRIPTION')
                print('=' * 60)
                transcript = fetch_transcript_whisper(video_id)
                print(f'✓ Successfully transcribed via Whisper with {len(transcript["segments"])} segments')
            except Exception as e:
                error_messages.append(f'Whisper: {str(e)}')
                print(f'✗ Whisper failed: {str(e)}')
                print('=' * 60)
        
        if not transcript:
            return jsonify({
                'error': 'Failed to fetch transcription from all sources',
                'details': ' | '.join(error_messages)
            }), 500
        
        return jsonify({
            'success': True,
            'videoId': video_id,
            'transcript': transcript,
            'method': transcript.get('method', 'unknown')
        })
        
    except Exception as e:
        print(f'Unexpected error: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to fetch transcription',
            'details': str(e)
        }), 500

@app.route('/api/extract-facts', methods=['POST'])
def extract_facts():
    """Extract verifiable facts from transcript using GPT"""
    try:
        if not openai_client:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        data = request.get_json()
        transcript_text = data.get('transcript')
        
        if not transcript_text:
            return jsonify({'error': 'Transcript text is required'}), 400
        
        print(f'Extracting facts from transcript ({len(transcript_text)} characters)...')
        
        # Create the prompt for GPT
        system_prompt = """You are a fact-checking assistant. Your task is to analyze transcripts and extract verifiable factual claims.

For each claim, identify:
1. The specific factual statement
2. The category (statistics, historical event, scientific claim, quote, etc.)
3. Why it needs verification
4. Key entities or topics to search for verification

Focus on:
- Specific numbers, dates, statistics
- Historical events or facts
- Scientific or medical claims
- Quotes attributed to people
- Assertions about companies, products, or events

Ignore:
- Opinions or subjective statements
- Hypotheticals or future predictions
- General statements without specific claims

Return your response as a JSON array of fact objects."""

        user_prompt = f"""Analyze this transcript and extract all verifiable factual claims:

"{transcript_text}"

Return a JSON array where each fact has:
- "claim": the exact factual statement
- "category": type of claim (statistic/historical/scientific/quote/general)
- "context": surrounding context from transcript
- "entities": key terms to search for verification
- "verifiable": boolean if this can be fact-checked"""

        # Call GPT API
        response = openai_client.chat.completions.create(
            model="gpt-5-mini",  
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        import json
        result = json.loads(response.choices[0].message.content)
        
        # Ensure we have a facts array
        facts = result.get('facts', []) if isinstance(result.get('facts'), list) else []
        
        print(f'✓ Extracted {len(facts)} facts from transcript')
        
        return jsonify({
            'success': True,
            'factCount': len(facts),
            'facts': facts,
            'usage': {
                'promptTokens': response.usage.prompt_tokens,
                'completionTokens': response.usage.completion_tokens,
                'totalTokens': response.usage.total_tokens
            }
        })
        
    except Exception as e:
        print(f'Error extracting facts: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to extract facts',
            'details': str(e)
        }), 500

@app.route('/api/extract-facts-chunk', methods=['POST'])
def extract_facts_chunk():
    """Extract facts from a chunk of transcript"""
    try:
        if not openai_client:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        data = request.get_json()
        transcript_chunk = data.get('chunk')
        chunk_index = data.get('chunkIndex', 0)
        total_chunks = data.get('totalChunks', 1)
        
        if not transcript_chunk:
            return jsonify({'error': 'Transcript chunk is required'}), 400
        
        print(f'Processing chunk {chunk_index + 1}/{total_chunks} ({len(transcript_chunk)} characters)...')
        
        system_prompt = """You are a fact-checking assistant. Extract verifiable factual claims from this transcript segment.

For each claim, identify:
1. The specific factual statement
2. The category (statistics, historical event, scientific claim, quote, etc.)
3. Key entities or topics to search for verification

Focus on:
- Specific numbers, dates, statistics
- Historical events or facts
- Scientific or medical claims
- Quotes attributed to people
- Assertions about companies, products, or events

Ignore opinions, hypotheticals, and general statements.
Return a JSON object with a "facts" array."""

        user_prompt = f"""Extract all verifiable factual claims from this transcript segment:

"{transcript_chunk}"

Return JSON with a "facts" array where each fact has:
- "claim": the exact factual statement
- "category": type (statistic/historical/scientific/quote/general)
- "context": surrounding context (max 100 chars)
- "entities": key terms array (max 5 items)
- "verifiable": boolean"""

        response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        facts = result.get('facts', []) if isinstance(result.get('facts'), list) else []
        
        print(f'✓ Extracted {len(facts)} facts from chunk {chunk_index + 1}')
        
        return jsonify({
            'success': True,
            'chunkIndex': chunk_index,
            'factCount': len(facts),
            'facts': facts
        })
        
    except Exception as e:
        print(f'Error extracting facts from chunk: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to extract facts from chunk',
            'details': str(e)
        }), 500

@app.route('/api/verify-fact', methods=['POST'])
def verify_single_fact():
    """Verify a single fact"""
    try:
        if not openai_client or not BRAVE_API_KEY:
            return jsonify({'error': 'APIs not configured'}), 500
        
        data = request.get_json()
        fact = data.get('fact')
        fact_index = data.get('factIndex', 0)
        total_facts = data.get('totalFacts', 1)
        
        if not fact:
            return jsonify({'error': 'Fact is required'}), 400
        
        print(f'Verifying fact {fact_index + 1}/{total_facts}: {fact.get("claim", "")[:50]}...')
        
        # Build search query
        claim = fact.get('claim', '').strip()
        if not claim:
            raise Exception('Empty claim')
        
        entities = fact.get('entities', [])
        entity_text = ' '.join(str(e) for e in entities[:2] if e) if entities else ''
        search_query = f"{claim} {entity_text}".strip()
        
        if len(search_query) > 300:
            search_query = search_query[:300].rsplit(' ', 1)[0]
        
        # Search Brave
        search_results = search_brave(search_query, count=3)
        
        # Extract sources
        sources = []
        for result in search_results.get('web', {}).get('results', [])[:3]:
            description = result.get('description', '')
            if len(description) > 200:
                description = description[:200] + '...'
            
            sources.append({
                'title': result.get('title', '')[:150],
                'url': result.get('url', ''),
                'description': description
            })
        
        # GPT verification
        verification_prompt = f"""Analyze if these search results support or refute this claim.

CLAIM: {claim}

SEARCH RESULTS:
{chr(10).join([f"{i+1}. {s['title']}: {s['description']}" for i, s in enumerate(sources)])}

Return JSON with:
- verdict: "supported", "refuted", "partially_true", "unverified", or "inconclusive"
- confidence: 0-100
- reasoning: brief explanation (max 150 chars)
- relevant_sources: indices array (0-based)"""

        verification_response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are a fact-checker. Be concise."},
                {"role": "user", "content": verification_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        verification_result = json.loads(verification_response.choices[0].message.content)
        
        verified_fact = {
            **fact,
            'verification': {
                'verdict': verification_result.get('verdict', 'inconclusive'),
                'confidence': verification_result.get('confidence', 0),
                'reasoning': verification_result.get('reasoning', '')[:200],  # Limit reasoning
                'sources': [sources[i] for i in verification_result.get('relevant_sources', []) if i < len(sources)][:2]  # Max 2 sources
            }
        }
        
        print(f'✓ Verified: {verification_result.get("verdict")}')
        
        return jsonify({
            'success': True,
            'factIndex': fact_index,
            'verifiedFact': verified_fact
        })
        
    except Exception as e:
        print(f'Error verifying fact: {str(e)}')
        return jsonify({
            'success': False,
            'factIndex': fact_index,
            'error': str(e),
            'verifiedFact': {
                **fact,
                'verification': {
                    'verdict': 'error',
                    'confidence': 0,
                    'reasoning': f'Error: {str(e)[:100]}',
                    'sources': []
                }
            }
        }), 200  # Return 200 to continue processing

def search_brave(query, count=3):
    """Search using Brave Search API"""
    if not BRAVE_API_KEY:
        raise Exception('Brave API key not configured')
    
    # Clean and validate query
    query = query.strip()
    if not query:
        raise Exception('Empty search query')
    
    # Limit query length (Brave API limit is around 400 chars)
    if len(query) > 400:
        query = query[:400]
    
    url = 'https://api.search.brave.com/res/v1/web/search'
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': BRAVE_API_KEY
    }
    params = {
        'q': query,
        'count': min(count, 5),  # Reduce to max 5 results
        'text_decorations': False,  # Disable text decorations to reduce response size
        'search_lang': 'en'
    }
    
    print(f'Brave Search query: {query[:100]}...')
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f'Brave API HTTP Error: {e.response.status_code} - {e.response.text}')
        raise Exception(f'Brave Search API error: {e.response.status_code}')
    except Exception as e:
        print(f'Brave API Error: {str(e)}')
        raise

@app.route('/api/verify-facts', methods=['POST'])
def verify_facts():
    """Verify facts using Brave Search and GPT analysis"""
    try:
        if not openai_client:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
        
        if not BRAVE_API_KEY:
            return jsonify({'error': 'Brave Search API key not configured'}), 500
        
        data = request.get_json()
        facts = data.get('facts', [])
        
        if not facts:
            return jsonify({'error': 'No facts provided for verification'}), 400
        
        # Limit to first 10 facts to avoid response size issues
        max_facts = 10
        if len(facts) > max_facts:
            print(f'Limiting verification to first {max_facts} facts (received {len(facts)})')
            facts = facts[:max_facts]
        
        print(f'Verifying {len(facts)} facts...')
        
        verified_facts = []
        
        for idx, fact in enumerate(facts):
            print(f'Verifying fact {idx + 1}/{len(facts)}: {fact.get("claim", "")[:50]}...')
            
            try:
                # Build search query from claim and entities
                claim = fact.get('claim', '').strip()
                if not claim:
                    raise Exception('Empty claim')
                    
                entities = fact.get('entities', [])
                
                # Build a clean search query
                # Use claim + top 2-3 entities, limit to reasonable length
                entity_text = ' '.join(str(e) for e in entities[:2] if e) if entities else ''
                search_query = f"{claim} {entity_text}".strip()
                
                # Limit query length
                if len(search_query) > 300:
                    search_query = search_query[:300].rsplit(' ', 1)[0]  # Cut at last word
                
                # Search Brave (reduced to 3 results)
                search_results = search_brave(search_query, count=3)
                
                # Extract relevant info from search results (limit to 3)
                sources = []
                for result in search_results.get('web', {}).get('results', [])[:3]:
                    # Truncate descriptions to reduce response size
                    description = result.get('description', '')
                    if len(description) > 200:
                        description = description[:200] + '...'
                    
                    sources.append({
                        'title': result.get('title', '')[:150],  # Limit title length
                        'url': result.get('url', ''),
                        'description': description
                    })
                
                # Use GPT to analyze if search results support or refute the claim
                verification_prompt = f"""You are a fact-checker. Analyze if the following search results support or refute this claim.

CLAIM: {claim}

SEARCH RESULTS:
{chr(10).join([f"{i+1}. {s['title']}: {s['description']}" for i, s in enumerate(sources)])}

Analyze the search results and determine:
1. verdict: "supported", "refuted", "partially_true", "unverified", or "inconclusive"
2. confidence: 0-100 (how confident are you in this verdict)
3. reasoning: brief explanation of your analysis
4. relevant_sources: indices of most relevant search results (0-based array)

Return as JSON with these exact fields."""

                verification_response = openai_client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[
                        {"role": "system", "content": "You are a fact-checking expert who analyzes search results objectively."},
                        {"role": "user", "content": verification_prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                
                import json
                verification_result = json.loads(verification_response.choices[0].message.content)
                
                # Combine fact with verification result
                verified_fact = {
                    **fact,
                    'verification': {
                        'verdict': verification_result.get('verdict', 'inconclusive'),
                        'confidence': verification_result.get('confidence', 0),
                        'reasoning': verification_result.get('reasoning', ''),
                        'sources': [sources[i] for i in verification_result.get('relevant_sources', []) if i < len(sources)]
                    },
                    'searchQuery': search_query
                }
                
                verified_facts.append(verified_fact)
                print(f'✓ Verified: {verification_result.get("verdict")} ({verification_result.get("confidence")}% confidence)')
                
            except Exception as e:
                print(f'✗ Error verifying fact: {str(e)}')
                verified_facts.append({
                    **fact,
                    'verification': {
                        'verdict': 'error',
                        'confidence': 0,
                        'reasoning': f'Error during verification: {str(e)}',
                        'sources': []
                    }
                })
        
        # Calculate overall score
        total_facts = len(verified_facts)
        supported = sum(1 for f in verified_facts if f.get('verification', {}).get('verdict') == 'supported')
        refuted = sum(1 for f in verified_facts if f.get('verification', {}).get('verdict') == 'refuted')
        partially_true = sum(1 for f in verified_facts if f.get('verification', {}).get('verdict') == 'partially_true')
        
        # Score calculation (supported: 100%, partially: 50%, refuted: 0%)
        score = ((supported * 100) + (partially_true * 50)) / total_facts if total_facts > 0 else 0
        
        print(f'✓ Verification complete. Score: {score:.1f}/100')
        
        return jsonify({
            'success': True,
            'verifiedFacts': verified_facts,
            'summary': {
                'totalFacts': total_facts,
                'supported': supported,
                'refuted': refuted,
                'partiallyTrue': partially_true,
                'score': round(score, 1)
            }
        })
        
    except Exception as e:
        print(f'Error verifying facts: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to verify facts',
            'details': str(e)
        }), 500

@app.route('/api/analyze', methods=['POST'])
@verify_token
def analyze_video():
    """Fast video analysis: transcript → extract facts → sample & verify → grade"""
    try:
        import random
        
        # Get authenticated user info
        user_uid = request.user['uid']
        user_email = request.user.get('email', 'anonymous')
        print(f'Authenticated user: {user_email} ({user_uid})')
        
        data = request.get_json()
        youtube_url = data.get('youtubeUrl')
        check_mode = data.get('checkMode', 'sample')  # 'sample' or 'full'
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400
        
        # Step 1: Get video ID
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        print(f'\n{"="*60}')
        print(f'ANALYZING VIDEO: {video_id} (Mode: {check_mode})')
        print(f'{"="*60}')
        
        # Step 2: Get transcript (2-tier system: yt-dlp → Whisper)
        print('\n[1/5] Fetching transcript...')
        transcript = None
        transcript_method = None
        
        # METHOD 1: Try yt-dlp
        try:
            transcript = fetch_transcript_ytdlp(video_id)
            transcript_method = 'yt-dlp'
            print(f'✓ Transcript fetched via yt-dlp ({len(transcript["full"])} chars)')
        except Exception as e:
            print(f'✗ yt-dlp failed: {str(e)}')
        
        # METHOD 2: Fall back to Whisper if yt-dlp failed
        if not transcript and openai_client:
            try:
                transcript = fetch_transcript_whisper(video_id)
                transcript_method = 'OpenAI Whisper'
                print(f'✓ Transcript fetched via Whisper ({len(transcript["full"])} chars)')
            except Exception as e:
                print(f'✗ Whisper failed: {str(e)}')
                return jsonify({'error': f'All transcription methods failed. Last error: {str(e)}'}), 500
        
        if not transcript:
            return jsonify({'error': 'Could not fetch transcript from any source'}), 500
        
        # Normalize transcript format (use 'full' key for consistency)
        transcript_text = transcript.get('full', '')
        
        # Step 3: Extract ALL facts at once (no chunking)
        print(f'\n[2/5] Extracting facts from transcript... (Method: {transcript_method})')
        
        system_prompt = """Extract verifiable factual claims from this transcript. Focus on:
- Specific numbers, statistics, dates
- Historical events or facts
- Scientific or medical claims
- Quotes attributed to people
- Assertions about companies, products, or events

Return ONLY facts that can be verified through web search. Ignore opinions and predictions."""

        user_prompt = f"Extract all verifiable facts from this transcript:\n\n{transcript_text}"
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "facts_extraction",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "facts": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "claim": {"type": "string"},
                                        "category": {"type": "string"},
                                        "entities": {"type": "array", "items": {"type": "string"}}
                                    },
                                    "required": ["claim", "category", "entities"]
                                }
                            }
                        },
                        "required": ["facts"]
                    }
                }
            }
        )
        
        import json
        all_facts = json.loads(response.choices[0].message.content).get('facts', [])
        print(f'✓ Extracted {len(all_facts)} total facts')
        
        # Step 3.5: Extract and verify central thesis
        print('\n[3/5] Extracting central thesis...')
        
        thesis_prompt = """Analyze this video transcript and identify THE ONE central claim or main thesis.
This should be the primary argument or key message the video is trying to convey.
Return only the single most important claim that represents the video's core message."""

        thesis_response = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": thesis_prompt},
                {"role": "user", "content": f"Transcript:\n\n{transcript_text[:8000]}"}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "thesis_extraction",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "thesis": {"type": "string"},
                            "importance": {"type": "string"}
                        },
                        "required": ["thesis", "importance"]
                    }
                }
            }
        )
        
        thesis_data = json.loads(thesis_response.choices[0].message.content)
        central_thesis = thesis_data.get('thesis', '')
        print(f'✓ Central thesis: {central_thesis[:100]}...')
        
        # Verify the central thesis
        print('  Verifying central thesis...')
        thesis_search_query = f'{central_thesis[:200]}'
        thesis_search_results = search_brave(thesis_search_query, count=5)
        thesis_web_results = thesis_search_results.get('web', {}).get('results', [])[:3]
        thesis_sources = [{'title': r.get('title', '')[:150], 'url': r.get('url', '')} for r in thesis_web_results]
        
        thesis_analysis_prompt = f"""Claim: "{central_thesis}"

Search Results:
{chr(10).join([f"- {s['title']}" for s in thesis_sources])}

Verdict (supported/refuted/partially_true):"""

        thesis_analysis = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": thesis_analysis_prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "verification",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "verdict": {"type": "string", "enum": ["supported", "refuted", "partially_true"]},
                            "reasoning": {"type": "string"}
                        },
                        "required": ["verdict", "reasoning"]
                    }
                }
            }
        )
        
        thesis_result = json.loads(thesis_analysis.choices[0].message.content)
        thesis_verdict = thesis_result['verdict']
        print(f'  ✓ Thesis verdict: {thesis_verdict}')
        
        # Store thesis verification
        thesis_verification = {
            'claim': central_thesis,
            'category': 'Central Thesis',
            'entities': [],
            'verification': {
                'verdict': thesis_verdict,
                'reasoning': thesis_result['reasoning'][:200],
                'sources': thesis_sources
            }
        }
        
        # Step 4: Smart sampling - select facts based on mode
        if check_mode == 'full':
            # Full check - verify ALL facts
            sampled_facts = all_facts
            print(f'\n[4/5] Full check mode - verifying ALL {len(sampled_facts)} facts...')
        else:
            # Sample check - select 5-7 representative facts
            sample_size = min(7, len(all_facts))
            sampled_facts = random.sample(all_facts, sample_size) if len(all_facts) > sample_size else all_facts
            print(f'\n[4/5] Sample check mode - verifying {len(sampled_facts)} facts...')
        
        if len(all_facts) == 0:
            return jsonify({
                'success': True,
                'grade': 'N/A',
                'gradeDescription': 'No verifiable facts found',
                'gradeColor': 'gray',
                'totalFacts': 0,
                'sampledFacts': 0,
                'verifiedFacts': [],
                'checkMode': check_mode
            })
        
        # Step 5: Verify sampled facts
        print('\n[5/5] Verifying sampled facts...')
        verified_facts = []
        
        for i, fact in enumerate(sampled_facts, 1):
            try:
                print(f'  Verifying fact {i}/{len(sampled_facts)}: {fact["claim"][:60]}...')
                
                # Search with Brave
                search_query = f'{fact["claim"][:200]} {" ".join(fact["entities"][:3])}'
                search_results = search_brave(search_query, count=3)
                
                web_results = search_results.get('web', {}).get('results', [])[:2]
                sources = [{'title': r.get('title', '')[:150], 'url': r.get('url', '')} for r in web_results]
                
                # Analyze with GPT
                analysis_prompt = f"""Claim: "{fact['claim']}"

Search Results:
{chr(10).join([f"- {s['title']}" for s in sources])}

Verdict (supported/refuted/partially_true):"""
                
                analysis = openai_client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[{"role": "user", "content": analysis_prompt}],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "verification",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "verdict": {"type": "string", "enum": ["supported", "refuted", "partially_true"]},
                                    "reasoning": {"type": "string"}
                                },
                                "required": ["verdict", "reasoning"]
                            }
                        }
                    }
                )
                
                result = json.loads(analysis.choices[0].message.content)
                
                verified_facts.append({
                    **fact,
                    'verification': {
                        'verdict': result['verdict'],
                        'reasoning': result['reasoning'][:200],
                        'sources': sources
                    }
                })
                
                print(f'    ✓ {result["verdict"]}')
                
            except Exception as e:
                print(f'    ✗ Error: {str(e)}')
                verified_facts.append({
                    **fact,
                    'verification': {
                        'verdict': 'error',
                        'reasoning': f'Verification failed: {str(e)}',
                        'sources': []
                    }
                })
        
        # Step 6: Calculate grade with thesis weight
        supported = sum(1 for f in verified_facts if f['verification']['verdict'] == 'supported')
        refuted = sum(1 for f in verified_facts if f['verification']['verdict'] == 'refuted')
        partially_true = sum(1 for f in verified_facts if f['verification']['verdict'] == 'partially_true')
        
        # Calculate base score: supported=100%, partially=50%, refuted=0%
        base_score = ((supported * 100) + (partially_true * 50)) / len(verified_facts) if verified_facts else 0
        
        # Apply thesis multiplier - if central thesis fails, significantly reduce score
        if thesis_verdict == 'refuted':
            # Central thesis refuted = automatic fail (max 40% score)
            final_score = min(base_score * 0.4, 40)
            print(f'⚠️  Central thesis REFUTED - score reduced from {base_score:.1f}% to {final_score:.1f}%')
        elif thesis_verdict == 'partially_true':
            # Central thesis partially true = reduced score (75% of base)
            final_score = base_score * 0.75
            print(f'⚠️  Central thesis PARTIALLY TRUE - score reduced from {base_score:.1f}% to {final_score:.1f}%')
        else:
            # Central thesis supported = full score
            final_score = base_score
            print(f'✓ Central thesis SUPPORTED - full score: {final_score:.1f}%')
        
        # Assign grade based on final score
        score = final_score
        if score >= 80:
            grade = 'A'
            description = 'High Truth - Most claims are well-supported'
            color = 'green'
        elif score >= 60:
            grade = 'B'
            description = 'Needs Verification - Some claims need fact-checking'
            color = 'blue'
        elif score >= 40:
            grade = 'C'
            description = 'Read Other Sources - Many unverified claims'
            color = 'orange'
        else:
            grade = 'D'
            description = "Don't Believe - Most claims are questionable"
            color = 'red'
        
        print(f'\n{"="*60}')
        print(f'GRADE: {grade} ({score:.1f}%) - {description}')
        print(f'{"="*60}\n')
        
        # Increment user's usage count
        increment_usage(user_uid)
        
        return jsonify({
            'success': True,
            'videoId': video_id,
            'videoTitle': transcript.get('title', 'Unknown Title'),
            'videoUploader': transcript.get('uploader', 'Unknown Uploader'),
            'videoDuration': transcript.get('duration', 0),
            'videoViewCount': transcript.get('view_count', 0),
            'transcriptMethod': transcript_method,  # NEW: Show which method was used
            'grade': grade,
            'gradeDescription': description,
            'gradeColor': color,
            'score': round(score, 1),
            'totalFacts': len(all_facts),
            'sampledFacts': len(sampled_facts),
            'verifiedFacts': verified_facts,
            'centralThesis': thesis_verification,
            'checkMode': check_mode,
            'summary': {
                'supported': supported,
                'refuted': refuted,
                'partiallyTrue': partially_true
            }
        })
        
    except Exception as e:
        print(f'\n✗ Analysis failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to analyze video',
            'details': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Truth Quest Python API is running'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3001))
    print(f'🚀 Flask server running on http://localhost:{port}')
    app.run(debug=True, port=port, host='0.0.0.0')

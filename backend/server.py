from flask import Flask, request, jsonify
from flask_cors import CORS
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI
import yt_dlp
import re
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# YouTube API configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube_api = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY) if YOUTUBE_API_KEY else None

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

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

def fetch_transcript_youtube_api(video_id):
    """Fetch transcript using YouTube Data API v3"""
    if not youtube_api:
        raise Exception('YouTube API key not configured')
    
    try:
        # Get caption tracks for the video
        captions_response = youtube_api.captions().list(
            part='snippet',
            videoId=video_id
        ).execute()
        
        if not captions_response.get('items'):
            raise Exception('No captions available')
        
        # Find English caption track (prefer manual, then auto-generated)
        caption_id = None
        for item in captions_response['items']:
            lang = item['snippet']['language']
            track_kind = item['snippet'].get('trackKind', 'standard')
            
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
        
        # Download the caption
        caption = youtube_api.captions().download(
            id=caption_id,
            tfmt='srt'  # SubRip format
        ).execute()
        
        # Parse SRT format to extract text
        import io
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
        if e.resp.status == 403:
            raise Exception('YouTube API quota exceeded or access forbidden')
        elif e.resp.status == 404:
            raise Exception('Video not found or captions not available')
        else:
            raise Exception(f'YouTube API error: {e.error_details}')

def fetch_transcript_ytdlp(video_id):
    """Fetch transcript using yt-dlp (fallback method)"""
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
            'method': 'yt-dlp'
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
        
        # Try YouTube API first (if configured)
        if youtube_api:
            try:
                print('Attempting to fetch via YouTube Data API v3...')
                transcript = fetch_transcript_youtube_api(video_id)
                print(f'✓ Successfully fetched via YouTube API with {len(transcript["segments"])} segments')
            except Exception as e:
                error_messages.append(f'YouTube API: {str(e)}')
                print(f'✗ YouTube API failed: {str(e)}')
        
        # Fallback to yt-dlp if YouTube API failed or not configured
        if not transcript:
            try:
                print('Attempting to fetch via yt-dlp...')
                transcript = fetch_transcript_ytdlp(video_id)
                print(f'✓ Successfully fetched via yt-dlp with {len(transcript["segments"])} segments')
            except Exception as e:
                error_messages.append(f'yt-dlp: {str(e)}')
                print(f'✗ yt-dlp failed: {str(e)}')
        
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
            model="gpt-4o",  # or "gpt-4-turbo" or "gpt-3.5-turbo" for testing
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
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

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Truth Quest Python API is running'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3001))
    print(f'🚀 Flask server running on http://localhost:{port}')
    app.run(debug=True, port=port, host='0.0.0.0')

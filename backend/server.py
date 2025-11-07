from flask import Flask, request, jsonify
from flask_cors import CORS
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI
import yt_dlp
import requests
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

# Brave Search API configuration
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')

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

def search_brave(query, count=5):
    """Search using Brave Search API"""
    if not BRAVE_API_KEY:
        raise Exception('Brave API key not configured')
    
    url = 'https://api.search.brave.com/res/v1/web/search'
    headers = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'X-Subscription-Token': BRAVE_API_KEY
    }
    params = {
        'q': query,
        'count': count
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    return response.json()

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
        
        print(f'Verifying {len(facts)} facts...')
        
        verified_facts = []
        
        for idx, fact in enumerate(facts):
            print(f'Verifying fact {idx + 1}/{len(facts)}: {fact.get("claim", "")[:50]}...')
            
            try:
                # Build search query from claim and entities
                claim = fact.get('claim', '')
                entities = fact.get('entities', [])
                search_query = f"{claim} {' '.join(entities[:3])}"  # Use claim + top 3 entities
                
                # Search Brave
                search_results = search_brave(search_query, count=5)
                
                # Extract relevant info from search results
                sources = []
                for result in search_results.get('web', {}).get('results', [])[:5]:
                    sources.append({
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'description': result.get('description', '')
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
                    model="gpt-4o-mini",
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

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Truth Quest Python API is running'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3001))
    print(f'🚀 Flask server running on http://localhost:{port}')
    app.run(debug=True, port=port, host='0.0.0.0')

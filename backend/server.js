import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { YoutubeTranscript } from 'youtube-transcript';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Helper function to extract video ID from YouTube URL
function extractVideoId(url) {
  const regex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
  const match = url.match(regex);
  return match ? match[1] : null;
}

// Route to get YouTube transcription
app.post('/api/transcription', async (req, res) => {
  try {
    const { youtubeUrl } = req.body;

    if (!youtubeUrl) {
      return res.status(400).json({ 
        error: 'YouTube URL is required' 
      });
    }

    const videoId = extractVideoId(youtubeUrl);
    
    if (!videoId) {
      return res.status(400).json({ 
        error: 'Invalid YouTube URL' 
      });
    }

    console.log(`Fetching transcription for video: ${videoId}`);

    // Fetch the transcript
    const transcript = await YoutubeTranscript.fetchTranscript(videoId);

    // Combine all transcript parts into full text
    const fullText = transcript.map(item => item.text).join(' ');

    res.json({
      success: true,
      videoId,
      transcript: {
        full: fullText,
        segments: transcript
      }
    });

  } catch (error) {
    console.error('Error fetching transcription:', error);
    
    if (error.message.includes('Transcript is disabled')) {
      return res.status(404).json({ 
        error: 'Transcription is not available for this video' 
      });
    }
    
    res.status(500).json({ 
      error: 'Failed to fetch transcription',
      details: error.message 
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Truth Quest API is running' });
});

app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
});

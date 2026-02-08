from flask import Flask, request, jsonify, render_template
import PyPDF2
from youtube_transcript_api import YouTubeTranscriptApi
import re

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

def smart_summary(text):
    """Create REAL bullet point summary from extracted text"""
    if len(text) < 50:
        return "• No readable text found\n• Try a different PDF/video\n• Use text-based documents"
    
    # Extract sentences and key points
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:8]
    
    summary = "✅ **MAIN POINTS EXTRACTED:**\n\n"
    for i, sentence in enumerate(sentences, 1):
        summary += f"• {sentence[:100]}...\n"
    
    return summary

def extract_text_from_pdf(pdf_file):
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages[:5]:
            text += page.extract_text() or ""
        print(f"📄 Extracted {len(text)} chars from PDF")
        return text.strip()
    except:
        return ""

def get_youtube_transcript(video_id):
    try: 
        # Try English first
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        text = " ".join([t["text"] for t in transcript[:100]])
        return text
    except:
        try:
            # Try ANY available language
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_generated_transcript(['en'])
            text = " ".join([t["text"] for t in transcript.fetch()[:100]])
            return text
        except:
            return "No transcript available - video subtitles disabled"


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/summarize-pdf", methods=["POST"])
def summarize_pdf():
    try:
        file = request.files["file"]
        text = extract_text_from_pdf(file)
        
        if not text:
            return jsonify({"error": "No text found in PDF (try text-based PDF)"})
        
        summary = smart_summary(text)
        return jsonify({
            "summary": f"📄 **{file.filename}**\n\n{text[:300]}...\n\n{summary}"
        })
    except:
        return jsonify({"error": "PDF processing error"})

@app.route("/summarize-youtube", methods=["POST"])
def summarize_youtube():
    try:
        print("🎥 YouTube request received")
        data = request.get_json()
        url = data["url"].strip()
        print(f"Processing URL: {url}")
        
        # BETTER YouTube ID extraction (works with ALL formats)
        video_id = ""
        if "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        elif "embed/" in url:
            video_id = url.split("embed/")[1].split("?")[0]
        elif "youtube.com/shorts/" in url:
            video_id = url.split("shorts/")[1].split("?")[0]
        
        print(f"Extracted video ID: {video_id}")
        
        if len(video_id) != 11 or not video_id.replace('-', '').replace('_', '').isalnum():
            return jsonify({"error": f"Invalid YouTube URL. Video ID should be 11 chars: {video_id}"})
        
        text = get_youtube_transcript(video_id)
        
        if not text:
            return jsonify({"error": "No transcript available for this video (private/unlisted?)"})
        
        summary = smart_summary(text)
        return jsonify({
            "summary": f"🎥 **YouTube Video**\nVideo ID: {video_id}\n\nPreview: {text[:200]}...\n\n{summary}"
        })
    except Exception as e:
        print(f"❌ YouTube error: {e}")
        return jsonify({"error": f"Error processing video: {str(e)}"})

if __name__ == "__main__":
    print("🚀 AI Summarizer (Real Content) - http://localhost:5001")
    app.run(debug=True, port=5001)
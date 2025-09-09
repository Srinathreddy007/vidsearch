# Video Search - Backend
## Steps to Run
- download `ffmpeg` using the command `brew install ffmpeg` globally
- run `requirements.txt` file using the command `pip3 install -r requirements.txt`
- Run both client and server side applications and open url `http://localhost:5173/` in the browser to see the complete working application
  
## Approach
I have built a Django REST Framework API as the backend for Video Search.
The system is designed to be API-first, so any frontend (React, mobile, etc.) can consume it. The backend handles three main responsibilities:

### 1. Video Upload & Validation

  - Videos are uploaded via POST /api/videos/.

  - I stream the file to a temporary location and use ffprobe (FFmpeg) to measure its duration.

  - Only videos ≤ 180 seconds are accepted and otherwise a validation error is returned.

  - Once validated, the file is saved in media/videos/ and metadata (title, duration_seconds, uploaded_at) is stored in the video model.
### 2. Transcription & Segmentation
  - On request,  /api/videos/{id}/transcribe/  the POST api call  extracts audio and runs  faster-whisper  for speech-to-text.

  - We collect word-level timestamps and group them into approximately 5 second  segments.

  - Each segment is saved in the database with start, end, text, and an embedding vector generated using sentence-transformers.

  - This makes each video searchable at the segment level.
### 3. Natural Language Search
  - GET /api/videos/{id}/search?q=...&include_frame=1 embeds the user’s query and runs cosine similarity against stored segment embeddings.

  - The API returns the best matching segment(s) with text, start/end timestamps, and similarity scores.

  - Optionally, we extract a thumbnail frame at the match timestamp using FFmpeg, returning a frame_url in the response.
    
##  Architectural Decisions

- **Django + DRF**  --> Chosen for rapid prototyping, easy API design, and built-in ORM.  
- **ffprobe validation** --> Avoids storing long or invalid videos before processing.  
- **Chunked segments (approx 5s)** --> Provides a balance between precision (fine grained timestamps) and context (enough text for embeddings to capture meaning).  
- **Embeddings in JSONField** --> Simple to store in SQLite without extra dependencies.  
- **Whisper (small model used)** --> Balances speed and accuracy and easy to swap out for larger models if quality matters more than latency.  
- **Cosine similarity using NumPy** --> Simple in-memory search works for small datasets. For larger deployments, a vector database would be required.  
- **Frame extraction using FFmpeg** --> Provides a visual cue to improve UX.

## Trade-offs

- **Accuracy vs Speed** --> I used Whisper *small* is fast enough for short clips but not as accurate as *medium* or *large*. We chose it for performance in a take-home assignment.  
- **Storage Simplicity vs Scale** --> JSONField embeddings in SQLite are easy to implement, but not scalable. A vector DB would be better in real-world use.  
- **Synchronous Processing** --> Transcription currently blocks the request. For production, we can use WebSockets or polling to make Trascriptions run asynchronously.  
- **Security** --> We allow unauthenticated requests (`AllowAny`) for simplicity. In production, we would add JWT authentication, file size limits, and virus scanning.

## Demo Pictures
<img width="1151" height="515" alt="Pasted Graphic 1" src="https://github.com/user-attachments/assets/50757e5a-3160-4d99-ab86-cf6cef8f765c" />
<img width="1252" height="684" alt="Pasted Graphic 2" src="https://github.com/user-attachments/assets/b989e907-cb02-4266-b784-83eecf59962b" />
<img width="1234" height="753" alt="Pasted Graphic 3" src="https://github.com/user-attachments/assets/07c14034-ce09-47ca-90dc-7e7b92169a1c" />












  
  

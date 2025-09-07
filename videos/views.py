import json
import numpy as np
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Video, Transcript, TranscriptSegment
from .serializers import VideoSerializer  # from Step 1
from .serializers import TranscriptSerializer, SearchResultSerializer
from .nlp import transcribe_to_word_segments, rechunk_words, embed_texts, cosine_sim

class VideoViewSet(viewsets.ModelViewSet):
    """
    POST /api/videos/            create (multipart: title, file)
    GET  /api/videos/            list
    GET  /api/videos/{id}/       retrieve
    PUT  /api/videos/{id}/       update()   Replace a video record
    PATCH /api/videos/{id}/      partial_update()   Update part of a record
    DELETE /api/videos/{id}/     destroy()  Delete a video
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @action(detail=True, methods=["POST"], url_path="transcribe")
    def transcribe(self, request, pk=None):
        """
        Transcribe the video, chunk into ~5s segments, store embeddings.
        POST /api/videos/{id}/transcribe/
        """
        video = self.get_object()

        # idempotency: if transcript exists, return it
        transcript, created = Transcript.objects.get_or_create(video=video, defaults={"language": "en"})
        if not created and transcript.segments.exists():
            ser = TranscriptSerializer(transcript)
            return Response({"message": "already_transcribed", "transcript": ser.data})

        # Build segments
        words= transcribe_to_word_segments(video.file.path, language="en")
        print("words-->", words)
        chunks = rechunk_words(words, target_window_s=5.0, max_window_s=8.0)
        # print("chunks-->", chunks)
        if not chunks:
            return Response({"detail": "No speech detected."}, status=400)

        # Embed and persist
        texts = [c["text"] for c in chunks]
        embs = embed_texts(texts)
        seg_objs = []
        for c, e in zip(chunks, embs):
            seg_objs.append(TranscriptSegment(
                Transcript=transcript,
                start=c["start"],
                end=c["end"],
                text=c["text"],
                embedding=e,
            ))
        TranscriptSegment.objects.bulk_create(seg_objs)

        ser = TranscriptSerializer(transcript)
        return Response({"message": "transcribed", "transcript": ser.data}, status=201)

    @action(detail=True, methods=["GET"], url_path="search")
    def search(self, request, pk=None):
        """
        GET /api/videos/{id}/search/?q=When%20does%20...
        Returns best segment(s) with timestamp & confidence.
        """
        q = request.query_params.get("q ", "").strip()
        if not q:
            return Response({"detail": "Missing query param 'q'."}, status=400)

        top_k = max(1, min(int(request.query_params.get("top_k", 1)), 10))
        video = self.get_object()
        transcript = getattr(video, "transcript", None)
        if transcript is None or not transcript.segments.exists():
            return Response({"detail": "No transcript. Call /transcribe first."}, status=400)

        # Fetch embeddings into matrix
        segs = list(transcript.segments.all().values("id", "start", "end", "text", "embedding"))
        texts = [s["text"] for s in segs]
        E = np.asarray([np.asarray(s["embedding"], dtype=np.float32) for s in segs])
        # normalize defensively
        norms = np.linalg.norm(E, axis=1, keepdims=True) + 1e-12
        E = E / norms

        # Embed query (normalized)
        from .nlp import get_st_model
        qv = get_st_model().encode([q], normalize_embeddings=True)[0]
        qv = np.asarray(qv, dtype=np.float32)

        sims = (E @ qv)  # cosine similarity
        idx = np.argsort(-sims)[:top_k]

        results = [{
            "start": float(segs[i]["start"]),
            "end": float(segs[i]["end"]),
            "text": segs[i]["text"],
            "score": float(sims[i]),
        } for i in idx]

        return Response({"query": q, "results": results})

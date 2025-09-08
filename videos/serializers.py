import os, tempfile
from django.core.files.base import File

from rest_framework import serializers
from .models import Video
from .ffprobe import get_duration_seconds
from .models import Transcript

# 3 minute duration
MAX_VIDEO_DURATION = 180
ALLOWED_VIDEO_FORMATS = [".mp4", ".mov", ".mkv", ".webm", ".avi"]

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'
        read_only_fields = ["id", "duration_seconds", "uploaded_at"]

    def validate_file(self, f):
        name = (getattr(f, "name", "") or "").lower()
        if not name.endswith(tuple(ALLOWED_VIDEO_FORMATS)):
            raise serializers.ValidationError(
                "Unsupported file format. Use MP4/MOV/MKV/WEBM/AVI."
            )
        return f
    
    def create(self, validated_data):
        upload = validated_data.get("file")
        suffix = os.path.splitext(getattr(upload, "name", ""))[1].lower()

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in upload.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        duration = get_duration_seconds(tmp_path)

        if duration > MAX_VIDEO_DURATION:
            os.remove(tmp_path)
            raise serializers.ValidationError({"file": "Video exceeds 3 minutes."})
        if duration == 0:
            os.remove(tmp_path)
            raise serializers.ValidationError({"file": "Could not read duration (is ffprobe installed?)"})
        
        video = Video(duration_seconds=duration, **validated_data)
        with open(tmp_path, "rb") as f:
            video.file.save(getattr(upload, "name", ""), File(f), save=True)
        os.remove(tmp_path)
        return video
    
class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
            # fields = '__all__'
        fields = ["id", "video", "language", "created_at"]
        
class SearchResultSerializer(serializers.Serializer):
    start = serializers.FloatField()
    end = serializers.FloatField()
    text = serializers.CharField()
    score = serializers.FloatField()
    

    

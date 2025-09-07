from django.db import models


class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="videos/")
    duration_seconds = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title
    
class Transcript(models.Model):
    video = models.OneToOneField(Video, on_delete=models.CASCADE, related_name="transcript")
    language = models.CharField(max_length = 16, default="en")
    created_at = models.DateTimeField(auto_now_add=True)

class TranscriptSegment(models.Model):
    Transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE, related_name="segments")
    start = models.FloatField(help_text="Start time in seconds ")
    end = models.FloatField(help_text="End time in seconds")
    text = models.TextField()
    embedding = models.JSONField() 

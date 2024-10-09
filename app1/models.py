from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class BlogPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    you_tube_title = models.CharField(max_length=300)
    you_tube_link = models.URLField()
    generate = models.TextField()
    create_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.you_tube_title
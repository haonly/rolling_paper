from django.db import models

# Create your models here.


class Rolling(models.Model):
    topic = models.CharField(max_length=70)
    content = models.CharField(max_length=200)

    def __str__(self):
        return self.topic

from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    category_name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#ffdcdc')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('category_name', 'user')

    def __str__(self):
        return self.category_name

class Activity(models.Model):

    STATE_CHOICES = [
        ('planned', 'planned'),
        ('progress', 'in progress'),
        ('completed', 'completed'),
        ('canceled', 'canceled'),
    ]

    activity_name = models.CharField(max_length=100)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    state = models.CharField(
        max_length=30, 
        choices=STATE_CHOICES, 
        default='planned'
    )

    def __str__(self):
        return self.activity_name

class Emojiii(models.Model):
    image = models.ImageField(upload_to='imagini/emoji', max_length=255)
    status = models.CharField(max_length=255)

class Journall(models.Model):
    Date = models.DateField()
    Text = models.TextField()
    Emojis = models.ManyToManyField('Emojiii')
    Image = models.ImageField(upload_to='imagini/images_from_journal')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Entry on {self.Date}"

class AvatarEyes(models.Model):
    img_eyes = models.ImageField(upload_to='avatar/eyes')

class AvatarHair(models.Model):
    img_hair = models.ImageField(upload_to='avatar/hair')

class AvatarMouth(models.Model):
    img_mouth = models.ImageField(upload_to='avatar/mouth')

class Avatar(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    imagine_finala = models.ImageField(upload_to='avatar/final', null=True, blank=True)

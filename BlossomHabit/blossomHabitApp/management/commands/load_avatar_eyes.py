from django.conf import settings
from django.core.management.base import BaseCommand
from blossomHabitApp.models import AvatarEyes
import os

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        eyes_dir = os.path.join(settings.MEDIA_ROOT, 'imagini', 'avatar', 'eyes')
        for filename in os.listdir(eyes_dir):
            if filename.endswith('.png'):
                eyes = AvatarEyes.objects.create(img_eyes=os.path.join('imagini', 'avatar', 'eyes', filename))
                self.stdout.write(self.style.SUCCESS(f'Successfully loaded {filename}'))

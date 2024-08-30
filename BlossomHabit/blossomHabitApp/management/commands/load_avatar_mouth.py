from django.conf import settings
from django.core.management.base import BaseCommand
from blossomHabitApp.models import AvatarMouth
import os

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        mouth_dir = os.path.join(settings.MEDIA_ROOT, 'imagini', 'avatar', 'mouth')
        for filename in os.listdir(mouth_dir):
            if filename.endswith('.png'):
                mouth = AvatarMouth.objects.create(img_mouth=os.path.join('imagini', 'avatar', 'mouth', filename))
                self.stdout.write(self.style.SUCCESS(f'Successfully loaded {filename}'))

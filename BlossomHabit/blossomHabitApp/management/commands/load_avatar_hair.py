from django.conf import settings
from django.core.management.base import BaseCommand
from blossomHabitApp.models import AvatarHair
import os

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        hair_dir = os.path.join(settings.MEDIA_ROOT, 'imagini', 'avatar', 'hair')
        for filename in os.listdir(hair_dir):
            if filename.endswith('.png'):
                hair = AvatarHair.objects.create(img_hair=os.path.join('imagini', 'avatar', 'hair', filename))
                self.stdout.write(self.style.SUCCESS(f'Successfully loaded {filename}'))

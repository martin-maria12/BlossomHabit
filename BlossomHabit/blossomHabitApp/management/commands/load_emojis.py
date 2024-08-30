from django.conf import settings
from django.core.management.base import BaseCommand
from blossomHabitApp.models import Emojiii
import os

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        emoji_dir = os.path.join(settings.MEDIA_ROOT, 'imagini', 'emoji')
        for filename in os.listdir(emoji_dir):
            if filename.endswith('.png'):
                name, _ = os.path.splitext(filename)
                status = name
                emoji = Emojiii.objects.create(image=os.path.join('imagini', 'emoji', filename), status=status)
                self.stdout.write(self.style.SUCCESS(f'Successfully loaded {filename} with status {status}'))

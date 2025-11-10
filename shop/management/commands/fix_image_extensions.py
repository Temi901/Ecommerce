# shop/management/commands/fix_image_extensions.py

from django.core.management.base import BaseCommand
from django.db import transaction
from shop.models import Product
import cloudinary.api
import cloudinary.exceptions  # <-- Corrected import
import os

class Command(BaseCommand):
    help = 'Queries Cloudinary to find the true file extension and updates the DB if a mismatch is found.'

    def handle(self, *args, **options):
        # Configure Cloudinary (NOTE: Requires CLOUDINARY_API_KEY/SECRET to be set in environment)
        # We rely on settings.py's import and configuration being available, but ensure it's configured
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'YOUR_CLOUD_NAME'),
            api_key=os.environ.get('CLOUDINARY_API_KEY', 'YOUR_API_KEY'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'YOUR_API_SECRET'),
        )

        total_updated = 0
        
        self.stdout.write(self.style.NOTICE('Starting automatic extension fix based on Cloudinary data...'))
        
        with transaction.atomic():
            for p in Product.objects.all():
                if not p.image or not str(p.image).split('.')[-1].lower() in ('jpg', 'jpeg', 'png', 'webp', 'gif'):
                    continue
                
                image_path = str(p.image)
                
                # Extract public ID (path relative to MEDIA_ROOT, without extension)
                base_public_id = image_path.rsplit('.', 1)[0]
                db_extension = image_path.split('.')[-1].lower()

                try:
                    # Query Cloudinary API for the resource metadata
                    resource = cloudinary.api.resource(base_public_id, resource_type="image")
                    cloudinary_format = resource.get('format', '').lower()
                    
                    if cloudinary_format and cloudinary_format != db_extension:
                        new_image_path = f"{base_public_id}.{cloudinary_format}"
                        p.image = new_image_path
                        p.save()
                        total_updated += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'[UPDATED] ID {p.id}: {p.name} - Changed from .{db_extension} to .{cloudinary_format}'
                        ))

                except cloudinary.exceptions.Error:  # <-- FIX: Use cloudinary.exceptions.Error
                    # Image not found or API issue (ignore, handled by the other script)
                    pass
        
        self.stdout.write(self.style.NOTICE('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS(f'Database fix complete. Total products updated: {total_updated}'))
        self.stdout.write(self.style.NOTICE('='*50))
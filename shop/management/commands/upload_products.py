from django.core.management.base import BaseCommand
from django.core.files import File
from shop.models import Product, Category
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Upload products from local database to production with Cloudinary'

    def handle(self, *args, **kwargs):
        # Get the base directory (where manage.py is)
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        
        products = Product.objects.all()
        
        for product in products:
            if product.image:
                # Get the local image path
                local_image_path = BASE_DIR / 'media' / str(product.image)
                
                if local_image_path.exists():
                    # Re-save the image to trigger Cloudinary upload
                    with open(local_image_path, 'rb') as img_file:
                        product.image.save(
                            local_image_path.name,
                            File(img_file),
                            save=True
                        )
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Uploaded: {product.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠ Image not found: {product.name} - {local_image_path}')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ No image: {product.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Processed {products.count()} products')
        )
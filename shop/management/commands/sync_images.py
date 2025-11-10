from django.core.management.base import BaseCommand
from shop.models import Product
from django.core.files.base import ContentFile
import cloudinary
import cloudinary.uploader
from pathlib import Path
import os

class Command(BaseCommand):
    help = 'Upload product images from local media folder to Cloudinary'

    def handle(self, *args, **kwargs):
        # Configure Cloudinary - added fallback values
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'dznwck80z'),
            api_key=os.environ.get('CLOUDINARY_API_KEY', '253791256396167'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'BhGfUyC_Nr5pJfrdgFgQidQRLck'),
            secure=True
        )
        
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        media_dir = BASE_DIR / 'media'
        
        products = Product.objects.all()
        total = products.count()
        uploaded = 0
        failed = 0
        
        self.stdout.write(f'Found {total} products')
        
        for product in products:
            # Check if local image exists
            old_image_path = str(product.image) if product.image else None
            
            if old_image_path:
                local_path = media_dir / old_image_path
                
                if local_path.exists():
                    try:
                        # Upload to Cloudinary and get URL
                        result = cloudinary.uploader.upload(
                            str(local_path),
                            folder='products',  # CHANGED: simplified folder name
                            public_id=f'product_{product.id}',  # CHANGED: simplified, removed slug
                            overwrite=True,
                            resource_type='image'
                        )
                        
                        # Get the Cloudinary URL
                        cloudinary_url = result['secure_url']
                        
                        # CHANGED: Match the folder name above
                        cloudinary_path = f"products/product_{product.id}"
                        
                        # Update product image field
                        product.image = cloudinary_path
                        product.save(update_fields=['image'])
                        
                        uploaded += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'✓ {uploaded}/{total}: {product.name}\n'
                            f'   Cloudinary URL: {cloudinary_url}\n'
                            f'   Saved as: {cloudinary_path}'
                        ))
                        
                    except Exception as e:
                        failed += 1
                        self.stdout.write(self.style.ERROR(f'✗ Failed: {product.name} - {str(e)}'))
                else:
                    # No local image found, skip
                    self.stdout.write(self.style.WARNING(f'⚠ No image: {product.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ No image field: {product.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Complete! Uploaded: {uploaded}, Failed: {failed}'))
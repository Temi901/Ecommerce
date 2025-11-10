from django.core.management.base import BaseCommand
from shop.models import Product
import cloudinary
import cloudinary.uploader
from pathlib import Path
import os
import re

class Command(BaseCommand):
    help = 'Upload all images from media/products folder to Cloudinary and match to products'

    def clean_name(self, name):
        """Clean and normalize names for matching"""
        # Remove file extension
        name = name.lower().replace('.jpeg', '').replace('.jpg', '').replace('.png', '').replace('.webp', '')
        # Remove Django duplicate suffixes (like _xxx)
        name = re.sub(r'_[a-zA-Z0-9]{7,8}$', '', name)
        # Replace underscores with spaces
        name = name.replace('_', ' ')
        # Remove extra spaces
        name = ' '.join(name.split())
        return name

    def handle(self, *args, **kwargs):
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'dznwck80z'),
            api_key=os.environ.get('CLOUDINARY_API_KEY', '253791256396167'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'BhGfUyC_Nr5pJfrdgFgQidQRLck'),
            secure=True
        )
        
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        media_dir = BASE_DIR / 'media' / 'products'
        
        if not media_dir.exists():
            self.stdout.write(self.style.ERROR('❌ Media folder not found!'))
            return
        
        # Get all products
        products = {self.clean_name(p.name): p for p in Product.objects.all()}
        
        self.stdout.write(f'\nFound {len(products)} products in database\n')
        
        # Get all image files
        image_files = list(media_dir.glob('*.jpeg')) + list(media_dir.glob('*.jpg')) + list(media_dir.glob('*.png')) + list(media_dir.glob('*.webp'))
        
        self.stdout.write(f'Found {len(image_files)} image files\n')
        
        uploaded = 0
        failed = 0
        matched = 0
        
        # Process each image
        for image_path in image_files:
            clean_filename = self.clean_name(image_path.stem)
            
            # Try to find matching product
            product = None
            for product_name, prod_obj in products.items():
                if clean_filename in product_name or product_name in clean_filename:
                    product = prod_obj
                    break
            
            if not product:
                self.stdout.write(self.style.WARNING(f'⚠ No product match for: {image_path.name}'))
                continue
            
            try:
                # Upload to Cloudinary
                result = cloudinary.uploader.upload(
                    str(image_path),
                    folder='products',
                    public_id=f'product_{product.id}',
                    overwrite=True,
                    resource_type='image'
                )
                
                # Save Cloudinary path to product
                cloudinary_path = f"products/product_{product.id}"
                product.image = cloudinary_path
                product.save(update_fields=['image'])
                
                uploaded += 1
                matched += 1
                
                self.stdout.write(self.style.SUCCESS(
                    f'✓ {product.name}\n'
                    f'  File: {image_path.name}\n'
                    f'  URL: {result["secure_url"]}'
                ))
                
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(
                    f'✗ Failed: {product.name} ({image_path.name}): {str(e)}'
                ))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*60}\n'
            f'✅ Complete!\n'
            f'Matched & Uploaded: {matched}\n'
            f'Failed: {failed}\n'
            f'Unmatched images: {len(image_files) - matched - failed}\n'
            f'{"="*60}'
        ))
        
# Save as: shop/management/commands/verify_all_images.py

from django.core.management.base import BaseCommand
from django.db import transaction
from shop.models import Product
import cloudinary
import cloudinary.api
import os

class Command(BaseCommand):
    help = 'Verify all product images and report any issues'

    def handle(self, *args, **options):
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'dznwck80z'),
            api_key=os.environ.get('CLOUDINARY_API_KEY', '253791256396167'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'BhGfUyC_Nr5pJfrdgFgQidQRLck'),
            secure=True
        )
        
        products = Product.objects.all()
        
        missing = []
        incorrect = []
        correct = []
        
        self.stdout.write(f'\n{"="*70}')
        self.stdout.write(f'Verifying {products.count()} products...')
        self.stdout.write(f'{"="*70}\n')
        
        for product in products:
            try:
                if not product.image:
                    missing.append(product)
                    self.stdout.write(self.style.WARNING(
                        f'[NO IMAGE] {product.id}: {product.name}'
                    ))
                    continue
                
                current_path = str(product.image)
                
                # Try to fetch from Cloudinary to verify
                public_id = f'products/product_{product.id}'
                
                try:
                    resource = cloudinary.api.resource(public_id)
                    actual_format = resource.get('format', 'jpg')
                    expected_extension = f'.{actual_format}'
                    
                    if not current_path.endswith(expected_extension):
                        incorrect.append((product, current_path, expected_extension))
                        self.stdout.write(self.style.ERROR(
                            f'[WRONG EXT] {product.id}: {product.name}\n'
                            f'           Has: {current_path}\n'
                            f'           Should be: {public_id}{expected_extension}'
                        ))
                    else:
                        correct.append(product)
                        self.stdout.write(self.style.SUCCESS(
                            f'[OK] {product.id}: {product.name}'
                        ))
                        
                except cloudinary.exceptions.NotFound:
                    missing.append(product)
                    self.stdout.write(self.style.ERROR(
                        f'[NOT ON CLOUDINARY] {product.id}: {product.name}\n'
                        f'                     Looking for: {public_id}'
                    ))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'[ERROR] {product.id}: {product.name} - {str(e)}'
                ))
        
        # Summary
        self.stdout.write(f'\n{"="*70}')
        self.stdout.write(self.style.SUCCESS('SUMMARY:'))
        self.stdout.write(self.style.SUCCESS(f'✓ Correct: {len(correct)}'))
        self.stdout.write(self.style.ERROR(f'✗ Wrong Extension: {len(incorrect)}'))
        self.stdout.write(self.style.WARNING(f'⚠ Missing/Not on Cloudinary: {len(missing)}'))
        self.stdout.write(f'{"="*70}\n')
        
        if incorrect:
            self.stdout.write(self.style.WARNING(
                '\n💡 To fix products with wrong extensions, run:\n'
                '   python manage.py fix_image_extensions\n'
            ))
        
        if missing:
            self.stdout.write(self.style.WARNING(
                f'\n⚠ {len(missing)} products need images uploaded to Cloudinary\n'
            ))
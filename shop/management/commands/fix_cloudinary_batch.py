# Save as: shop/management/commands/fix_cloudinary_batch.py

from django.core.management.base import BaseCommand
from django.db import connection
from shop.models import Product
import cloudinary
import cloudinary.api
import os
import time

class Command(BaseCommand):
    help = 'Fix Cloudinary URLs in batches (safer for large datasets)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of products to process before committing (default: 10)'
        )

    def handle(self, *args, **options):
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'dznwck80z'),
            api_key=os.environ.get('CLOUDINARY_API_KEY', '253791256396167'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'BhGfUyC_Nr5pJfrdgFgQidQRLck'),
            secure=True
        )
        
        batch_size = options['batch_size']
        
        # Get products that need fixing
        products = Product.objects.filter(image__isnull=False).exclude(image='')
        total = products.count()
        
        fixed = 0
        skipped = 0
        failed = 0
        batch_count = 0
        
        self.stdout.write(f'\n{"="*70}')
        self.stdout.write(f'Processing {total} products in batches of {batch_size}...')
        self.stdout.write(f'{"="*70}\n')
        
        for product in products:
            batch_count += 1
            
            try:
                current_path = str(product.image)
                
                # Skip if already has full URL or proper extension
                if current_path.startswith('http') or any(current_path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                    skipped += 1
                    self.stdout.write(self.style.SUCCESS(f'[OK] {product.name}'))
                    continue
                
                # Try to fetch from Cloudinary
                try:
                    public_id = f'products/product_{product.id}'
                    resource = cloudinary.api.resource(public_id)
                    
                    # Get format and build new path
                    file_format = resource.get('format', 'jpg')
                    new_path = f'{public_id}.{file_format}'
                    secure_url = resource['secure_url']
                    
                    # Update product
                    product.image = new_path
                    product.save(update_fields=['image'])
                    
                    fixed += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'[FIXED {fixed}] {product.name} → {secure_url}'
                    ))
                    
                except cloudinary.exceptions.NotFound:
                    failed += 1
                    self.stdout.write(self.style.ERROR(
                        f'[NOT FOUND] {product.name} - Image missing on Cloudinary'
                    ))
                
                # Commit every batch_size products
                if batch_count % batch_size == 0:
                    connection.close()  # Close and reopen connection
                    self.stdout.write(self.style.WARNING(
                        f'\n--- Batch complete: {batch_count}/{total} processed ---\n'
                    ))
                    time.sleep(0.5)  # Small delay to prevent overwhelming
                    
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f'[ERROR] {product.name}: {str(e)}'))
                # Don't let one error stop the whole process
                connection.close()
                time.sleep(0.5)
        
        # Final summary
        self.stdout.write(f'\n{"="*70}')
        self.stdout.write(self.style.SUCCESS('FINAL SUMMARY:'))
        self.stdout.write(self.style.SUCCESS(f'✓ Fixed: {fixed}'))
        self.stdout.write(self.style.WARNING(f'○ Already OK: {skipped}'))
        self.stdout.write(self.style.ERROR(f'✗ Failed: {failed}'))
        self.stdout.write(f'{"="*70}\n')
        
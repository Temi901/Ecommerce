from django.core.management.base import BaseCommand
from django.db import transaction
from shop.models import Product

class Command(BaseCommand):
    help = 'Directly fix image paths by adding .jpg extension'

    def handle(self, *args, **options):
        
        fixed = 0
        skipped = 0
        
        self.stdout.write(f'\n{"="*70}')
        self.stdout.write('Fixing image paths directly...')
        self.stdout.write(f'{"="*70}\n')
        
        # Get all products with images
        products = Product.objects.filter(image__isnull=False).exclude(image='')
        
        for product in products:
            try:
                current_path = str(product.image)
                
                # Skip if already has extension
                if any(current_path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                    skipped += 1
                    self.stdout.write(self.style.SUCCESS(f'[OK] {product.name} - {current_path}'))
                    continue
                
                # Check if it's a Cloudinary path without extension
                if current_path.startswith('products/product_'):
                    # Add .jpg extension (most common)
                    new_path = f'{current_path}.jpg'
                    
                    # Update the product
                    with transaction.atomic():
                        product.image = new_path
                        product.save(update_fields=['image'])
                    
                    fixed += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'[FIXED {fixed}] {product.name}\n'
                        f'         OLD: {current_path}\n'
                        f'         NEW: {new_path}\n'
                    ))
                else:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(
                        f'[SKIP] {product.name} - Unrecognized format: {current_path}'
                    ))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'[ERROR] {product.name}: {str(e)}'
                ))
        
        # Summary
        self.stdout.write(f'\n{"="*70}')
        self.stdout.write(self.style.SUCCESS('SUMMARY:'))
        self.stdout.write(self.style.SUCCESS(f'✓ Fixed: {fixed}'))
        self.stdout.write(self.style.WARNING(f'○ Skipped: {skipped}'))
        self.stdout.write(f'{"="*70}\n')
        
        if fixed > 0:
            self.stdout.write(self.style.SUCCESS(
                '\n✅ Database updated! Now run:\n'
                '   python manage.py runserver\n'
                '   and refresh your browser.\n'
            ))
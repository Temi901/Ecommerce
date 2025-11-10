from django.core.management.base import BaseCommand
from shop.models import Product
import cloudinary
import cloudinary.api
import os

class Command(BaseCommand):
    help = 'Fix product image URLs to use proper Cloudinary format'

    def handle(self, *args, **kwargs):
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'dznwck80z'),
            api_key=os.environ.get('CLOUDINARY_API_KEY', '253791256396167'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'BhGfUyC_Nr5pJfrdgFgQidQRLck'),
            secure=True
        )
        
        products = Product.objects.all()
        updated = 0
        failed = 0
        
        self.stdout.write(f'\nChecking {products.count()} products...\n')
        
        for product in products:
            try:
                # Check if image exists and needs fixing
                if product.image:
                    current_path = str(product.image)
                    
                    # If it's already a full URL, skip
                    if current_path.startswith('http'):
                        self.stdout.write(self.style.SUCCESS(f'✓ OK: {product.name}'))
                        continue
                    
                    # Extract public_id from path
                    # Path format: "products/product_87" or "products/product_87.jpg"
                    public_id = current_path.replace('products/', '').split('.')[0]
                    
                    # Try to get the resource from Cloudinary
                    try:
                        resource = cloudinary.api.resource(f'products/product_{product.id}')
                        cloudinary_url = resource['secure_url']
                        
                        # Update with the extension
                        file_format = resource.get('format', 'jpg')
                        new_path = f'products/product_{product.id}.{file_format}'
                        
                        product.image = new_path
                        product.save(update_fields=['image'])
                        
                        updated += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'✓ FIXED: {product.name}\n'
                            f'  Old: {current_path}\n'
                            f'  New: {new_path}\n'
                            f'  URL: {cloudinary_url}\n'
                        ))
                        
                    except cloudinary.exceptions.NotFound:
                        failed += 1
                        self.stdout.write(self.style.ERROR(
                            f'✗ NOT FOUND: {product.name}\n'
                            f'  Looking for: products/product_{product.id}\n'
                        ))
                        
                else:
                    self.stdout.write(self.style.WARNING(f'⚠ NO IMAGE: {product.name}'))
                    
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f'✗ ERROR: {product.name} - {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*60}\n'
            f'✅ Complete!\n'
            f'Updated: {updated}\n'
            f'Failed: {failed}\n'
            f'{"="*60}'
        ))
        
from django.core.management.base import BaseCommand
from shop.models import Product, Category
import cloudinary
import cloudinary.uploader
from pathlib import Path
import os
import sqlite3

class Command(BaseCommand):
    help = 'Migrate products from local SQLite to production with Cloudinary images'

    def handle(self, *args, **kwargs):
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME', 'dznwck80z'),
            api_key=os.environ.get('CLOUDINARY_API_KEY', '253791256396167'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET', 'BhGfUyC_Nr5pJfrdgFgQidQRLck'),
            secure=True
        )
        
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        local_db = BASE_DIR / 'db.sqlite3'
        media_dir = BASE_DIR / 'media'
        
        if not local_db.exists():
            self.stdout.write(self.style.ERROR('❌ Local database not found!'))
            return
        
        # Connect to local SQLite database
        conn = sqlite3.connect(str(local_db))
        cursor = conn.cursor()
        
        # Check if is_active column exists
        cursor.execute("PRAGMA table_info(shop_product)")
        columns = [col[1] for col in cursor.fetchall()]
        has_is_active = 'is_active' in columns
        
        # Get all products from local database
        if has_is_active:
            cursor.execute("""
                SELECT id, name, slug, description, price, stock, category_id, image, is_active
                FROM shop_product
            """)
        else:
            cursor.execute("""
                SELECT id, name, slug, description, price, stock, category_id, image
                FROM shop_product
            """)
        
        local_products = cursor.fetchall()
        total = len(local_products)
        created = 0
        updated = 0
        uploaded = 0
        failed = 0
        
        self.stdout.write(f'\nFound {total} products in local database\n')
        
        for row in local_products:
            if has_is_active:
                prod_id, name, slug, description, price, stock, category_id, image_path, is_active = row
            else:
                prod_id, name, slug, description, price, stock, category_id, image_path = row
                is_active = True  # Default to active
            
            try:
                # Get or create category
                if category_id:
                    cursor.execute("SELECT name, slug FROM shop_category WHERE id=?", (category_id,))
                    cat_data = cursor.fetchone()
                    if cat_data:
                        category, _ = Category.objects.get_or_create(
                            slug=cat_data[1],
                            defaults={'name': cat_data[0]}
                        )
                    else:
                        category = None
                else:
                    category = None
                
                # Check if product exists in production
                product, product_created = Product.objects.update_or_create(
                    slug=slug,
                    defaults={
                        'name': name,
                        'description': description or '',
                        'price': price,
                        'stock': stock,
                        'category': category,
                        'is_active': bool(is_active),
                    }
                )
                
                if product_created:
                    created += 1
                    status = "CREATED"
                else:
                    updated += 1
                    status = "UPDATED"
                
                # Handle image upload to Cloudinary
                if image_path:
                    local_image = media_dir / image_path
                    
                    if local_image.exists():
                        try:
                            # Upload to Cloudinary
                            result = cloudinary.uploader.upload(
                                str(local_image),
                                folder='products',
                                public_id=f'product_{product.id}',
                                overwrite=True,
                                resource_type='image'
                            )
                            
                            # Save Cloudinary path
                            cloudinary_path = f"products/product_{product.id}"
                            product.image = cloudinary_path
                            product.save(update_fields=['image'])
                            
                            uploaded += 1
                            self.stdout.write(self.style.SUCCESS(
                                f'✓ {status}: {name}\n'
                                f'  Image: {result["secure_url"]}'
                            ))
                        except Exception as e:
                            failed += 1
                            self.stdout.write(self.style.ERROR(
                                f'✗ {status}: {name} (Image upload failed: {e})'
                            ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'⚠ {status}: {name} (No local image found)'
                        ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'⚠ {status}: {name} (No image in database)'
                    ))
                    
            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f'✗ Failed: {name} - {str(e)}'))
        
        conn.close()
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*60}\n'
            f'✅ Migration Complete!\n'
            f'Created: {created}, Updated: {updated}\n'
            f'Images uploaded: {uploaded}, Failed: {failed}\n'
            f'{"="*60}'
        ))
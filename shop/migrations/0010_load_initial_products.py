from django.db import migrations
import json
import os

def load_products(apps, schema_editor):
    """Load products from products_data.json"""
    Product = apps.get_model('shop', 'Product')
    Category = apps.get_model('shop', 'Category')
    
    # Path to the JSON file
    json_file = os.path.join(os.path.dirname(__file__), '..', '..', 'products_data.json')
    
    if not os.path.exists(json_file):
        print(f"⚠️  Warning: products_data.json not found at {json_file}")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Load categories first
    categories_loaded = 0
    for item in data:
        if item['model'] == 'shop.category':
            if not Category.objects.filter(pk=item['pk']).exists():
                Category.objects.create(
                    id=item['pk'],
                    name=item['fields']['name'],
                    slug=item['fields']['slug']
                )
                categories_loaded += 1
    
    # Load products
    products_loaded = 0
    for item in data:
        if item['model'] == 'shop.product':
            if not Product.objects.filter(pk=item['pk']).exists():
                category = Category.objects.get(pk=item['fields']['category'])
                Product.objects.create(
                    id=item['pk'],
                    category=category,
                    name=item['fields']['name'],
                    slug=item['fields']['slug'],
                    description=item['fields']['description'],
                    price=item['fields']['price'],
                    available=item['fields']['available'],
                    stock=item['fields']['stock'],
                    created=item['fields']['created'],
                    updated=item['fields']['updated'],
                    # Note: images will be added separately
                )
                products_loaded += 1
    
    print(f"✅ Loaded {categories_loaded} categories and {products_loaded} products")

def reverse_func(apps, schema_editor):
    """Remove loaded products"""
    Product = apps.get_model('shop', 'Product')
    Category = apps.get_model('shop', 'Category')
    Product.objects.all().delete()
    Category.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0009_order_user_order_number'),  # Change this to your latest migration
    ]

    operations = [
        migrations.RunPython(load_products, reverse_func),
    ]
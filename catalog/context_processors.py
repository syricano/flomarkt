# catalog/context_processors.py
from .models import Category

def catalog_nav(request):
    roots = Category.objects.select_related("parent").filter(parent__isnull=True).order_by("name")
    return {
        "catalog_root_categories": roots,
        "catalog_quick_types": [
            ("PRODUCT", "Products"),
            ("SERVICE", "Services"),
            ("CAR", "Cars"),
            ("PROPERTY", "Real Estate"),
        ],
    }

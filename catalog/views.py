from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category


def product_list(request):
    category_slug = request.GET.get('category')
    sort = request.GET.get('sort')
    query = request.GET.get('q')

    products = Product.objects.filter(available=True)
    categories = Category.objects.all()

    # --- FILTERING ---
    if category_slug:
        products = products.filter(category__slug=category_slug)

    # --- SEARCH FUNCTIONALITY ---
    if query:
        products = products.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    # --- SORTING OPTIONS ---
    if sort == 'most_purchased':
        products = products.order_by('-times_purchased')
    elif sort == 'most_expensive':
        products = products.order_by('-price')
    else:
        products = products.order_by('-created_at')

    # --- PAGINATION ---
    # Pagination is only active when no filter/search is applied
    if not (category_slug or sort or query):
        paginator = Paginator(products, 9)  # 20 products per page
        page_number = request.GET.get('page')
        products = paginator.get_page(page_number)

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'selected_sort': sort,
        'query': query,
    }
    return render(request, 'catalog/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    size_range = range(product.min_size, product.max_size + 1)
    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'size_range': size_range
    })

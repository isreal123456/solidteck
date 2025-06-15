from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CategoryForm, ProductForm
from .models import Category, Product

User = get_user_model()

# Role check
def is_storekeeper(user):
    return user.is_authenticated and user.is_storekeeper

# ---------- CATEGORY CRUD ----------

@login_required
@user_passes_test(is_storekeeper)
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.save()
            return redirect('inventory')
    else:
        form = CategoryForm()
    return render(request, 'inventory/create_category.html', {'form': form})

@login_required
@user_passes_test(is_storekeeper)
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('inventory')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'inventory/edit_category.html', {'form': form, 'category': category})

@login_required
@user_passes_test(is_storekeeper)
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return redirect('inventory')

# ---------- PRODUCT CRUD ----------

@login_required
@user_passes_test(is_storekeeper)
def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            return redirect('inventory')
    else:
        form = ProductForm()
    return render(request, 'inventory/create_product.html', {'form': form})

@login_required
@user_passes_test(is_storekeeper)
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('inventory')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/edit_product.html', {'form': form, 'product': product})

@login_required
@user_passes_test(is_storekeeper)
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('inventory')

# ---------- INVENTORY VIEW ----------
def product_view(request, pk):
    product = Product.objects.filter(category_id=pk)
    return render(request, 'inventory/product.html', {'product': product})

@login_required
@user_passes_test(is_storekeeper)
def inventory_view(request):
    categories = Category.objects.all()
    return render(request, 'inventory/inventory.html', {'categories': categories})





@login_required
@user_passes_test(is_storekeeper)
def inventory_dashboard(request):
    total_categories = Category.objects.count()
    total_products = Product.objects.count()
    total_stock = Product.objects.aggregate(total_stock_qty=Sum('stock'))['total_stock_qty'] or 0
    low_stock_threshold = 10
    low_stock_products = Product.objects.filter(stock__lte=low_stock_threshold)
    recent_products = Product.objects.order_by('-created_at')[:5]
    recent_categories = Category.objects.order_by('-created_at')[:5]

    context = {
        'total_categories': total_categories,
        'total_products': total_products,
        'total_stock': total_stock,
        'low_stock_products': low_stock_products,
        'recent_products': recent_products,
        'recent_categories': recent_categories,
    }
    return render(request, 'inventory/dashboard.html', context)

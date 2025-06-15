from datetime import datetime
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Count, Sum, F, FloatField
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
import json

from django.utils.dateparse import parse_date
from openpyxl.workbook import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from inventory.forms import ProductForm, CategoryForm
from inventory.models import Category, Product
from logs.models import Log
from sales.forms import OrderItemFormSet, OrderForm
from sales.models import OrderItem, Order

User = get_user_model()
def is_admin(user):
    return user.is_authenticated and user.is_admin

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    import json
    from datetime import datetime

    # Get dates from GET parameters
    start_date = parse_date(request.GET.get('start_date')) if request.GET.get('start_date') else None
    end_date = parse_date(request.GET.get('end_date')) if request.GET.get('end_date') else None

    order_items = OrderItem.objects.all()
    orders = Order.objects.all()

    if start_date and end_date:
        orders = orders.filter(created_at__date__range=(start_date, end_date))
        order_items = order_items.filter(order__created_at__date__range=(start_date, end_date))

    # Totals
    total_categories = Category.objects.count()
    total_products = Product.objects.count()
    total_stock = Product.objects.aggregate(total=Sum('stock'))['total'] or 0
    total_orders = orders.count()

    total_revenue = order_items.aggregate(
        total=Sum(F('quantity') * F('product__price'), output_field=FloatField())
    )['total'] or 0

    # Revenue by month
    revenue_by_month = (
        order_items
        .annotate(month=TruncMonth('order__created_at'))
        .values('month')
        .annotate(total=Sum(F('quantity') * F('product__price'), output_field=FloatField()))
        .order_by('month')
    )
    labels = [item['month'].strftime('%b %Y') for item in revenue_by_month]
    data = [item['total'] for item in revenue_by_month]

    # Top 5 selling products
    top_products = (
        order_items
        .values('product__name')
        .annotate(count=Sum('quantity'))
        .order_by('-count')[:5]
    )
    top_labels = [item['product__name'] for item in top_products]
    top_data = [item['count'] for item in top_products]

    # Recent orders and logs
    recent_orders = orders.order_by('-created_at')[:5]
    recent_log = Log.objects.order_by('-created_at')[:5]

    context = {
        'total_categories': total_categories,
        'total_products': total_products,
        'total_stock': total_stock,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'labels': json.dumps(labels),
        'data': json.dumps(data),
        'top_labels': json.dumps(top_labels),
        'top_data': json.dumps(top_data),
        'recent_orders': recent_orders,
        'recent_log': recent_log,
    }

    return render(request, 'dashboard/admin_dashboard.html', context)
def product_view_admin(request, pk):
    product = Product.objects.filter(category_id=pk)
    return render(request, 'dashboard/product.html', {'product': product})

@login_required
@user_passes_test(is_admin)
def catergory_view(request):
    categories = Category.objects.all()
    return render(request, 'dashboard/category.html', {'categories': categories})

@login_required
@user_passes_test(is_admin)
def order_list(request):
    orders = Order.objects.all().select_related('sold_by')
    return render(request, 'dashboard/order.html', {'orders': orders})

@login_required
@user_passes_test(is_admin)
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('sold_by'), pk=pk)
    return render(request, 'dashboard/order_detail.html', {'order': order})

@login_required
@user_passes_test(is_admin)
def order_list(request):
    orders = Order.objects.all()

    customer = request.GET.get('customer')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if customer:
        orders = orders.filter(customer_name__icontains=customer)
    if start_date:
        orders = orders.filter(created_at__date__gte=parse_date(start_date))
    if end_date:
        orders = orders.filter(created_at__date__lte=parse_date(end_date))

    return render(request, 'dashboard/order.html', {'orders': orders})

from django.db.models import Q


def filter_admin_products(request):
    products = Product.objects.annotate(total_sold=Sum('orderitem__quantity'))

    name = request.GET.get('name')
    min_stock = request.GET.get('min_stock')
    max_stock = request.GET.get('max_stock')
    min_sold = request.GET.get('min_sold')
    max_sold = request.GET.get('max_sold')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if name:
        products = products.filter(name__icontains=name)

    if min_stock:
        try:
            products = products.filter(stock__gte=int(min_stock))
        except ValueError:
            pass

    if max_stock:
        try:
            products = products.filter(stock__lte=int(max_stock))
        except ValueError:
            pass

    if min_sold:
        try:
            products = products.filter(total_sold__gte=int(min_sold))
        except ValueError:
            pass

    if max_sold:
        try:
            products = products.filter(total_sold__lte=int(max_sold))
        except ValueError:
            pass
    if start_date:
        parsed_start = parse_date(start_date)
        if parsed_start:
            products = products.filter(created_at__gte=parsed_start)

    if end_date:
        parsed_end = parse_date(end_date)
        if parsed_end:
            products = products.filter(created_at__lte=parsed_end)

    return products

@login_required
@user_passes_test(is_admin)
def admin_report(request):
    products = filter_admin_products(request)

    product_labels = [p.name for p in products]
    product_sales_data = [p.total_sold or 0 for p in products]
    product_stock_data = [p.stock for p in products]

    return render(request, 'dashboard/admin_report.html', {
        'products': products,
        'product_labels': product_labels,
        'product_sales_data': product_sales_data,
        'product_stock_data': product_stock_data,
        'request': request,
    })

def export_admin_report_excel(request):
    products = filter_admin_products(request)
    wb = Workbook()
    ws = wb.active
    ws.title = "Admin Report"
    ws.append(['Product Name', 'Stock Level', 'Total Sold'])

    for p in products:
        ws.append([p.name, p.stock, p.total_sold or 0])

    filename = f"admin_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    return response

def export_admin_report_pdf(request):
    products = filter_admin_products(request)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 14)
    p.drawString(200, height - 50, "🧾 Admin Report")
    p.setFont("Helvetica", 11)
    p.drawString(40, height - 70, "Product | Stock | Sold")

    y = height - 90
    p.setFont("Helvetica", 10)

    for product in products:
        line = f"{product.name} | {product.stock} | {product.total_sold or 0}"
        p.drawString(40, y, line)
        y -= 15
        if y < 50:
            p.showPage()
            y = height - 50

    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')


@login_required
@user_passes_test(is_admin)
def create_category_admin(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.save()
            return redirect('inventory_view_admin')
    else:
        form = CategoryForm()
    return render(request, 'dashboard/create_category_admin.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def edit_category_admin(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('inventory_view_admin')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'dashboard/edit_category_admin.html', {'form': form, 'category': category})

@login_required
@user_passes_test(is_admin)
def delete_category_admin(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return redirect('inventory_view_admin')

# ---------- PRODUCT CRUD ----------

@login_required
@user_passes_test(is_admin)
def create_product_admin(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            return redirect('inventory_view_admin')
    else:
        form = ProductForm()
    return render(request, 'dashboard/create_product_admin.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def edit_product_admin(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('inventory_view_admin')
    else:
        form = ProductForm(instance=product)
    return render(request, 'dashboard/edit_product_admin.html', {'form': form, 'product': product})

@login_required
@user_passes_test(is_admin)
def delete_product_admin(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('inventory_view_admin')


@login_required
@user_passes_test(is_admin)
@transaction.atomic
def create_order_admin(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            if not any(f.cleaned_data for f in formset.forms):
                formset._non_form_errors = formset.error_class(["At least one item is required."])
            else:
                order = form.save(commit=False)
                order.sold_by = request.user
                order.save()
                formset.instance = order
                formset.save()

                # Check stock before committing and show alert
                insufficient_stock_items = []
                for item in order.items.select_related('product'):
                    product = item.product
                    if product.stock < item.quantity:
                        insufficient_stock_items.append(f"{product.name} (Available: {product.stock}, Requested: {item.quantity})")

                if insufficient_stock_items:
                    # Delete saved order and items to rollback
                    order.delete()
                    formset._non_form_errors = formset.error_class([
                        f"Insufficient stock for: {', '.join(insufficient_stock_items)}"
                    ])
                else:
                    # Update stock
                    for item in order.items.select_related('product'):
                        product = item.product
                        product.stock -= item.quantity
                        product.save()

                return redirect('detail', pk=order.pk)
    else:
        form = OrderForm()
        formset = OrderItemFormSet()

    return render(request, 'dashboard/create_order_admin.html', {'form': form, 'formset': formset})# --- Order Views ---

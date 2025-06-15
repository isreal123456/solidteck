import json
from io import BytesIO
from datetime import datetime
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Sum, F
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.dateparse import parse_date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from openpyxl import Workbook

from inventory.models import Product
from .models import Order, OrderItem
from .forms import OrderForm, OrderItemFormSet

User = get_user_model()
def is_salesperson(user):
    return user.is_authenticated and user.is_salesperson()

# --- Helper to filter orders ---
def filter_orders(request):
    orders = Order.objects.all()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    user_id = request.GET.get('user')

    if start_date:
        orders = orders.filter(created_at__date__gte=start_date)
    if end_date:
        orders = orders.filter(created_at__date__lte=end_date)
    if user_id:
        orders = orders.filter(sold_by_id=user_id)

    return orders

# --- Create Order ---

@login_required
@user_passes_test(is_salesperson)
@transaction.atomic
def create_order(request):
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

                    return redirect('order_detail', pk=order.pk)
    else:
        form = OrderForm()
        formset = OrderItemFormSet()

    return render(request, 'sales/create_order.html', {'form': form, 'formset': formset})# --- Order Views ---
@login_required
@user_passes_test(is_salesperson)
def order_list(request):
    orders = Order.objects.all().select_related('sold_by')

    customer = request.GET.get('customer')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    user_id = request.GET.get('user')

    if customer:
        orders = orders.filter(customer_name__icontains=customer)
    if start_date:
        orders = orders.filter(created_at__date__gte=start_date)
    if end_date:
        orders = orders.filter(created_at__date__lte=end_date)
    if user_id:
        orders = orders.filter(sold_by_id=user_id)

    users = User.objects.all()

    return render(request, 'sales/order_list.html', {
        'orders': orders,
        'users': users
    })

@login_required
@user_passes_test(is_salesperson)
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('sold_by'), pk=pk)
    return render(request, 'sales/order_detail.html', {'order': order})

# --- Dashboard ---
@login_required
@user_passes_test(is_salesperson)
def dashboard(request):
    orders = filter_orders(request).select_related('sold_by').prefetch_related('items__product')

    total_orders = orders.count()
    total_revenue = orders.aggregate(total=Sum(F('items__product__price') * F('items__quantity')))['total'] or 0

    sales_by_date = orders.annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(total=Sum(F('items__product__price') * F('items__quantity'))) \
        .order_by('date')

    date_labels = [entry['date'].strftime('%Y-%m-%d') for entry in sales_by_date]
    revenue_data = [float(entry['total'] or 0) for entry in sales_by_date]

    top_products = OrderItem.objects.filter(order__in=orders) \
        .values(name=F('product__name')) \
        .annotate(total_sold=Sum('quantity')) \
        .order_by('-total_sold')[:5]

    top_product_labels = [p['name'] for p in top_products]
    top_product_data = [p['total_sold'] for p in top_products]

    users = User.objects.all()

    return render(request, 'sales/dashboard.html', {
        'total_orders': total_orders,
        'total_revenue': float(total_revenue),
        'date_labels': json.dumps(date_labels),
        'revenue_data': json.dumps(revenue_data),
        'top_product_labels': json.dumps(top_product_labels),
        'top_product_data': json.dumps(top_product_data),
        'users': users,
    })
# --- Sales Report View ---
@login_required
@user_passes_test(is_salesperson)
def sales_report(request):
    orders = filter_orders(request)
    total_orders = orders.count()
    total_revenue = orders.aggregate(total=Sum(F('items__product__price') * F('items__quantity')))['total'] or 0

    daily_sales = orders.annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(revenue=Sum(F('items__product__price') * F('items__quantity'))) \
        .order_by('date')

    users = User.objects.all()

    return render(request, 'sales/sales_report.html', {
        'orders': orders,
        'daily_sales': daily_sales,
        'total_orders': total_orders,
        'total_revenue': float(total_revenue),
        'users': users,
    })

# --- Export to Excel ---
def generate_excel(orders, sheet_title, filename_prefix):
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title
    ws.append(['Order ID', 'Customer', 'Sold By', 'Created At', 'Total Amount'])

    for order in orders:
        total = order.items.aggregate(
            total=Sum(F('product__price') * F('quantity'))
        )['total'] or 0
        ws.append([
            order.id,
            order.customer_name,
            str(order.sold_by),
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            float(total),
        ])

    filename = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    return response

@login_required
@user_passes_test(is_salesperson)
def export_orders_excel(request):
    orders = filter_orders(request).prefetch_related('items__product')
    return generate_excel(orders, "Filtered Orders", "filtered_orders")

@login_required
@user_passes_test(is_salesperson)
def export_sales_excel(request):
    orders = filter_orders(request).prefetch_related('items__product')
    return generate_excel(orders, "Sales Report", "sales_report")

# --- Export to PDF ---
def draw_pdf_header(p, title, height):
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, title)
    p.setFont("Helvetica", 12)
    p.drawString(40, height - 70, "ID | Customer | Sold By | Date | Total")

def generate_pdf(orders, title):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    draw_pdf_header(p, title, height)
    y = height - 90
    p.setFont("Helvetica", 10)

    for order in orders:
        total = order.items.aggregate(
            total=Sum(F('product__price') * F('quantity'))
        )['total'] or 0
        line = f"{order.id} | {order.customer_name} | {order.sold_by} | {order.created_at.strftime('%Y-%m-%d')} | ₦{float(total):,.2f}"
        p.drawString(40, y, line)
        y -= 15
        if y < 50:
            p.showPage()
            draw_pdf_header(p, title, height)
            y = height - 90

    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

@login_required
def export_orders_pdf(request):
    orders = filter_orders(request).prefetch_related('items__product')
    return generate_pdf(orders, "Filtered Order Report")

@login_required
def export_sales_pdf(request):
    orders = filter_orders(request).prefetch_related('items__product')
    return generate_pdf(orders, "Sales Report")

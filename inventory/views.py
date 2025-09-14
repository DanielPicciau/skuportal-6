import csv, io
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.db.models import Q, Sum, F, DecimalField, ExpressionWrapper, Avg
from decimal import Decimal
from .constants import STATUSES, CATEGORIES
from .models import Product, Variant, ProductImage
from .forms import ProductForm, VariantForm, ImportFileForm
from .csv_sync import schedule_csv_sync

@login_required
def dashboard(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    products_qs = Product.objects.prefetch_related('variants')
    if q:
        products_qs = products_qs.filter(
            Q(name__icontains=q) |
            Q(brand__icontains=q) |
            Q(category__icontains=q) |
            Q(main_sku__iexact=q) |
            Q(main_sku__icontains=q) |
            Q(variants__variant_sku__iexact=q) |
            Q(variants__variant_sku__icontains=q)
        )
    if status and status in STATUSES:
        products_qs = products_qs.filter(variants__status=status)
    show_archived = request.GET.get('archived', '') in ('1','true','yes')
    if not show_archived:
        products_qs = products_qs.filter(archived=False)
    # Archived filter: archived=1 shows ONLY archived; default shows ONLY active
    show_archived = request.GET.get('archived', '') in ('1','true','yes')
    if show_archived:
        products_qs = products_qs.filter(archived=True)
    else:
        products_qs = products_qs.filter(archived=False)
    products = products_qs.order_by('-id').distinct()[:100]
    # Build category suggestions from constants + DB
    db_cats = list(Product.objects.values_list('category', flat=True).distinct())
    cat_suggestions = sorted({*(c for c in CATEGORIES), *(c for c in db_cats if c)})
    return render(request, 'inventory/dashboard.html', {
        'products': products,
        'q': q,
        'status': status,
        'statuses': STATUSES,
        'categories': cat_suggestions,
        'show_archived': show_archived,
    })

@login_required
def home(request):
    # High-level KPIs; profit only from Sold variants
    sold_qs = Variant.objects.filter(status='Sold')
    listed_qs = Variant.objects.filter(status='Listed')
    unsold_qs = Variant.objects.exclude(status='Sold')
    total_profit = sold_qs.aggregate(total=Sum('profit'))['total'] or Decimal('0')
    total_net = sold_qs.aggregate(total=Sum('net'))['total'] or Decimal('0')
    # Stock-level sums (qty-aware)
    sum_price_qty = ExpressionWrapper(F('price') * F('qty'), output_field=DecimalField(max_digits=12, decimal_places=2))
    sum_cost_qty = ExpressionWrapper(F('cost') * F('qty'), output_field=DecimalField(max_digits=12, decimal_places=2))
    stock_list_value = unsold_qs.aggregate(total=Sum(sum_price_qty))['total'] or Decimal('0')
    stock_cost_value = unsold_qs.aggregate(total=Sum(sum_cost_qty))['total'] or Decimal('0')
    listed_list_value = listed_qs.aggregate(total=Sum(sum_price_qty))['total'] or Decimal('0')

    totals = {
        'products': Product.objects.count(),
        'variants': Variant.objects.count(),
        'sold': sold_qs.aggregate(q=Sum('qty'))['q'] or 0,
        'listed': listed_qs.aggregate(q=Sum('qty'))['q'] or 0,
        'draft': Variant.objects.filter(status='Draft').aggregate(q=Sum('qty'))['q'] or 0,
    }
    # Milestones (simple defaults)
    milestone_targets = [Decimal('100'), Decimal('500'), Decimal('1000'), Decimal('5000')]
    next_target = None
    for m in milestone_targets:
        if total_profit < m:
            next_target = m
            break
    progress_pct = int((total_profit / next_target * 100)) if next_target and next_target > 0 else 100
    # Top categories by sold count
    # Top categories with percentage bars
    raw_top_categories = list(
        sold_qs.select_related('product')
        .values('product__category')
        .annotate(count=Sum('qty'))
        .order_by('-count')[:5]
    )
    max_cat = max([row['count'] for row in raw_top_categories], default=0)
    top_categories = [
        {
            'category': row['product__category'],
            'count': row['count'],
            'pct': int((row['count'] / max_cat * 100)) if max_cat else 0,
        }
        for row in raw_top_categories
    ]

    # Top brands by units sold and profit
    top_brands = list(
        sold_qs.select_related('product')
        .values('product__brand')
        .annotate(count=Sum('qty'), profit=Sum('profit'))
        .order_by('-count')[:5]
    )

    avg_margin = sold_qs.aggregate(m=Avg('margin'))['m'] or Decimal('0')
    recent = Variant.objects.select_related('product').order_by('-id')[:6]
    ctx = {
        'total_profit': total_profit,
        'total_net': total_net,
        'totals': totals,
        'next_target': next_target,
        'progress_pct': progress_pct,
        'top_categories': top_categories,
        'top_brands': top_brands,
        'avg_margin': avg_margin,
        'stock_list_value': stock_list_value,
        'stock_cost_value': stock_cost_value,
        'listed_list_value': listed_list_value,
        'recent': recent,
    }
    return render(request, 'inventory/home.html', ctx)

@login_required
def bulk_update(request):
    if request.method != 'POST':
        return redirect('inventory:dashboard')
    ids = request.POST.getlist('ids')
    set_status = request.POST.get('set_status', '').strip()
    set_location = request.POST.get('set_location', '').strip()
    set_category = request.POST.get('set_category', '').strip()

    if not ids:
        messages.error(request, 'No items selected.')
        return redirect('inventory:dashboard')

    # Update selected products and their variants
    products = Product.objects.filter(pk__in=ids)
    updated = 0
    if set_category:
        updated += products.update(category=set_category)
    if set_status or set_location:
        vqs = Variant.objects.filter(product__in=products)
        update_kwargs = {}
        if set_status and set_status in STATUSES:
            update_kwargs['status'] = set_status
        if set_location:
            update_kwargs['location'] = set_location
        if update_kwargs:
            updated += vqs.update(**update_kwargs)

    messages.success(request, f'Updated {updated} fields on selected items.')
    schedule_csv_sync()
    return redirect('inventory:dashboard')

@login_required
def product_create(request):
    if request.method == 'POST':
        pform = ProductForm(request.POST)
        vform = VariantForm(request.POST, request.FILES)
        if pform.is_valid() and vform.is_valid():
            product = pform.save()
            variant = vform.save(commit=False)
            variant.product = product
            variant.save()
            # handle multiple images
            files = request.FILES.getlist('new_images') or request.FILES.getlist('images')
            for f in files:
                ProductImage.objects.create(variant=variant, image=f)
            messages.success(request, 'Product created successfully.')
            schedule_csv_sync()
            return redirect('inventory:product_detail', pk=product.pk)
        else:
            pass
    else:
        pform = ProductForm()
        vform = VariantForm()
    db_cats = list(Product.objects.values_list('category', flat=True).distinct())
    cat_suggestions = sorted({*(c for c in CATEGORIES), *(c for c in db_cats if c)})
    return render(request, 'inventory/product_form.html', {'pform': pform, 'vform': vform, 'categories': cat_suggestions})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'inventory/product_detail.html', {'product': product})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated.')
            schedule_csv_sync()
            return redirect('inventory:product_detail', pk=product.pk)
        else:
            pass
    else:
        form = ProductForm(instance=product)
    db_cats = list(Product.objects.values_list('category', flat=True).distinct())
    cat_suggestions = sorted({*(c for c in CATEGORIES), *(c for c in db_cats if c)})
    return render(request, 'inventory/product_edit.html', {'form': form, 'product': product, 'categories': cat_suggestions})

@login_required
def variant_edit(request, pk):
    variant = get_object_or_404(Variant, pk=pk)
    if request.method == 'POST':
        form = VariantForm(request.POST, request.FILES, instance=variant)
        if form.is_valid():
            variant = form.save()
            files = request.FILES.getlist('new_images') or request.FILES.getlist('images')
            for f in files:
                ProductImage.objects.create(variant=variant, image=f)
            messages.success(request, 'Variant updated.')
            schedule_csv_sync()
            return redirect('inventory:product_detail', pk=variant.product.pk)
        else:
            pass
    else:
        form = VariantForm(instance=variant)
    return render(request, 'inventory/variant_form.html', {'form': form, 'variant': variant})

@login_required
def variant_create(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = VariantForm(request.POST, request.FILES)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            files = request.FILES.getlist('new_images') or request.FILES.getlist('images')
            for f in files:
                ProductImage.objects.create(variant=variant, image=f)
            messages.success(request, 'Variant added.')
            schedule_csv_sync()
            return redirect('inventory:product_detail', pk=product.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = VariantForm()
    return render(request, 'inventory/variant_create.html', {'form': form, 'product': product})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product "{name}" deleted.')
        schedule_csv_sync()
        return redirect('inventory:dashboard')
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})

@login_required
def variant_delete(request, pk):
    variant = get_object_or_404(Variant, pk=pk)
    product = variant.product
    if request.method == 'POST':
        sku = variant.variant_sku
        variant.delete()
        messages.success(request, f'Variant {sku or ""} deleted.')
        schedule_csv_sync()
        return redirect('inventory:product_detail', pk=product.pk)
    return render(request, 'inventory/variant_confirm_delete.html', {'variant': variant})

@login_required
def product_archive(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.archived = True
        product.save(update_fields=['archived'])
        messages.success(request, f'Archived {product.name}.')
        schedule_csv_sync()
        return redirect('inventory:dashboard')
    return redirect('inventory:product_detail', pk=pk)

@login_required
def product_unarchive(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.archived = False
        product.save(update_fields=['archived'])
        messages.success(request, f'Restored {product.name}.')
        schedule_csv_sync()
        return redirect('inventory:dashboard')
    return redirect('inventory:product_detail', pk=pk)

def signup(request):
    # Allow signup only if no users exist yet
    if User.objects.exists():
        messages.info(request, 'Signup is disabled. Please log in.')
        return redirect('login')
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        pwd1 = request.POST.get('password1') or ''
        pwd2 = request.POST.get('password2') or ''
        if not username or not pwd1:
            messages.error(request, 'Username and password are required.')
        elif pwd1 != pwd2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(username=username, password=pwd1)
            auth_login(request, user)
            return redirect('inventory:home')
    return render(request, 'auth/signup.html')

def import_products(request):
    if request.method == 'POST':
        form = ImportFileForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data['file']
            name = f.name.lower()
            try:
                if name.endswith('.csv'):
                    decoded = f.read().decode('utf-8')
                    # Robust delimiter detection based on header column count
                    lines = [ln for ln in decoded.splitlines() if ln.strip()]
                    header = lines[0] if lines else ''
                    candidates = ['\t', ',', ';', '|']
                    best = max(candidates, key=lambda d: len(header.split(d)))
                    if len(header.split(best)) <= 1:
                        best = ','
                    reader = csv.DictReader(io.StringIO(decoded), delimiter=best)
                    count = _ingest_rows(reader)
                elif name.endswith('.xlsx'):
                    try:
                        import openpyxl
                    except ImportError:
                        messages.error(request, 'XLSX import requires openpyxl. Install it and try again.')
                        return redirect('inventory:import_products')
                    wb = openpyxl.load_workbook(f)
                    ws = wb.active
                    headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
                    rows = (dict(zip(headers, [cell.value for cell in row])) for row in ws.iter_rows(min_row=2))
                    count = _ingest_rows(rows)
                else:
                    messages.error(request, 'Unsupported file type. Please upload CSV or XLSX.')
                    return redirect('inventory:import_products')
                messages.success(request, f'Imported {count} rows successfully.')
                return redirect('inventory:dashboard')
            except Exception as e:
                messages.error(request, f'Import failed: {e}')
                return redirect('inventory:import_products')
    else:
        form = ImportFileForm()
    return render(request, 'inventory/import.html', {'form': form})

def _ingest_rows(rows):
    count = 0
    for row in rows:
        # Normalize header keys: trim whitespace and unify casing
        norm = {}
        for k, v in row.items():
            kk = (k or '')
            if isinstance(kk, str):
                kk = kk.strip()
            norm[kk] = v
        row = norm
        # Accept flexible headers and synonyms
        def get_val(keys, default=''):
            for k in keys:
                if k in row and row.get(k) is not None:
                    v = row.get(k)
                    return v.strip() if isinstance(v, str) else v
            return default

        # Core fields
        name = (get_val(['Product Name', 'Title', 'Name'], '') or '').strip()
        if not name:
            continue
        brand = (get_val(['Brand'], '') or '')
        category = (get_val(['Category'], 'Clothing') or 'Clothing')

        # Optional main SKU handling (support Master/Main); zero-pad numeric
        main_sku_in = str(get_val(['Main SKU', 'Master SKU'], '') or '').strip()
        if main_sku_in.isdigit():
            main_sku_in = f"{int(main_sku_in):03d}"

        product = None
        if main_sku_in:
            product = Product.objects.filter(main_sku=main_sku_in).first()
        if product is None:
            product = Product.objects.create(name=name, brand=brand, category=category, main_sku=main_sku_in or '')

        variant_sku_in = (get_val(['Variant SKU', 'SKU Variant'], '') or '').strip()
        variant = None
        if variant_sku_in:
            variant = Variant.objects.filter(variant_sku=variant_sku_in).first()
        if variant is None:
            variant = Variant(product=product)
            if variant_sku_in:
                variant.variant_sku = variant_sku_in
        # assign fields
        variant.size = (get_val(['Size'], '') or '')[:40]
        variant.condition = (get_val(['Condition'], 'Good') or 'Good')
        variant.colour = (get_val(['Colour', 'Color'], '') or '')
        try:
            variant.qty = int(get_val(['Qty', 'Quantity'], 1) or 1)
        except Exception:
            variant.qty = 1
        variant.location = (get_val(['Location', 'Location/Bin', 'Bin', 'Shelf'], 'Spare Room') or 'Spare Room')
        variant.status = (get_val(['Status'], 'Draft') or 'Draft')
        # numeric and date parsing
        def parse_money(val):
            if val is None: return 0
            s = str(val).replace('£','').strip()
            return float(s or 0)
        def parse_date(val):
            if not val: return datetime.now().date()
            if isinstance(val, datetime): return val.date()
            for fmt in ('%d/%m/%Y','%Y-%m-%d','%d-%m-%Y'):
                try: return datetime.strptime(str(val), fmt).date()
                except: pass
            return datetime.now().date()

        variant.date = parse_date(get_val(['Date', 'Purchase Date']))
        variant.cost = parse_money(get_val(['Cost', 'Purchase Price', 'Buy Price']))
        variant.price = parse_money(get_val(['Price', 'Listed Price', 'Sale Price']))
        variant.fees = parse_money(get_val(['Fees', 'Estimated Fees', 'Platform Fees']))
        variant.save()
        count += 1
    return count

@login_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    writer = csv.writer(response)
    writer.writerow(['Main SKU','Variant SKU','Product Name','Brand','Category','Size','Condition','Colour','Date','Cost','Price','Fees','Net','Profit','Margin','Qty','Location','Status'])
    for v in Variant.objects.select_related('product').all():
        writer.writerow([
            v.product.main_sku, v.variant_sku, v.product.name, v.product.brand, v.product.category,
            v.size, v.condition, v.colour, v.date.strftime('%d/%m/%Y'), f"{v.cost:.2f}", f"{v.price:.2f}", f"{v.fees:.2f}",
            f"{v.net:.2f}", f"{v.profit:.2f}", f"{v.margin:.2f}%", v.qty, v.location, v.status
        ])
    return response

@login_required
def export_xlsx(request):
    try:
        import openpyxl
    except ImportError:
        return HttpResponse("XLSX export requires openpyxl library.", status=400)
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"
    headers = ['Main SKU','Variant SKU','Product Name','Brand','Category','Size','Condition','Colour','Date','Cost','Price','Fees','Net','Profit','Margin','Qty','Location','Status']
    ws.append(headers)
    for v in Variant.objects.select_related('product').all():
        ws.append([
            v.product.main_sku, v.variant_sku, v.product.name, v.product.brand, v.product.category,
            v.size, v.condition, v.colour, v.date.strftime('%d/%m/%Y'), float(v.cost), float(v.price), float(v.fees),
            float(v.net), float(v.profit), f"{v.margin:.2f}%", v.qty, v.location, v.status
        ])
    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    resp = HttpResponse(bio.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="products.xlsx"'
    return resp

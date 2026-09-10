from datetime import date
from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.core.cache import cache
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Case, IntegerField, Sum, Value, When

from .models import Category, SubCategory, Item, Currency, ExpenseEntry, CurrencyRate
from .serializers import (
    CategorySerializer,
    SubCategorySerializer,
    ItemSerializer,
    CurrencySerializer,
    CurrencyRateSerializer,
    ExpenseEntrySerializer,
)
from .services.prediction_service import ExpensePredictor
from .services.anomaly_service import detect_anomalies
from .services.expense_service import ExpenseService
from .services.report_service import ReportService
from .services.summary_service import SummaryService
from .services.currency_service import CurrencyService
from .services.intelligence_service import IntelligenceService


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (obj.user == request.user or request.user.is_staff)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by(
            Case(When(name__iexact='Other', then=Value(1)), default=Value(0), output_field=IntegerField()),
            'name',
        )


class SubCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SubCategory.objects.filter(category__is_active=True).select_related('category').order_by(
            'category__name',
            Case(When(name__iexact='Other', then=Value(1)), default=Value(0), output_field=IntegerField()),
            'name',
        )


class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Item.objects.select_related('category', 'subcategory').all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Item.objects.filter(category__is_active=True).select_related('category', 'subcategory').all()
        category = self.request.query_params.get('category')
        subcategory = self.request.query_params.get('subcategory')
        if category:
            queryset = queryset.filter(category_id=category)
        if subcategory:
            queryset = queryset.filter(subcategory_id=subcategory)
        return queryset.order_by('description')


class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.filter(is_active=True)
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticated]


class CurrencyRateViewSet(viewsets.ModelViewSet):
    queryset = CurrencyRate.objects.all()
    serializer_class = CurrencyRateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('-effective_date')


class ExpenseEntryViewSet(viewsets.ModelViewSet):
    """ViewSet for expense entries with separation of concerns."""
    
    serializer_class = ExpenseEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Get expenses for current user only (staff can still access if they're the owner)."""
        user = self.request.user
        # All users, including staff, see only their own expenses
        return ExpenseEntry.objects.filter(user=user).select_related(
            'category', 'item', 'currency', 'subcategory'
        )

    def perform_create(self, serializer):
        """Create expense and assign it to the current user."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Get expense summary for different time periods."""
        target_currency = request.query_params.get('target_currency', 'EUR').upper()
        summary_service = SummaryService(request.user)
        totals = summary_service.get_all_summaries(target_currency=target_currency)
        
        return Response({
            'currency': target_currency,
            'daily': float(totals['daily']),
            'weekly': float(totals['weekly']),
            'monthly': float(totals['monthly']),
            'quarterly': float(totals['quarterly']),
            'annual': float(totals['annual']),
        })

    @action(detail=False, methods=['get'], url_path='summary-range')
    def summary_range(self, request):
        """Get a converted total for an inclusive user-selected date range."""
        try:
            start_date = date.fromisoformat(request.query_params['start_date'])
            end_date = date.fromisoformat(request.query_params['end_date'])
        except (KeyError, ValueError):
            return Response({'detail': 'start_date and end_date must use YYYY-MM-DD.'}, status=400)

        if start_date > end_date:
            return Response({'detail': 'start_date must be on or before end_date.'}, status=400)

        target_currency = request.query_params.get('target_currency', 'EUR').upper()
        total = SummaryService(request.user).get_range_summary(start_date, end_date, target_currency)
        return Response({
            'start_date': start_date,
            'end_date': end_date,
            'currency': target_currency,
            'total': float(total),
        })

    @action(detail=False, methods=['get'], url_path='yearly/(?P<year>[^/.]+)')
    def yearly(self, request, year=None):
        """Get total expenses for a specific year."""
        target_currency = request.query_params.get('target_currency', 'EUR').upper()
        summary_service = SummaryService(request.user)
        total = summary_service.get_yearly_total(int(year), target_currency=target_currency)
        
        return Response({
            'year': year,
            'currency': target_currency,
            'total': float(total)
        })

    @action(detail=False, methods=['get'], url_path='category-summary')
    def category_summary(self, request):
        """Get converted totals grouped by category for the relevant year.

        Default to the latest expense year for the user so older back-dated entries remain visible.
        """
        summary_service = SummaryService(request.user)
        try:
            year = int(request.query_params.get('year', summary_service.get_latest_expense_year()))
        except ValueError:
            return Response({'detail': 'year must be a valid integer.'}, status=400)

        target_currency = request.query_params.get('target_currency', 'EUR').upper()
        totals = summary_service.get_yearly_by_category(year, target_currency)
        return Response({
            'year': year,
            'currency': target_currency,
            'categories': [
                {**item, 'total': float(item['total'])}
                for item in totals
            ],
        })

    @action(detail=False, methods=['get'], url_path='chart')
    def chart(self, request):
        """Get chart data with category breakdown, converted to target currency."""
        target_currency = request.query_params.get('target_currency', 'EUR').upper()
        expense_service = ExpenseService(request.user)
        expensive = expense_service.get_top_expensive_categories(limit=5, target_currency=target_currency)
        least = expense_service.get_least_expensive_categories(limit=3, target_currency=target_currency)
        
        return Response({
            'expensive': expensive,
            'least': least
        })

    @action(detail=False, methods=['get'], url_path='prediction')
    def prediction(self, request):
        """Get predicted expenses for next month."""
        target_currency = request.query_params.get('target_currency', 'EUR').upper()
        predictor = ExpensePredictor(request.user)
        return Response(predictor.predict_next_month(target_currency))

    @action(detail=False, methods=['get'], url_path='insights')
    def insights(self, request):
        """Get insights including anomaly detection."""
        target_currency = request.query_params.get('target_currency', 'EUR').upper()
        anomalies = IntelligenceService.anomaly_summary(request.user, target_currency)
        predictor = ExpensePredictor(request.user)
        return Response({
            'anomalies': anomalies,
            'predictions': predictor.predict_next_month(target_currency),
            'budget_recommendations': IntelligenceService.budget_recommendations(request.user, target_currency),
            'financial_insights': IntelligenceService.financial_insights(request.user, target_currency),
            'currency': target_currency,
        })

    @action(detail=False, methods=['post'], url_path='parse-quick-entry')
    def parse_quick_entry(self, request):
        """Parse natural language into a reviewable expense draft; never saves it."""
        text = request.data.get('text', '')
        if not isinstance(text, str) or not text.strip():
            return Response({'detail': 'text is required.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(IntelligenceService.parse_quick_entry(text, request.user))


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_rates(request):
    """Return the active weekly conversion matrix from Redis cache with a DB fallback."""
    cached_rates = cache.get('active_weekly_rates')
    if cached_rates:
        return Response({'source': 'cache', 'rates': cached_rates})

    symbols = ['EUR', 'USD', 'UGX']
    default_currency_map = {
        'EUR': {'name': 'Euro', 'symbol': '€'},
        'USD': {'name': 'US Dollar', 'symbol': '$'},
        'UGX': {'name': 'Uganda Shilling', 'symbol': 'USh'},
    }
    for code, meta in default_currency_map.items():
        Currency.objects.get_or_create(
            code=code,
            defaults={'name': meta['name'], 'symbol': meta['symbol'], 'is_active': True},
        )

    matrix = {}
    for base in symbols:
        base_currency = Currency.objects.filter(code=base).first()
        if not base_currency:
            continue
        row = {}
        for target in symbols:
            target_currency = Currency.objects.filter(code=target).first()
            if not target_currency:
                continue
            if base == target:
                row[target] = 1.0
                continue
            latest = CurrencyRate.objects.filter(
                base_currency=base_currency,
                target_currency=target_currency,
            ).order_by('-effective_date', '-id').first()
            if latest:
                row[target] = float(latest.rate)
                continue
            reverse = CurrencyRate.objects.filter(
                base_currency=target_currency,
                target_currency=base_currency,
            ).order_by('-effective_date', '-id').first()
            row[target] = float(1 / reverse.rate) if reverse and reverse.rate else 1.0
        matrix[base] = row

    if matrix:
        cache.set('active_weekly_rates', matrix, timeout=604800)
        return Response({'source': 'database', 'rates': matrix})

    return Response({'source': 'empty', 'rates': {}}, status=200)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def monthly_report(request):
    """Return a month report using the normalized EUR snapshot and Redis rate matrix."""
    month = request.query_params.get('month', date.today().strftime('%Y-%m'))
    target_currency = request.query_params.get('currency', 'EUR').upper()

    try:
        year, month_number = map(int, month.split('-'))
    except (ValueError, TypeError):
        return Response({'detail': 'month must be in YYYY-MM format.'}, status=400)

    expenses = request.user.expenses.filter(date__year=year, date__month=month_number).select_related('currency')
    total_eur = expenses.aggregate(total=Sum('amount_base_eur'))['total'] or Decimal('0.00')

    rates = cache.get('active_weekly_rates', {}).get('EUR', {})
    multiplier = Decimal(str(rates.get(target_currency, 1.0)))

    return Response({
        'report_month': month,
        'report_currency': target_currency,
        'total_amount': float((total_eur * multiplier).quantize(Decimal('0.01'))),
        'items': [
            {
                'id': item.id,
                'description': item.item_description or (item.item.description if item.item else item.category.name),
                'expense_date': item.date,
                'amount_original': float(item.amount),
                'currency_original': item.currency.code,
                'amount_converted': float((item.amount_base_eur * multiplier).quantize(Decimal('0.01'))),
            }
            for item in expenses
        ],
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def convert_currency(request):
    """Convert an amount between currencies."""
    base = request.query_params.get('base', 'EUR').upper()
    target = request.query_params.get('target', 'USD').upper()
    amount = request.query_params.get('amount')
    
    rate = CurrencyService.get_latest_rate(base, target)
    converted = None
    
    if amount is not None and rate is not None:
        try:
            converted = float(Decimal(amount) * Decimal(str(rate)))
        except (ValueError, TypeError):
            converted = None
    
    return Response({
        'base': base,
        'target': target,
        'rate': rate,
        'converted': converted
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@csrf_exempt
def export_report(request):
    """Export expense report with optional currency conversion."""
    import json
    from rest_framework.authtoken.models import Token
    from accounts.models import User
    
    if request.method != 'POST':
        return HttpResponse(
            json.dumps({'detail': 'Method not allowed'}),
            content_type='application/json',
            status=405
        )
    
    # Prefer Django/DRF-authenticated requests, then support direct Token headers.
    user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token_key = None
    if auth_header.startswith('Token '):
        token_key = auth_header[6:]  # Remove 'Token ' prefix
    
    if user is None and token_key:
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
            if not user.is_active:
                return HttpResponse(
                    json.dumps({'detail': 'User inactive or deleted.'}),
                    content_type='application/json',
                    status=401
                )
        except Token.DoesNotExist:
            return HttpResponse(
                json.dumps({'detail': 'Invalid token.'}),
                content_type='application/json',
                status=401
            )
    elif user is None:
        return HttpResponse(
            json.dumps({'detail': 'Authentication credentials were not provided.'}),
            content_type='application/json',
            status=401
        )
    
    if hasattr(request, 'data') and request.data:
        data = request.data
    else:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, AttributeError):
            return HttpResponse(
                json.dumps({'detail': 'Invalid JSON in request body'}),
                content_type='application/json',
                status=400
            )
    
    period = data.get('period', 'monthly')
    year = int(data.get('year', date.today().year))
    month = int(data.get('month', date.today().month)) if data.get('month') else date.today().month
    target_currency = data.get('target_currency', 'EUR').upper()
    export_format = request.GET.get('format', 'json').lower()

    report_service = ReportService(user)

    start_year = int(data.get('start_year', year))
    end_year = int(data.get('end_year', year))

    if period == 'monthly':
        if export_format == 'csv':
            csv_content = report_service.export_monthly_report_csv(year, month, target_currency)
            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="expense_report_{year}_{month:02d}.csv"'
            return response
        if export_format == 'pdf':
            pdf_content = report_service.export_monthly_report_pdf(year, month, target_currency)
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="expense_report_{year}_{month:02d}.pdf"'
            return response
        report = report_service.generate_monthly_report(year, month, target_currency)
    elif period == 'yearly':
        if export_format == 'csv':
            csv_content = report_service.export_yearly_report_csv(year, target_currency)
            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="expense_report_{year}.csv"'
            return response
        if export_format == 'pdf':
            pdf_content = report_service.export_yearly_report_pdf(year, target_currency)
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="expense_report_{year}.pdf"'
            return response
        report = report_service.generate_yearly_report(year, target_currency)
    elif period == 'custom_dates':
        start_date_value = data.get('date_start') or data.get('start_date')
        end_date_value = data.get('date_end') or data.get('end_date')
        if not start_date_value or not end_date_value:
            return HttpResponse(
                json.dumps({'detail': 'date_start and date_end are required for custom_dates.'}),
                content_type='application/json',
                status=400
            )
        try:
            start_date = date.fromisoformat(start_date_value)
            end_date = date.fromisoformat(end_date_value)
        except ValueError:
            return HttpResponse(
                json.dumps({'detail': 'date_start and date_end must use YYYY-MM-DD.'}),
                content_type='application/json',
                status=400
            )
        if start_date > end_date:
            return HttpResponse(
                json.dumps({'detail': 'date_start must be on or before date_end.'}),
                content_type='application/json',
                status=400
            )

        if export_format == 'csv':
            csv_content = report_service.export_custom_date_report_csv(start_date, end_date, target_currency)
            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="expense_report_{start_date}_{end_date}.csv"'
            return response
        if export_format == 'pdf':
            pdf_content = report_service.export_custom_date_report_pdf(start_date, end_date, target_currency)
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="expense_report_{start_date}_{end_date}.pdf"'
            return response
        report = report_service.generate_custom_date_report(start_date, end_date, target_currency)
    else:
        if export_format == 'csv':
            csv_content = report_service.export_year_range_report_csv(start_year, end_year, target_currency)
            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="expense_report_{start_year}_{end_year}.csv"'
            return response
        if export_format == 'pdf':
            pdf_content = report_service.export_year_range_report_pdf(start_year, end_year, target_currency)
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="expense_report_{start_year}_{end_year}.pdf"'
            return response
        report = report_service.generate_year_range_report(start_year, end_year, target_currency)

    return HttpResponse(json.dumps(report), content_type='application/json')

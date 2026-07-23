from datetime import date
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.http import HttpResponse

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


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (obj.user == request.user or request.user.is_staff)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class SubCategoryViewSet(viewsets.ModelViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.select_related('category', 'subcategory').all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]


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
        """Get expenses for current user (or all if admin)."""
        user = self.request.user
        if user.is_staff:
            return ExpenseEntry.objects.all().select_related(
                'category', 'item', 'currency', 'subcategory'
            )
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

    @action(detail=False, methods=['get'], url_path='chart')
    def chart(self, request):
        """Get chart data with category breakdown."""
        expense_service = ExpenseService(request.user)
        expensive = expense_service.get_top_expensive_categories(limit=5)
        least = expense_service.get_least_expensive_categories(limit=3)
        
        return Response({
            'expensive': expensive,
            'least': least
        })

    @action(detail=False, methods=['get'], url_path='prediction')
    def prediction(self, request):
        """Get predicted expenses for next month."""
        predictor = ExpensePredictor(request.user)
        return Response(predictor.predict_next_month())

    @action(detail=False, methods=['get'], url_path='insights')
    def insights(self, request):
        """Get insights including anomaly detection."""
        anomalies = detect_anomalies(request.user)
        return Response({'anomalies': anomalies})


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
            from decimal import Decimal
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
def export_report(request):
    """Export expense report with optional currency conversion."""
    period = request.data.get('period', 'monthly')
    year = int(request.data.get('year', date.today().year))
    month = int(request.data.get('month', date.today().month)) if request.data.get('month') else date.today().month
    target_currency = request.data.get('target_currency', 'EUR').upper()
    export_format = request.query_params.get('format', 'json').lower()

    report_service = ReportService(request.user)

    start_year = int(request.data.get('start_year', year))
    end_year = int(request.data.get('end_year', year))

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

    return Response(report)

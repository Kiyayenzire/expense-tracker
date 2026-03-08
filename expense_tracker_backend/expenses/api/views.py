

# expenses/api/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from collections import defaultdict
from decimal import Decimal
import csv
import os

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from django.conf import settings

from ..models import Expense, Category, SubCategory, ExchangeRate
from ..serializers import ExpenseSerializer, CategorySerializer, SubCategorySerializer, ExchangeRateSerializer
from ..pagination import CustomLimitOffsetPagination

# ------------------------------
# Test Connection
# ------------------------------
@api_view(['GET'])
def test_connection(request):
    return Response({"status": "connected"})

# ------------------------------
# Category ViewSet
# ------------------------------
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).prefetch_related("subcategories")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# ------------------------------
# SubCategory ViewSet
# ------------------------------
class SubCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = SubCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["category"]

    def get_queryset(self):
        return SubCategory.objects.filter(category__user=self.request.user).select_related("category")

    def perform_create(self, serializer):
        category = serializer.validated_data["category"]
        if category.user != self.request.user:
            raise permissions.PermissionDenied("Not allowed.")
        serializer.save()

# ------------------------------
# ExchangeRate ViewSet
# ------------------------------
class ExchangeRateViewSet(viewsets.ModelViewSet):
    serializer_class = ExchangeRateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExchangeRate.objects.all().order_by('currency_from', 'currency_to')

# ------------------------------
# Expense ViewSet
# ------------------------------
class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ["supplier", "currency", "category", "subcategory"]
    search_fields = ["item", "supplier"]
    ordering_fields = ["date", "amount"]

    def get_queryset(self):
        queryset = Expense.objects.filter(user=self.request.user).select_related("category", "subcategory")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        return queryset.order_by("-date")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        target_currency = self.request.query_params.get("target_currency")
        if target_currency:
            context['target_currency'] = target_currency
        return context

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # ------------------------------
    # CSV Export
    # ------------------------------
    def list(self, request, *args, **kwargs):
        if request.query_params.get("export") == "csv":
            return self.export_csv(request)
        if request.query_params.get("export") == "pdf":
            return self.export_pdf(request)
        return super().list(request, *args, **kwargs)

    def export_csv(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        target_currency = request.query_params.get("target_currency")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=expenses.csv"
        writer = csv.writer(response)
        writer.writerow(["Date","Category","SubCategory","Item","Quantity","Supplier","Country","Amount","Currency"])
        for expense in queryset:
            amount = expense.amount
            if target_currency and target_currency != expense.currency:
                try:
                    rate_obj = ExchangeRate.objects.get(currency_from=expense.currency, currency_to=target_currency)
                    amount = round(amount * rate_obj.rate, 2)
                except ExchangeRate.DoesNotExist:
                    pass
            writer.writerow([
                expense.date,
                expense.category.name if expense.category else "",
                expense.subcategory.name if expense.subcategory else "",
                expense.item,
                expense.quantity,
                expense.supplier,
                expense.country,
                amount,
                target_currency or expense.currency
            ])
        return response

    # ------------------------------
    # PDF Export
    # ------------------------------
    def export_pdf(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        target_currency = request.query_params.get("target_currency")
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=expenses_report.pdf"
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        logo_path = os.path.join(settings.BASE_DIR, "expenses/static/expenses/logo.png")
        if os.path.exists(logo_path):
            elements.append(Image(logo_path, width=100, height=50))
        else:
            elements.append(Paragraph("Company Logo", styles["Title"]))
        elements.append(Paragraph("<b>Expenses Report</b>", styles["Title"]))
        elements.append(Spacer(1, 12))
        grouped = defaultdict(list)
        for exp in queryset:
            grouped[exp.category.name if exp.category else "Uncategorized"].append(exp)
        for category_name, expenses in grouped.items():
            elements.append(Paragraph(f"<b>Category: {category_name}</b>", styles["Heading2"]))
            data = [["Date","Item","Qty","Supplier","Country","Amount","Currency"]]
            for exp in expenses:
                amount = exp.amount
                if target_currency and target_currency != exp.currency:
                    try:
                        rate_obj = ExchangeRate.objects.get(currency_from=exp.currency, currency_to=target_currency)
                        amount = round(amount * rate_obj.rate, 2)
                    except ExchangeRate.DoesNotExist:
                        pass
                data.append([
                    exp.date.strftime("%Y-%m-%d"),
                    exp.item,
                    exp.quantity,
                    exp.supplier,
                    exp.country,
                    amount,
                    target_currency or exp.currency
                ])
            table = Table(data, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.grey),
                ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
                ("GRID", (0,0), (-1,-1), 0.5, colors.black)
            ]))
            elements.append(table)
            elements.append(PageBreak())
        doc.build(elements)
        return response



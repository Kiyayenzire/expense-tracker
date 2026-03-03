from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.conf import settings
from django.templatetags.static import static
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from collections import defaultdict
import os
from .models import Expense, Category
from .serializers import ExpenseSerializer, CategorySerializer
from .pagination import CustomLimitOffsetPagination

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['supplier', 'currency', 'category']
    search_fields = ['item', 'supplier']
    ordering_fields = ['date', 'amount']

    def get_queryset(self):
        queryset = Expense.objects.filter(user=self.request.user)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        return queryset.order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        if request.query_params.get('export') == 'pdf':
            return self.export_pdf(request)
        elif request.query_params.get('export') == 'csv':
            return self.export_csv(request)
        return super().list(request, *args, **kwargs)

    def export_csv(self, request):
        import csv
        queryset = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Category', 'Item', 'Quantity', 'Supplier', 'Country', 'Amount', 'Currency'])
        for expense in queryset:
            writer.writerow([
                expense.date,
                expense.category.name if expense.category else '',
                expense.item,
                expense.quantity,
                expense.supplier,
                expense.country,
                expense.amount,
                expense.currency
            ])
        return response

    def export_pdf(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        buffer = HttpResponse(content_type='application/pdf')
        buffer['Content-Disposition'] = 'attachment; filename="expenses_report.pdf"'

        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        logo_path = os.path.join(settings.BASE_DIR, 'expenses/static/expenses/logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=100, height=50)
            elements.append(logo)
        else:
            elements.append(Paragraph("Company Logo", styles['Title']))

        elements.append(Paragraph("<b>Expenses Report</b>", styles['Title']))
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        filter_text = f"Date Range: {start_date} to {end_date}" if start_date and end_date else "All Dates"
        elements.append(Paragraph(filter_text, styles['Normal']))
        elements.append(Spacer(1, 12))

        grouped = defaultdict(list)
        for exp in queryset:
            grouped[exp.category.name if exp.category else "Uncategorized"].append(exp)

        for category_name, expenses in grouped.items():
            elements.append(Paragraph(f"<b>Category: {category_name}</b>", styles['Heading2']))
            data = [["Date", "Item", "Qty", "Supplier", "Country", "Amount", "Currency"]]
            for exp in expenses:
                data.append([
                    exp.date.strftime("%Y-%m-%d"),
                    exp.item,
                    exp.quantity,
                    exp.supplier,
                    exp.country,
                    f"{exp.amount:.2f}",
                    exp.currency
                ])
            table = Table(data, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(table)
            elements.append(PageBreak())

        doc.build(elements)
        return buffer

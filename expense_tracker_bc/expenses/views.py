from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
import csv
from io import StringIO, BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm, mm
from .models import Expense, Category
from .serializers import ExpenseSerializer, CategorySerializer
from datetime import datetime

class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = None  # No hard cap on maximum

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['category__name', 'currency']
    ordering_fields = ['date', 'amount']
    search_fields = ['item', 'supplier']

    def get_queryset(self):
        queryset = Expense.objects.filter(user=self.request.user)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
        return queryset

    @action(detail=False, methods=['get'])
    def export(self, request):
        format = request.query_params.get('format', 'csv')
        expenses = self.get_queryset()

        if format == 'pdf':
            return self.export_pdf(expenses)
        return self.export_csv(expenses)

    def export_csv(self, expenses):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Item', 'Category', 'Amount', 'Currency'])
        for exp in expenses:
            writer.writerow([
                exp.date,
                exp.item,
                exp.category.name,
                exp.amount,
                exp.currency
            ])
        return response

    def export_pdf(self, expenses):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        styles = getSampleStyleSheet()
        title = Paragraph("Expense Report", styles["Title"])
        elements.append(title)

        date_str = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"])
        elements.append(date_str)
        elements.append(Spacer(1, 12))

        data = [["Date", "Item", "Category", "Amount", "Currency"]]
        total_amount = 0

        for exp in expenses:
            data.append([
                exp.date.strftime("%Y-%m-%d"),
                exp.item,
                exp.category.name,
                f"{exp.amount:.2f}",
                exp.currency,
            ])
            total_amount += float(exp.amount)

        data.append(["", "", "Total", f"{total_amount:.2f}", ""])

        table = Table(data, repeatRows=1, colWidths=[3*cm, 5*cm, 4*cm, 3*cm, 2*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(table)

        def add_page_number(canvas, doc):
            page_num = canvas.getPageNumber()
            canvas.setFont('Helvetica', 9)
            canvas.drawRightString(200 * mm, 15 * mm, f"Page {page_num}")

        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        buffer.seek(0)
        return HttpResponse(buffer, content_type='application/pdf')

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

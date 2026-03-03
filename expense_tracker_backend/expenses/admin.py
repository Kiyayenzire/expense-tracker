from django.contrib import admin
from .models import Expense, Category
from import_export.admin import ExportMixin
from import_export import resources, fields
from import_export.widgets import DecimalWidget
from import_export.formats.base_formats import CSV
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint


# Resource for export with CSV only and customizations
class ExpenseResource(resources.ModelResource):
    amount = fields.Field(column_name="Total Amount (€)", attribute="amount", widget=DecimalWidget())

    class Meta:
        model = Expense
        exclude = ('created_at',)
        export_order = ('item', 'category', 'quantity', 'rate', 'amount', 'currency', 'supplier', 'country', 'date', 'user')

    def get_export_formats(self):
        return [CSV()]  # Enable only CSV format


# PDF export action
@admin.action(description="Export selected expenses to PDF")
def export_as_pdf(modeladmin, request, queryset):
    html_string = render_to_string("expenses/pdf_template.html", {"expenses": queryset})
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=expenses.pdf"
    weasyprint.HTML(string=html_string).write_pdf(response)
    return response


# Expense Admin with export support and PDF action
class ExpenseAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ExpenseResource
    list_display = ('item', 'category', 'quantity', 'rate', 'amount', 'currency_symbol', 'supplier', 'country', 'date', 'user')
    list_filter = ('category', 'currency', 'country', 'date')
    search_fields = ('item', 'supplier', 'country')
    actions = [export_as_pdf]
    readonly_fields = ('user',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user
        obj.save()

    def currency_symbol(self, obj):
        symbols = {
            "EUR": "€",
            "USD": "$",
            "UGX": "UGX",
        }
        return symbols.get(obj.currency, obj.currency)
    currency_symbol.short_description = "Currency"


# Register models
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Category)

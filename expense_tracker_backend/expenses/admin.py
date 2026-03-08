


# expenses/admin.py
from django.contrib import admin
from .models import Expense, Category, SubCategory, ExchangeRate
from import_export.admin import ExportMixin
from import_export import resources, fields
from import_export.widgets import DecimalWidget
from import_export.formats.base_formats import CSV
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint
from django.db.models import Sum

# -----------------------------
# Export Resource
# -----------------------------
class ExpenseResource(resources.ModelResource):
    amount = fields.Field(
        column_name="Total Amount",
        attribute="amount",
        widget=DecimalWidget()
    )
    class Meta:
        model = Expense
        exclude = ("created_at",)
        export_order = (
            "item","category","subcategory","quantity","unit","rate","amount","currency",
            "supplier","country","date","user"
        )
    def get_export_formats(self):
        return [CSV()]

# -----------------------------
# PDF Export Action
# -----------------------------
@admin.action(description="Export selected expenses to PDF")
def export_as_pdf(modeladmin, request, queryset):
    html_string = render_to_string("expenses/pdf_template.html", {"expenses": queryset})
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=expenses.pdf"
    weasyprint.HTML(string=html_string).write_pdf(response)
    return response

# -----------------------------
# Expense Admin
# -----------------------------
@admin.register(Expense)
class ExpenseAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ExpenseResource
    list_display = (
        "item","category","subcategory","quantity_unit","rate_formatted","amount_formatted","currency_symbol",
        "supplier","country","date","user",
    )
    readonly_fields = ("amount","user","summary")
    fieldsets = ((None, {"fields": ("item","category","subcategory","quantity","unit","rate","amount","currency",
                                     "supplier","country","date","user","summary")}),)
    list_filter = ("category","subcategory","currency","country","date")
    search_fields = ("item","supplier","country","category__name")
    actions = [export_as_pdf]

    change_list_template = "admin/expenses/expense_change_list.html"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category" and not request.user.is_superuser:
            kwargs["queryset"] = Category.objects.filter(user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user
        obj.save()

    def has_change_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return obj.user == request.user
        return super().has_delete_permission(request, obj)

    # Display helpers
    def currency_symbol(self, obj):
        symbols = {"EUR":"€","USD":"$","UGX":"UGX"}
        return symbols.get(obj.currency, obj.currency)
    currency_symbol.short_description = "Currency"

    def quantity_unit(self, obj):
        return f"{obj.quantity} {obj.unit}"
    quantity_unit.short_description = "Quantity"

    def amount_formatted(self, obj):
        return f"{obj.amount:,.2f}"
    amount_formatted.short_description = "Amount"

    def rate_formatted(self, obj):
        return f"{obj.rate:,.2f}"
    rate_formatted.short_description = "Rate"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        qs = self.get_queryset(request)
        totals = qs.values("currency").annotate(total_amount=Sum("amount")).order_by()
        extra_context["totals"] = totals
        return super().changelist_view(request, extra_context=extra_context)

# -----------------------------
# Category Admin
# -----------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name","user","description")
    search_fields = ("name",)
    list_filter = ("user",)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user
        obj.save()

# -----------------------------
# SubCategory Admin
# -----------------------------
@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name","category")
    search_fields = ("name",)
    list_filter = ("category",)

# -----------------------------
# ExchangeRate Admin
# -----------------------------
@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("currency_from","currency_to","rate","updated_at")
    search_fields = ("currency_from","currency_to")





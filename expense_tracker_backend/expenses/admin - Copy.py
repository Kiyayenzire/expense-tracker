from django.contrib import admin
from .models import Expense, Category


class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'item', 'category', 'quantity', 'rate', 'amount',
        'currency', 'supplier', 'country', 'date', 'user', 'summary'
    )
    readonly_fields = ('amount', 'user', 'summary')
    fieldsets = (
        (None, {
            'fields': (
                'item', 'category', 'quantity', 'rate', 'amount', 'currency',
                'supplier', 'country', 'date', 'user', 'summary'
            )
        }),
    )
    list_filter = ('category', 'currency', 'country', 'date')
    search_fields = ('item', 'supplier', 'country', 'category__name')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category' and not request.user.is_superuser:
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


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'description')
    search_fields = ('name',)
    list_filter = ('user',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.user = request.user
        obj.save()


admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Category, CategoryAdmin)

from datetime import timedelta

from django import forms
from django.contrib import admin
from .models import Category, SubCategory, Item, Currency, CurrencyRate, ExpenseEntry
from django.core.exceptions import ValidationError
from django.utils import timezone

admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Item)
admin.site.register(Currency)
@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
	list_display = ('base_currency', 'target_currency', 'rate', 'effective_date')
	list_filter = ('base_currency', 'target_currency', 'effective_date')
	ordering = ('-effective_date', 'base_currency', 'target_currency')

	def get_form(self, request, obj=None, **kwargs):
		class WeeklyCurrencyRateForm(forms.ModelForm):
			class Meta:
				model = CurrencyRate
				fields = '__all__'

			def clean(self):
				cleaned_data = super().clean()
				base = cleaned_data.get('base_currency')
				target = cleaned_data.get('target_currency')
				effective_date = cleaned_data.get('effective_date')
				today = timezone.localdate()
				week_start = today - timedelta(days=today.weekday())
				window_end = week_start + timedelta(days=4)

				if base and base.code != 'EUR' or target and target.code != 'UGX':
					raise ValidationError('The manual weekly rate must be EUR to UGX.')
				if today.weekday() > 4:
					raise ValidationError('Weekly EUR to UGX rates are locked after Friday. Update again next Monday.')
				if CurrencyRate.objects.filter(
					base_currency__code='EUR',
					target_currency__code='UGX',
					effective_date__gte=week_start,
					effective_date__lte=window_end,
					is_manual=True,
				).exists():
					raise ValidationError('A manual EUR to UGX rate was already recorded this week. Editing is locked until next Monday.')
				if effective_date and not (week_start <= effective_date <= window_end):
					raise ValidationError('The effective date must be a day from this Monday through Friday.')
				return cleaned_data

		return WeeklyCurrencyRateForm

	def save_model(self, request, obj, form, change):
		obj.is_manual = True
		super().save_model(request, obj, form, change)

admin.site.register(ExpenseEntry)

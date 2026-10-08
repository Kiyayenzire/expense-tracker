from decimal import Decimal

from django import forms
from django.contrib import admin
from .models import Category, SubCategory, Item, Currency, CurrencyRate, ExpenseEntry
from django.core.exceptions import ValidationError
from django.db import transaction
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

			def __init__(self, *args, **form_kwargs):
				super().__init__(*args, **form_kwargs)
				self.initial.setdefault('effective_date', timezone.localdate())
				self.initial['is_manual'] = True
				self.fields['is_manual'].initial = True
				self.fields['is_manual'].disabled = True

			def clean(self):
				cleaned_data = super().clean()
				base = cleaned_data.get('base_currency')
				target = cleaned_data.get('target_currency')
				effective_date = cleaned_data.get('effective_date')
				today = timezone.localdate()
				allowed_pairs = {('EUR', 'UGX'), ('USD', 'UGX'), ('UGX', 'EUR'), ('UGX', 'USD')}

				if base and target:
					pair = (base.code, target.code)
					if pair not in allowed_pairs:
						raise ValidationError('Manual weekly rates are only allowed for EUR/UGX, USD/UGX, UGX/EUR, and UGX/USD.')

				rate = cleaned_data.get('rate')
				if rate is not None and rate <= 0:
					raise ValidationError('Exchange rates must be greater than zero.')
				if rate is not None:
					reciprocal_rate = (Decimal('1') / rate).quantize(Decimal('0.0000000000001'))
					if reciprocal_rate > Decimal('99999.99999999999'):
						raise ValidationError('The reciprocal rate exceeds the supported precision.')

				if effective_date and effective_date > today:
					raise ValidationError('The effective date cannot be in the future.')

				if base and target and effective_date:
					existing_manual_rates = CurrencyRate.objects.filter(
						base_currency=base,
						target_currency=target,
						effective_date=effective_date,
						is_manual=True,
					)
					if obj and obj.pk:
						existing_manual_rates = existing_manual_rates.exclude(pk=obj.pk)
					if existing_manual_rates.exists():
						raise ValidationError('A manual rate for this pair and effective date already exists.')
				return cleaned_data

		return WeeklyCurrencyRateForm

	@transaction.atomic
	def save_model(self, request, obj, form, change):
		obj.save_as_manual()

admin.site.register(ExpenseEntry)

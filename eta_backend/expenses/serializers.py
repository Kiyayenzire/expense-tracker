from rest_framework import serializers
from .models import Category, SubCategory, Item, Currency, ExpenseEntry, CurrencyRate


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'color', 'is_active']


class SubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category', 'category_name']


class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)

    class Meta:
        model = Item
        fields = ['id', 'description', 'category', 'category_name', 'subcategory', 'subcategory_name']


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id', 'code', 'name', 'symbol', 'is_active']


class CurrencyRateSerializer(serializers.ModelSerializer):
    base_currency_code = serializers.CharField(source='base_currency.code', read_only=True)
    target_currency_code = serializers.CharField(source='target_currency.code', read_only=True)

    class Meta:
        model = CurrencyRate
        fields = ['id', 'base_currency', 'base_currency_code', 'target_currency', 'target_currency_code', 'rate', 'effective_date', 'created_at']


class ExpenseEntrySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    item_description = serializers.CharField(source='item.description', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)

    class Meta:
        model = ExpenseEntry
        fields = [
            'id',
            'user',
            'date',
            'category',
            'category_name',
            'item',
            'item_description',
            'subcategory',
            'subcategory_name',
            'quantity',
            'supplier',
            'country',
            'amount',
            'currency',
            'currency_code',
            'user_local_time',
            'user_timezone',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

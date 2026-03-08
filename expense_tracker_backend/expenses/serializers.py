

# expenses/serializers.py
from rest_framework import serializers
from .models import Expense, Category, SubCategory, ExchangeRate

# ------------------------------
# SubCategory Serializer
# ------------------------------
class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'category', 'name']

# ------------------------------
# Category Serializer
# ------------------------------
class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'user', 'name', 'description', 'subcategories']
        read_only_fields = ['user']

# ------------------------------
# Expense Serializer
# ------------------------------
class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    subcategory_name = serializers.CharField(source="subcategory.name", read_only=True)
    converted_amount = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = [
            'id', 'user', 'category', 'category_name', 'subcategory', 'subcategory_name',
            'item', 'quantity', 'rate', 'supplier', 'country', 'amount', 'converted_amount',
            'currency', 'date', 'created_at',
        ]
        read_only_fields = ['user', 'amount', 'created_at']

    def get_converted_amount(self, obj):
        target_currency = self.context.get('target_currency')
        if target_currency and target_currency != obj.currency:
            try:
                rate_obj = ExchangeRate.objects.get(currency_from=obj.currency, currency_to=target_currency)
                return round(obj.amount * rate_obj.rate, 2)
            except ExchangeRate.DoesNotExist:
                return None
        return obj.amount

    # Validation
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value

    def validate_rate(self, value):
        if value < 0:
            raise serializers.ValidationError("Rate cannot be negative.")
        return value

    def validate(self, data):
        request = self.context.get("request")
        user = request.user
        category = data.get("category")
        subcategory = data.get("subcategory")
        if category and category.user != user:
            raise serializers.ValidationError("Selected category does not belong to the user.")
        if subcategory:
            if subcategory.category != category:
                raise serializers.ValidationError("Selected subcategory does not belong to the chosen category.")
            if subcategory.category.user != user:
                raise serializers.ValidationError("Selected subcategory does not belong to the user.")
        return data

# ------------------------------
# ExchangeRate Serializer
# ------------------------------
class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = ['id', 'currency_from', 'currency_to', 'rate', 'updated_at']
        read_only_fields = ['updated_at']




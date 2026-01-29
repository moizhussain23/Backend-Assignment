from django.contrib import admin
from .models import Customer, Loan


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'first_name', 'last_name', 'phone_number', 'monthly_salary', 'approved_limit', 'current_debt']
    search_fields = ['first_name', 'last_name', 'phone_number']
    list_filter = ['created_at']
    readonly_fields = ['customer_id', 'created_at', 'updated_at']


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['loan_id', 'customer', 'loan_amount', 'interest_rate', 'tenure', 'start_date', 'end_date', 'is_active']
    search_fields = ['customer__first_name', 'customer__last_name', 'loan_id']
    list_filter = ['start_date', 'end_date', 'interest_rate']
    readonly_fields = ['loan_id', 'created_at', 'updated_at']
    
    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True

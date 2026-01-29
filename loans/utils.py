from decimal import Decimal
from datetime import datetime, date
from .models import Customer, Loan
import math


def calculate_credit_score(customer_id):
    """
    Calculate credit score for a customer based on historical loan data.
    Score is out of 100.
    """
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return 0
    
    # Check if sum of current loans > approved limit
    current_loans_sum = sum(float(loan.loan_amount) for loan in customer.loans.filter(end_date__gte=date.today()))
    if current_loans_sum > float(customer.approved_limit):
        return 0
    
    loans = customer.loans.all()
    if not loans:
        return 50  # Default score for new customers
    
    score = 0
    
    # Component 1: Past Loans paid on time (0-35 points)
    total_emis = sum(loan.tenure for loan in loans)
    emis_paid_on_time = sum(loan.emis_paid_on_time for loan in loans)
    if total_emis > 0:
        on_time_ratio = float(emis_paid_on_time) / float(total_emis)
        score += min(35, on_time_ratio * 35)
    
    # Component 2: Number of loans taken in past (0-15 points)
    # More loans = lower score (reverse scoring)
    num_loans = loans.count()
    if num_loans <= 2:
        score += 15
    elif num_loans <= 5:
        score += 10
    elif num_loans <= 10:
        score += 5
    else:
        score += 0
    
    # Component 3: Loan activity in current year (0-15 points)
    current_year = datetime.now().year
    current_year_loans = loans.filter(start_date__year=current_year)
    if current_year_loans.count() <= 2:
        score += 15
    elif current_year_loans.count() <= 4:
        score += 10
    elif current_year_loans.count() <= 6:
        score += 5
    else:
        score += 0
    
    # Component 4: Loan approved volume (0-35 points)
    total_loan_volume = sum(float(loan.loan_amount) for loan in loans)
    if customer.approved_limit > 0:
        volume_ratio = min(1, total_loan_volume / float(customer.approved_limit))
        # Lower volume ratio = higher score
        score += max(0, 35 - (volume_ratio * 35))
    
    return min(100, max(0, score))


def calculate_monthly_installment(principal, annual_interest_rate, tenure_months):
    """
    Calculate monthly installment using compound interest formula.
    EMI = P × r × (1 + r)^n / ((1 + r)^n - 1)
    """
    principal = Decimal(str(principal))
    annual_rate = Decimal(str(annual_interest_rate))
    tenure = Decimal(str(tenure_months))
    
    if annual_rate == 0:
        return principal / tenure
    
    monthly_rate = annual_rate / Decimal('1200')  # Convert annual % to monthly decimal
    
    # Calculate EMI using compound interest formula
    numerator = principal * monthly_rate * (Decimal('1') + monthly_rate) ** tenure
    denominator = (Decimal('1') + monthly_rate) ** tenure - Decimal('1')
    
    if denominator == 0:
        return principal / tenure
    
    emi = numerator / denominator
    return round(emi, 2)


def get_corrected_interest_rate(credit_score, requested_rate):
    """
    Get corrected interest rate based on credit score.
    """
    if credit_score > 50:
        return max(requested_rate, 8.0)  # Minimum 8% for good credit
    elif credit_score > 30:
        return max(requested_rate, 12.0)  # Minimum 12% for fair credit
    elif credit_score > 10:
        return max(requested_rate, 16.0)  # Minimum 16% for poor credit
    else:
        return requested_rate  # Loan will be rejected anyway


def check_loan_eligibility(customer_id, loan_amount, interest_rate, tenure):
    """
    Check if loan should be approved based on credit score and other criteria.
    Returns tuple: (approved, corrected_interest_rate, monthly_installment, message)
    """
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return False, interest_rate, 0, "Customer not found"
    
    credit_score = calculate_credit_score(customer_id)
    corrected_rate = get_corrected_interest_rate(credit_score, interest_rate)
    monthly_installment = calculate_monthly_installment(loan_amount, corrected_rate, tenure)
    
    # Check credit score criteria
    if credit_score <= 10:
        return False, corrected_rate, monthly_installment, "Credit score too low"
    
    # Check EMI vs salary ratio
    current_emis = sum(float(loan.monthly_repayment) for loan in customer.loans.filter(end_date__gte=date.today()))
    total_emis = current_emis + float(monthly_installment)
    
    if total_emis > (float(customer.monthly_salary) * 0.5):
        return False, corrected_rate, monthly_installment, "EMIs exceed 50% of monthly salary"
    
    # Check if loan amount exceeds reasonable limit
    if loan_amount > customer.approved_limit:
        return False, corrected_rate, monthly_installment, "Loan amount exceeds approved limit"
    
    return True, corrected_rate, monthly_installment, "Loan approved"
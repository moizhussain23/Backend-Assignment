from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from datetime import date
from .models import Customer, Loan
from .serializers import (
    CustomerRegistrationSerializer, 
    CustomerRegistrationResponseSerializer,
    LoanEligibilitySerializer,
    LoanEligibilityResponseSerializer,
    LoanCreateSerializer,
    LoanCreateResponseSerializer,
    LoanDetailSerializer,
    CustomerLoanListSerializer
)
from .utils import check_loan_eligibility, calculate_monthly_installment
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
def register_customer(request):
    """
    Register a new customer with approved limit based on salary.
    Formula: approved_limit = 36 * monthly_salary (rounded to nearest lakh)
    """
    serializer = CustomerRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            customer = serializer.save()
            response_serializer = CustomerRegistrationResponseSerializer(customer)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            return Response(
                {'error': 'Failed to create customer'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def check_eligibility(request):
    """
    Check loan eligibility based on credit score and other criteria.
    """
    serializer = LoanEligibilitySerializer(data=request.data)
    
    if serializer.is_valid():
        customer_id = serializer.validated_data['customer_id']
        loan_amount = serializer.validated_data['loan_amount']
        interest_rate = serializer.validated_data['interest_rate']
        tenure = serializer.validated_data['tenure']
        
        try:
            # Check eligibility (this function will handle customer existence)
            approved, corrected_rate, monthly_installment, message = check_loan_eligibility(
                customer_id, loan_amount, interest_rate, tenure
            )
            
            # Handle customer not found case
            if not approved and message == "Customer not found":
                return Response(
                    {'error': 'Customer not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            response_data = {
                'customer_id': customer_id,
                'approval': approved,
                'interest_rate': interest_rate,
                'corrected_interest_rate': corrected_rate,
                'tenure': tenure,
                'monthly_installment': monthly_installment
            }
            
            response_serializer = LoanEligibilityResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error checking eligibility: {str(e)}")
            return Response(
                {'error': 'Failed to check eligibility'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_loan(request):
    """
    Process a new loan based on eligibility.
    """
    serializer = LoanCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        customer_id = serializer.validated_data['customer_id']
        loan_amount = serializer.validated_data['loan_amount']
        interest_rate = serializer.validated_data['interest_rate']
        tenure = serializer.validated_data['tenure']
        
        try:
            customer = get_object_or_404(Customer, customer_id=customer_id)
            
            # Check eligibility first
            approved, corrected_rate, monthly_installment, message = check_loan_eligibility(
                customer_id, loan_amount, interest_rate, tenure
            )
            
            if approved:
                # Create the loan
                from dateutil.relativedelta import relativedelta
                from datetime import date
                
                start_date = date.today()
                end_date = start_date + relativedelta(months=tenure)
                
                # Use corrected interest rate for EMI calculation
                final_monthly_installment = calculate_monthly_installment(
                    loan_amount, corrected_rate, tenure
                )
                
                loan = Loan.objects.create(
                    customer=customer,
                    loan_amount=loan_amount,
                    interest_rate=corrected_rate,
                    monthly_repayment=final_monthly_installment,
                    tenure=tenure,
                    start_date=start_date,
                    end_date=end_date,
                    emis_paid_on_time=0
                )
                
                # Update customer's current debt
                customer.current_debt += loan_amount
                customer.save()
                
                response_data = {
                    'loan_id': loan.loan_id,
                    'customer_id': customer_id,
                    'loan_approved': True,
                    'message': 'Loan approved successfully',
                    'monthly_installment': final_monthly_installment
                }
            else:
                response_data = {
                    'loan_id': None,
                    'customer_id': customer_id,
                    'loan_approved': False,
                    'message': message,
                    'monthly_installment': monthly_installment
                }
            
            response_serializer = LoanCreateResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error creating loan: {str(e)}")
            return Response(
                {'error': 'Failed to process loan'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def view_loan(request, loan_id):
    """
    View loan details and customer details by loan ID.
    """
    try:
        loan = Loan.objects.get(loan_id=loan_id)
        serializer = LoanDetailSerializer(loan)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Loan.DoesNotExist:
        return Response(
            {'error': 'Loan not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error fetching loan details: {str(e)}")
        return Response(
            {'error': 'Failed to fetch loan details'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def view_customer_loans(request, customer_id):
    """
    View all current loan details by customer ID.
    """
    try:
        customer = Customer.objects.get(customer_id=customer_id)
        
        # Get current/active loans
        current_loans = customer.loans.filter(end_date__gte=date.today())
        
        serializer = CustomerLoanListSerializer(current_loans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error fetching customer loans: {str(e)}")
        return Response(
            {'error': 'Failed to fetch customer loans'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

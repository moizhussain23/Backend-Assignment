from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta
import json
from unittest.mock import patch, MagicMock

from .models import Customer, Loan
from .utils import calculate_credit_score, check_loan_eligibility
from .tasks import ingest_customer_data, ingest_loan_data


class CustomerModelTest(TestCase):
    """Test cases for Customer model"""
    
    def setUp(self):
        """Set up test data"""
        self.customer_data = {
            'customer_id': 1,
            'first_name': 'John',
            'last_name': 'Doe',
            'age': 30,
            'phone_number': 1234567890,
            'monthly_salary': Decimal('50000.00'),
            'approved_limit': Decimal('1800000.00'),
        }
        self.customer = Customer.objects.create(**self.customer_data)
    
    def test_customer_creation(self):
        """Test customer model creation"""
        self.assertEqual(self.customer.first_name, 'John')
        self.assertEqual(self.customer.last_name, 'Doe')
        self.assertEqual(self.customer.age, 30)
        self.assertEqual(self.customer.phone_number, 1234567890)
        self.assertEqual(self.customer.monthly_salary, Decimal('50000.00'))
        self.assertEqual(self.customer.approved_limit, Decimal('1800000.00'))
    
    def test_customer_str_method(self):
        """Test customer string representation"""
        expected_str = f"{self.customer.first_name} {self.customer.last_name} (ID: {self.customer.customer_id})"
        self.assertEqual(str(self.customer), expected_str)
    
    def test_approved_limit_calculation(self):
        """Test approved limit is correctly calculated (36 * monthly_salary)"""
        expected_limit = self.customer.monthly_salary * 36
        self.assertEqual(self.customer.approved_limit, expected_limit)
    
    def test_customer_unique_phone(self):
        """Test that phone number must be unique"""
        with self.assertRaises(Exception):
            Customer.objects.create(
                customer_id=2,
                first_name='Jane',
                last_name='Smith',
                age=25,
                phone_number=1234567890,  # Same phone number
                monthly_salary=Decimal('40000.00'),
                approved_limit=Decimal('1440000.00')
            )


class LoanModelTest(TestCase):
    """Test cases for Loan model"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = Customer.objects.create(
            customer_id=1,
            first_name='John',
            last_name='Doe',
            age=30,
            phone_number=1234567890,
            monthly_salary=Decimal('50000.00'),
            approved_limit=Decimal('1800000.00')
        )
        
        self.loan_data = {
            'customer': self.customer,
            'loan_id': 1001,
            'loan_amount': Decimal('100000.00'),
            'tenure': 12,
            'interest_rate': Decimal('10.00'),
            'monthly_repayment': Decimal('8792.59'),
            'emis_paid_on_time': 10,
            'start_date': date.today() - timedelta(days=60),
            'end_date': date.today() + timedelta(days=300)
        }
        self.loan = Loan.objects.create(**self.loan_data)
    
    def test_loan_creation(self):
        """Test loan model creation"""
        self.assertEqual(self.loan.customer, self.customer)
        self.assertEqual(self.loan.loan_amount, Decimal('100000.00'))
        self.assertEqual(self.loan.tenure, 12)
        self.assertEqual(self.loan.interest_rate, Decimal('10.00'))
        self.assertEqual(self.loan.emis_paid_on_time, 10)
    
    def test_loan_str_method(self):
        """Test loan string representation"""
        expected_str = f"Loan {self.loan.loan_id} - {self.customer.first_name} {self.customer.last_name}"
        self.assertEqual(str(self.loan), expected_str)
    
    def test_loan_customer_relationship(self):
        """Test loan-customer foreign key relationship"""
        self.assertEqual(self.loan.customer.first_name, 'John')
        self.assertEqual(self.customer.loans.first(), self.loan)
    
    def test_loan_repayment_calculation(self):
        """Test monthly repayment calculation logic"""
        # This would test EMI calculation formula
        self.assertGreater(self.loan.monthly_repayment, 0)
        self.assertIsInstance(self.loan.monthly_repayment, Decimal)


class UtilityFunctionsTest(TestCase):
    """Test cases for utility functions"""
    
    def setUp(self):
        """Set up test data"""
        self.customer = Customer.objects.create(
            customer_id=1,
            first_name='John',
            last_name='Doe',
            age=30,
            phone_number=1234567890,
            monthly_salary=Decimal('50000.00'),
            approved_limit=Decimal('1800000.00')
        )
        
        # Create some loans for credit score calculation
        Loan.objects.create(
            customer=self.customer,
            loan_id=1001,
            loan_amount=Decimal('100000.00'),
            tenure=12,
            interest_rate=Decimal('10.00'),
            monthly_repayment=Decimal('8792.59'),
            emis_paid_on_time=12,  # All EMIs paid on time
            start_date=date.today() - timedelta(days=365),
            end_date=date.today() - timedelta(days=30)
        )
    
    def test_credit_score_calculation_high_score(self):
        """Test credit score calculation for good customer"""
        score = calculate_credit_score(self.customer.customer_id)
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_credit_score_with_no_loans(self):
        """Test credit score for customer with no loan history"""
        new_customer = Customer.objects.create(
            customer_id=2,
            first_name='Jane',
            last_name='Smith',
            age=25,
            phone_number=9876543210,
            monthly_salary=Decimal('40000.00'),
            approved_limit=Decimal('1440000.00')
        )
        score = calculate_credit_score(new_customer.customer_id)
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)
    
    def test_loan_eligibility_approved(self):
        """Test loan eligibility for qualified customer"""
        approved, rate, monthly_payment, message = check_loan_eligibility(
            self.customer.customer_id, Decimal('100000.00'), Decimal('10.00'), 12
        )
        self.assertIsInstance(approved, bool)
        self.assertIsInstance(rate, Decimal)
        self.assertIsInstance(monthly_payment, Decimal)
        self.assertIsInstance(message, str)
    
    def test_loan_eligibility_high_emi_ratio(self):
        """Test loan eligibility rejection due to high EMI ratio"""
        # Create a loan that would exceed 50% of salary
        approved, rate, monthly_payment, message = check_loan_eligibility(
            self.customer.customer_id, Decimal('1000000.00'), Decimal('15.00'), 12
        )
        self.assertFalse(approved)
        self.assertIn("50%", message)
    
    def test_loan_eligibility_exceeds_limit(self):
        """Test loan eligibility when amount exceeds approved limit"""
        approved, rate, monthly_payment, message = check_loan_eligibility(
            self.customer.customer_id, Decimal('2000000.00'), Decimal('10.00'), 12
        )
        self.assertFalse(approved)


class APIEndpointTest(TestCase):
    """Test cases for API endpoints"""
    
    def setUp(self):
        """Set up test data and client"""
        self.client = Client()
        self.customer = Customer.objects.create(
            customer_id=1,
            first_name='John',
            last_name='Doe',
            age=30,
            phone_number=1234567890,
            monthly_salary=Decimal('50000.00'),
            approved_limit=Decimal('1800000.00')
        )
        
        self.loan = Loan.objects.create(
            customer=self.customer,
            loan_id=1001,
            loan_amount=Decimal('100000.00'),
            tenure=12,
            interest_rate=Decimal('10.00'),
            monthly_repayment=Decimal('8792.59'),
            emis_paid_on_time=10,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=300)
        )
    
    def test_customer_registration_success(self):
        """Test successful customer registration"""
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'age': 25,
            'phone_number': 9876543210,
            'monthly_income': 40000
        }
        response = self.client.post(
            reverse('register_customer'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertIn('customer_id', response_data)
        self.assertEqual(response_data['name'], 'Jane Smith')
    
    def test_customer_registration_duplicate_phone(self):
        """Test customer registration with duplicate phone number"""
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'age': 25,
            'phone_number': 1234567890,  # Same as existing customer
            'monthly_income': 40000
        }
        response = self.client.post(
            reverse('register_customer'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_customer_registration_invalid_data(self):
        """Test customer registration with invalid data"""
        data = {
            'first_name': 'Jane',
            # Missing required fields
            'age': 25,
            'monthly_income': 40000
        }
        response = self.client.post(
            reverse('register_customer'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_check_eligibility_success(self):
        """Test successful loan eligibility check"""
        data = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 50000,
            'interest_rate': 10,
            'tenure': 12
        }
        response = self.client.post(
            reverse('check_eligibility'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('approval', response_data)
        self.assertIn('monthly_installment', response_data)
    
    def test_check_eligibility_nonexistent_customer(self):
        """Test eligibility check for non-existent customer"""
        data = {
            'customer_id': 9999,
            'loan_amount': 50000,
            'interest_rate': 10,
            'tenure': 12
        }
        response = self.client.post(
            reverse('check_eligibility'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
    
    def test_create_loan_success(self):
        """Test successful loan creation"""
        data = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 75000,
            'interest_rate': 8,
            'tenure': 10
        }
        response = self.client.post(
            reverse('create_loan'),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIn('loan_id', response_data)
        self.assertTrue(response_data.get('loan_approved'))
    
    def test_view_loan_success(self):
        """Test viewing loan details"""
        response = self.client.get(reverse('view_loan', args=[self.loan.loan_id]))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['loan_id'], self.loan.loan_id)
        self.assertIn('customer', response_data)
        self.assertIn('loan_amount', response_data)
    
    def test_view_loan_not_found(self):
        """Test viewing non-existent loan"""
        response = self.client.get(reverse('view_loan', args=[9999]))
        self.assertEqual(response.status_code, 404)
    
    def test_view_customer_loans_success(self):
        """Test viewing customer's loans"""
        response = self.client.get(reverse('view_customer_loans', args=[self.customer.customer_id]))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsInstance(response_data, list)
        self.assertGreater(len(response_data), 0)
        self.assertEqual(response_data[0]['loan_id'], self.loan.loan_id)
    
    def test_view_customer_loans_not_found(self):
        """Test viewing loans for non-existent customer"""
        response = self.client.get(reverse('view_customer_loans', args=[9999]))
        self.assertEqual(response.status_code, 404)


class CeleryTaskTest(TestCase):
    """Test cases for Celery tasks"""
    
    @patch('loans.tasks.openpyxl.load_workbook')
    def test_ingest_customer_data_task(self, mock_workbook):
        """Test customer data ingestion task"""
        # Create mock cells for each data value
        def create_mock_cell(value):
            cell = MagicMock()
            cell.value = value
            return cell
        
        # Mock worksheet with max_row property and indexed access
        mock_ws = MagicMock()
        mock_ws.max_row = 3  # Header + 2 data rows
        
        # Mock row access by index (sheet[row_num] returns list of cells)
        mock_ws.__getitem__ = MagicMock(side_effect={
            2: [  # Row 2 (first data row)
                create_mock_cell(1), create_mock_cell('John'), create_mock_cell('Doe'),
                create_mock_cell(30), create_mock_cell(1234567890),
                create_mock_cell(50000), create_mock_cell(1800000)
            ],
            3: [  # Row 3 (second data row)  
                create_mock_cell(2), create_mock_cell('Jane'), create_mock_cell('Smith'),
                create_mock_cell(25), create_mock_cell(9876543210),
                create_mock_cell(40000), create_mock_cell(1440000)
            ]
        }.get)
        
        mock_workbook.return_value.active = mock_ws
        
        # Run the task
        result = ingest_customer_data()
        
        # Verify customers were created
        self.assertEqual(Customer.objects.count(), 2)
        
        # Check specific customer data
        john = Customer.objects.get(customer_id=1)
        self.assertEqual(john.first_name, 'John')
        self.assertEqual(john.last_name, 'Doe')
        
        jane = Customer.objects.get(customer_id=2)
        self.assertEqual(jane.first_name, 'Jane')
        self.assertEqual(jane.last_name, 'Smith')
    
    @patch('loans.tasks.openpyxl.load_workbook')
    def test_ingest_loan_data_task(self, mock_workbook):
        """Test loan data ingestion task"""
        # First create a customer
        customer = Customer.objects.create(
            customer_id=1,
            first_name='John',
            last_name='Doe',
            age=30,
            phone_number=1234567890,
            monthly_salary=Decimal('50000.00'),
            approved_limit=Decimal('1800000.00')
        )
        
        # Create mock cells for each data value
        def create_mock_cell(value):
            cell = MagicMock()
            cell.value = value
            return cell
            
        # Mock worksheet with max_row property and indexed access
        mock_ws = MagicMock()
        mock_ws.max_row = 2  # Header + 1 data row
        
        # Mock row access by index (sheet[row_num] returns list of cells)
        mock_ws.__getitem__ = MagicMock(side_effect={
            2: [  # Row 2 (first data row)
                create_mock_cell(1), create_mock_cell(1001), create_mock_cell(100000),
                create_mock_cell(12), create_mock_cell(10.0), create_mock_cell(8792.59),
                create_mock_cell(10), create_mock_cell('2023-01-01'), create_mock_cell('2024-01-01')
            ]
        }.get)
        
        mock_workbook.return_value.active = mock_ws
        
        # Run the task
        result = ingest_loan_data()
        
        # Verify loan was created
        self.assertEqual(Loan.objects.count(), 1)
        loan = Loan.objects.first()
        self.assertEqual(loan.customer, customer)
        self.assertEqual(loan.loan_id, 1001)
        self.assertEqual(loan.loan_amount, Decimal('100000.00'))


class IntegrationTest(TestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.customer_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'age': 30,
            'phone_number': 1234567890,
            'monthly_income': 50000
        }
    
    def test_complete_customer_loan_workflow(self):
        """Test complete workflow: Register -> Check Eligibility -> Create Loan -> View Loan"""
        
        # Step 1: Register Customer
        register_response = self.client.post(
            reverse('register_customer'),
            data=json.dumps(self.customer_data),
            content_type='application/json'
        )
        self.assertEqual(register_response.status_code, 201)
        customer_id = json.loads(register_response.content)['customer_id']
        
        # Step 2: Check Loan Eligibility
        eligibility_data = {
            'customer_id': customer_id,
            'loan_amount': 100000,
            'interest_rate': 10,
            'tenure': 12
        }
        eligibility_response = self.client.post(
            reverse('check_eligibility'),
            data=json.dumps(eligibility_data),
            content_type='application/json'
        )
        self.assertEqual(eligibility_response.status_code, 200)
        eligibility_result = json.loads(eligibility_response.content)
        self.assertTrue(eligibility_result['approval'])
        
        # Step 3: Create Loan
        loan_data = {
            'customer_id': customer_id,
            'loan_amount': 75000,
            'interest_rate': 8,
            'tenure': 10
        }
        create_response = self.client.post(
            reverse('create_loan'),
            data=json.dumps(loan_data),
            content_type='application/json'
        )
        self.assertEqual(create_response.status_code, 200)
        loan_result = json.loads(create_response.content)
        self.assertTrue(loan_result['loan_approved'])
        loan_id = loan_result['loan_id']
        
        # Step 4: View Loan Details
        view_response = self.client.get(reverse('view_loan', args=[loan_id]))
        self.assertEqual(view_response.status_code, 200)
        loan_details = json.loads(view_response.content)
        self.assertEqual(loan_details['loan_id'], loan_id)
        
        # Step 5: View Customer Loans
        customer_loans_response = self.client.get(reverse('view_customer_loans', args=[customer_id]))
        self.assertEqual(customer_loans_response.status_code, 200)
        customer_loans = json.loads(customer_loans_response.content)
        self.assertGreater(len(customer_loans), 0)
        self.assertEqual(customer_loans[0]['loan_id'], loan_id)
    
    def test_loan_rejection_workflow(self):
        """Test workflow for loan rejection scenarios"""
        
        # Register customer with low income
        low_income_data = {
            'first_name': 'Poor',
            'last_name': 'Customer',
            'age': 25,
            'phone_number': 5555555555,
            'monthly_income': 15000  # Low income
        }
        register_response = self.client.post(
            reverse('register_customer'),
            data=json.dumps(low_income_data),
            content_type='application/json'
        )
        self.assertEqual(register_response.status_code, 201)
        customer_id = json.loads(register_response.content)['customer_id']
        
        # Try to create a large loan
        large_loan_data = {
            'customer_id': customer_id,
            'loan_amount': 800000,  # Very large amount
            'interest_rate': 15,
            'tenure': 12
        }
        create_response = self.client.post(
            reverse('create_loan'),
            data=json.dumps(large_loan_data),
            content_type='application/json'
        )
        self.assertEqual(create_response.status_code, 200)
        loan_result = json.loads(create_response.content)
        self.assertFalse(loan_result['loan_approved'])
        self.assertIsNone(loan_result['loan_id'])
    
    def test_credit_score_impact_on_interest_rate(self):
        """Test how credit score affects interest rate"""
        
        # Create customer with good payment history
        customer = Customer.objects.create(
            customer_id=1,
            first_name='Good',
            last_name='Customer',
            age=35,
            phone_number=1111111111,
            monthly_salary=Decimal('80000.00'),
            approved_limit=Decimal('2880000.00')
        )
        
        # Add good loan history
        Loan.objects.create(
            customer=customer,
            loan_id=2001,
            loan_amount=Decimal('200000.00'),
            tenure=24,
            interest_rate=Decimal('12.00'),
            monthly_repayment=Decimal('9429.20'),
            emis_paid_on_time=24,  # All EMIs paid on time
            start_date=date.today() - timedelta(days=730),
            end_date=date.today() - timedelta(days=30)
        )
        
        # Check eligibility for new loan
        eligibility_data = {
            'customer_id': customer.customer_id,
            'loan_amount': 150000,
            'interest_rate': 15,  # High rate requested
            'tenure': 18
        }
        eligibility_response = self.client.post(
            reverse('check_eligibility'),
            data=json.dumps(eligibility_data),
            content_type='application/json'
        )
        self.assertEqual(eligibility_response.status_code, 200)
        result = json.loads(eligibility_response.content)
        
        # Should be approved with potentially better rate
        self.assertTrue(result['approval'])
        corrected_rate = float(result['corrected_interest_rate'])
        self.assertLessEqual(corrected_rate, 15)  # Rate should be same or better

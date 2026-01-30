from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix PostgreSQL sequences for customers and loans tables to prevent duplicate key errors'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--table',
            type=str,
            choices=['customers', 'loans', 'all'],
            default='all',
            help='Which table sequences to fix (default: all)',
        )
    
    def handle(self, *args, **options):
        table = options['table']
        
        try:
            with connection.cursor() as cursor:
                if table in ['customers', 'all']:
                    # Fix customers table sequence
                    cursor.execute("""
                        SELECT setval('customers_customer_id_seq', 
                                     (SELECT COALESCE(MAX(customer_id), 0) + 1 FROM customers));
                    """)
                    result = cursor.fetchone()[0]
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Customer sequence fixed. Next customer_id will be: {result}'
                        )
                    )
                
                if table in ['loans', 'all']:
                    # Fix loans table sequence with correct table name
                    cursor.execute("""
                        SELECT setval(pg_get_serial_sequence('loans', 'loan_id'), 
                                     (SELECT COALESCE(MAX(loan_id), 0) + 1 FROM loans));
                    """)
                    result = cursor.fetchone()[0]
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Loan sequence fixed. Next loan_id will be: {result}'
                        )
                    )
                
                # Show current status
                if table in ['customers', 'all']:
                    cursor.execute("SELECT MAX(customer_id) FROM customers;")
                    max_customer_id = cursor.fetchone()[0]
                    cursor.execute("SELECT last_value FROM customers_customer_id_seq;")
                    next_customer_id = cursor.fetchone()[0]
                    
                    self.stdout.write(
                        self.style.WARNING(
                            f'📊 Customer Status: Max ID = {max_customer_id}, Next ID = {next_customer_id}'
                        )
                    )
                
                if table in ['loans', 'all']:
                    cursor.execute("SELECT MAX(loan_id) FROM loans;")
                    max_loan_id = cursor.fetchone()[0] or 0
                    cursor.execute("SELECT last_value FROM loans_loan_id_seq;")
                    next_loan_id = cursor.fetchone()[0]
                    
                    self.stdout.write(
                        self.style.WARNING(
                            f'📊 Loan Status: Max ID = {max_loan_id}, Next ID = {next_loan_id}'
                        )
                    )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error fixing sequences: {str(e)}')
            )
            raise e
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🎉 Database sequences have been fixed! New registrations should work now.'
            )
        )
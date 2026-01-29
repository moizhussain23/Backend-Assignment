from django.core.management.base import BaseCommand
from loans.tasks import ingest_customer_data, ingest_loan_data, calculate_current_debt


class Command(BaseCommand):
    help = 'Ingest customer and loan data from Excel files'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data ingestion...'))
        
        # Run customer data ingestion
        self.stdout.write('Ingesting customer data...')
        result1 = ingest_customer_data.delay()
        self.stdout.write(f'Customer data task started: {result1.id}')
        
        # Run loan data ingestion
        self.stdout.write('Ingesting loan data...')
        result2 = ingest_loan_data.delay()
        self.stdout.write(f'Loan data task started: {result2.id}')
        
        # Calculate current debt
        self.stdout.write('Calculating current debt...')
        result3 = calculate_current_debt.delay()
        self.stdout.write(f'Current debt calculation task started: {result3.id}')
        
        self.stdout.write(
            self.style.SUCCESS('Data ingestion tasks have been queued successfully!')
        )
#!/usr/bin/env python
"""
Comprehensive test runner for Credit Approval System
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

def run_tests():
    """Run all tests with proper configuration"""
    
    # Set test settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')
    django.setup()
    
    # Get test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True)
    
    # Test labels - can specify specific tests or run all
    test_labels = [
        'loans.tests.CustomerModelTest',
        'loans.tests.LoanModelTest', 
        'loans.tests.UtilityFunctionsTest',
        'loans.tests.APIEndpointTest',
        'loans.tests.CeleryTaskTest',
        'loans.tests.IntegrationTest',
    ]
    
    print("🧪 Running Credit Approval System Test Suite")
    print("=" * 60)
    
    # Run tests
    failures = test_runner.run_tests(test_labels)
    
    if failures:
        print(f"\n❌ {failures} test(s) failed")
        return False
    else:
        print(f"\n✅ All tests passed successfully!")
        return True

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
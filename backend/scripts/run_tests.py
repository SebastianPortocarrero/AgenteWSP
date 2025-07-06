#!/usr/bin/env python3
# ================================================================
# COMPREHENSIVE TEST RUNNER SCRIPT
# Tony WhatsApp Assistant - Backend Testing Suite
# ================================================================

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestRunner:
    """Comprehensive test runner with coverage and security checks."""
    
    def __init__(self, coverage_threshold: float = 85.0):
        self.coverage_threshold = coverage_threshold
        self.start_time = time.time()
        self.results = {
            'unit_tests': {'passed': False, 'details': {}},
            'integration_tests': {'passed': False, 'details': {}},
            'security_tests': {'passed': False, 'details': {}},
            'performance_tests': {'passed': False, 'details': {}},
            'coverage': {'passed': False, 'details': {}},
            'quality_checks': {'passed': False, 'details': {}},
            'vulnerability_scan': {'passed': False, 'details': {}}
        }
    
    def run_command(self, command: str, description: str, 
                   check_returncode: bool = True) -> Tuple[bool, str, str]:
        """Run a shell command and return success status with output."""
        logger.info(f"Running: {description}")
        logger.debug(f"Command: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if check_returncode and result.returncode != 0:
                logger.error(f"Command failed: {description}")
                logger.error(f"Error output: {result.stderr}")
                return False, result.stdout, result.stderr
            
            logger.info(f"Completed: {description}")
            return True, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {description}")
            return False, "", "Command timeout"
        except Exception as e:
            logger.error(f"Command error: {description} - {str(e)}")
            return False, "", str(e)
    
    def install_dependencies(self) -> bool:
        """Install test dependencies."""
        logger.info("Installing test dependencies...")
        
        commands = [
            "pip install -r requirements-test.txt",
            "pip install -e .",  # Install package in development mode
        ]
        
        for cmd in commands:
            success, stdout, stderr = self.run_command(
                cmd, f"Installing dependencies: {cmd}"
            )
            if not success:
                return False
        
        return True
    
    def run_unit_tests(self) -> bool:
        """Run unit tests with coverage."""
        logger.info("Running unit tests...")
        
        command = (
            "python -m pytest tests/ "
            "-m 'unit' "
            "--cov=src "
            "--cov-report=term-missing "
            "--cov-report=html:htmlcov "
            "--cov-report=xml:coverage.xml "
            "--cov-report=json:coverage.json "
            f"--cov-fail-under={self.coverage_threshold} "
            "--tb=short "
            "--maxfail=5 "
            "-v"
        )
        
        success, stdout, stderr = self.run_command(
            command, "Unit tests with coverage", check_returncode=False
        )
        
        # Parse coverage results
        try:
            with open('coverage.json', 'r') as f:
                coverage_data = json.load(f)
                coverage_percent = coverage_data['totals']['percent_covered']
                
                self.results['unit_tests']['details'] = {
                    'coverage_percent': coverage_percent,
                    'lines_covered': coverage_data['totals']['covered_lines'],
                    'lines_total': coverage_data['totals']['num_statements'],
                    'missing_lines': coverage_data['totals']['missing_lines']
                }
                
                if coverage_percent >= self.coverage_threshold:
                    self.results['unit_tests']['passed'] = True
                    self.results['coverage']['passed'] = True
                    logger.info(f"Unit tests passed with {coverage_percent:.1f}% coverage")
                else:
                    logger.error(f"Coverage {coverage_percent:.1f}% below threshold {self.coverage_threshold}%")
                    
        except Exception as e:
            logger.error(f"Failed to parse coverage data: {e}")
            
        return success and self.results['unit_tests']['passed']
    
    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        logger.info("Running integration tests...")
        
        command = (
            "python -m pytest tests/ "
            "-m 'integration' "
            "--tb=short "
            "--maxfail=3 "
            "-v"
        )
        
        success, stdout, stderr = self.run_command(
            command, "Integration tests"
        )
        
        self.results['integration_tests']['passed'] = success
        return success
    
    def run_security_tests(self) -> bool:
        """Run security tests."""
        logger.info("Running security tests...")
        
        # Run pytest security tests
        command = (
            "python -m pytest tests/ "
            "-m 'security' "
            "--tb=short "
            "--maxfail=1 "
            "-v"
        )
        
        success, stdout, stderr = self.run_command(
            command, "Security tests"
        )
        
        self.results['security_tests']['passed'] = success
        return success
    
    def run_bandit_security_scan(self) -> bool:
        """Run Bandit security scanner."""
        logger.info("Running Bandit security scan...")
        
        command = (
            "bandit -r src/ "
            "-c bandit.yaml "
            "-f json "
            "-o bandit_results.json"
        )
        
        success, stdout, stderr = self.run_command(
            command, "Bandit security scan", check_returncode=False
        )
        
        # Parse Bandit results
        try:
            with open('bandit_results.json', 'r') as f:
                bandit_data = json.load(f)
                
                high_severity = len([issue for issue in bandit_data.get('results', []) 
                                   if issue.get('issue_severity') == 'HIGH'])
                medium_severity = len([issue for issue in bandit_data.get('results', []) 
                                     if issue.get('issue_severity') == 'MEDIUM'])
                
                self.results['vulnerability_scan']['details'] = {
                    'high_severity_issues': high_severity,
                    'medium_severity_issues': medium_severity,
                    'total_issues': len(bandit_data.get('results', [])),
                    'confidence_level': bandit_data.get('metrics', {}).get('_totals', {})
                }
                
                # Pass if no high severity issues
                if high_severity == 0:
                    self.results['vulnerability_scan']['passed'] = True
                    logger.info(f"Security scan passed: {high_severity} high, {medium_severity} medium issues")
                else:
                    logger.error(f"Security scan failed: {high_severity} high severity issues found")
                
        except Exception as e:
            logger.error(f"Failed to parse Bandit results: {e}")
            
        return self.results['vulnerability_scan']['passed']
    
    def run_safety_check(self) -> bool:
        """Run Safety dependency vulnerability check."""
        logger.info("Running Safety dependency check...")
        
        command = "safety check --json --output safety_results.json"
        
        success, stdout, stderr = self.run_command(
            command, "Safety dependency check", check_returncode=False
        )
        
        # Parse Safety results
        try:
            with open('safety_results.json', 'r') as f:
                safety_data = json.load(f)
                
                vulnerabilities = len(safety_data) if isinstance(safety_data, list) else 0
                
                if vulnerabilities == 0:
                    logger.info("Safety check passed: No known vulnerabilities")
                    return True
                else:
                    logger.error(f"Safety check failed: {vulnerabilities} vulnerabilities found")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to parse Safety results: {e}")
            return False
    
    def run_performance_tests(self) -> bool:
        """Run performance tests."""
        logger.info("Running performance tests...")
        
        command = (
            "python -m pytest tests/ "
            "-m 'performance' "
            "--tb=short "
            "--maxfail=2 "
            "-v "
            "--benchmark-skip"  # Skip benchmarks in CI
        )
        
        success, stdout, stderr = self.run_command(
            command, "Performance tests"
        )
        
        self.results['performance_tests']['passed'] = success
        return success
    
    def run_quality_checks(self) -> bool:
        """Run code quality checks."""
        logger.info("Running code quality checks...")
        
        checks = [
            ("black --check src/", "Code formatting check"),
            ("isort --check-only src/", "Import sorting check"),
            ("flake8 src/", "Linting check"),
            ("mypy src/", "Type checking")
        ]
        
        all_passed = True
        for command, description in checks:
            success, stdout, stderr = self.run_command(
                command, description, check_returncode=False
            )
            if not success:
                all_passed = False
                logger.error(f"Quality check failed: {description}")
        
        self.results['quality_checks']['passed'] = all_passed
        return all_passed
    
    def run_regression_tests(self) -> bool:
        """Run regression tests."""
        logger.info("Running regression tests...")
        
        command = (
            "python -m pytest tests/ "
            "-m 'regression' "
            "--tb=short "
            "--maxfail=1 "
            "-v"
        )
        
        success, stdout, stderr = self.run_command(
            command, "Regression tests"
        )
        
        return success
    
    def generate_test_report(self) -> None:
        """Generate comprehensive test report."""
        logger.info("Generating test report...")
        
        total_time = time.time() - self.start_time
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_time_seconds': total_time,
            'coverage_threshold': self.coverage_threshold,
            'results': self.results,
            'summary': {
                'total_tests': len(self.results),
                'passed_tests': sum(1 for r in self.results.values() if r['passed']),
                'failed_tests': sum(1 for r in self.results.values() if not r['passed']),
                'overall_success': all(r['passed'] for r in self.results.values())
            }
        }
        
        # Save detailed report
        with open('test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        logger.info("=" * 60)
        logger.info("TEST EXECUTION SUMMARY")
        logger.info("=" * 60)
        
        for test_type, result in self.results.items():
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            logger.info(f"{test_type.replace('_', ' ').title()}: {status}")
            
            if result['details']:
                for key, value in result['details'].items():
                    logger.info(f"  {key}: {value}")
        
        logger.info("=" * 60)
        logger.info(f"Overall Result: {'✅ ALL TESTS PASSED' if report['summary']['overall_success'] else '❌ SOME TESTS FAILED'}")
        logger.info(f"Total Time: {total_time:.2f} seconds")
        logger.info(f"Coverage: {self.results['unit_tests']['details'].get('coverage_percent', 0):.1f}%")
        logger.info("=" * 60)
        
        return report['summary']['overall_success']
    
    def run_all_tests(self, 
                     skip_install: bool = False,
                     skip_quality: bool = False,
                     skip_security: bool = False,
                     skip_performance: bool = False) -> bool:
        """Run all tests in sequence."""
        logger.info("Starting comprehensive test suite...")
        
        # Install dependencies
        if not skip_install:
            if not self.install_dependencies():
                logger.error("Failed to install dependencies")
                return False
        
        # Run tests in order
        test_sequence = [
            (self.run_unit_tests, "Unit tests"),
            (self.run_integration_tests, "Integration tests"),
        ]
        
        if not skip_security:
            test_sequence.extend([
                (self.run_security_tests, "Security tests"),
                (self.run_bandit_security_scan, "Security scan"),
                (self.run_safety_check, "Dependency vulnerability scan"),
            ])
        
        if not skip_performance:
            test_sequence.append((self.run_performance_tests, "Performance tests"))
        
        if not skip_quality:
            test_sequence.append((self.run_quality_checks, "Quality checks"))
        
        # Add regression tests
        test_sequence.append((self.run_regression_tests, "Regression tests"))
        
        # Execute all tests
        for test_func, test_name in test_sequence:
            logger.info(f"Starting {test_name}...")
            try:
                test_func()
            except Exception as e:
                logger.error(f"Error in {test_name}: {e}")
        
        # Generate final report
        success = self.generate_test_report()
        
        return success

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Run comprehensive test suite')
    parser.add_argument('--coverage-threshold', type=float, default=85.0,
                       help='Minimum coverage percentage required (default: 85.0)')
    parser.add_argument('--skip-install', action='store_true',
                       help='Skip dependency installation')
    parser.add_argument('--skip-quality', action='store_true',
                       help='Skip code quality checks')
    parser.add_argument('--skip-security', action='store_true',
                       help='Skip security tests')
    parser.add_argument('--skip-performance', action='store_true',
                       help='Skip performance tests')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick tests only (unit + integration)')
    
    args = parser.parse_args()
    
    if args.quick:
        args.skip_quality = True
        args.skip_security = True
        args.skip_performance = True
    
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    # Run tests
    runner = TestRunner(coverage_threshold=args.coverage_threshold)
    success = runner.run_all_tests(
        skip_install=args.skip_install,
        skip_quality=args.skip_quality,
        skip_security=args.skip_security,
        skip_performance=args.skip_performance
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 
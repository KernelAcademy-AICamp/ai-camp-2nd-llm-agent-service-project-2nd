#!/usr/bin/env python3
"""
TDD Workflow Helper Script
Enforces RED-GREEN-REFACTOR cycle
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple
import argparse

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'
    BOLD = '\033[1m'

class TDDRunner:
    def __init__(self, test_path: Optional[str] = None):
        self.test_path = test_path or "tests"
        self.project_root = Path.cwd()

    def print_phase(self, phase: str, message: str):
        """Print colored phase message"""
        colors = {
            "RED": Colors.RED,
            "GREEN": Colors.GREEN,
            "REFACTOR": Colors.BLUE
        }
        color = colors.get(phase, Colors.END)
        print(f"\n{color}{Colors.BOLD}{'='*60}")
        print(f"🔴🟢🔵 TDD Phase: {phase}")
        print(f"{message}")
        print(f"{'='*60}{Colors.END}\n")

    def run_tests(self, marker: Optional[str] = None) -> Tuple[bool, str]:
        """Run pytest with optional marker"""
        cmd = ["pytest", self.test_path, "-v", "--tb=short"]

        if marker:
            cmd.extend(["-m", marker])

        # Always run failed tests first
        cmd.append("--lf")

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout + result.stderr

    def check_coverage(self) -> Tuple[bool, float]:
        """Check test coverage"""
        cmd = ["pytest", "--cov=src", "--cov-report=term"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Parse coverage percentage
        output = result.stdout
        for line in output.split('\n'):
            if 'TOTAL' in line:
                parts = line.split()
                for part in parts:
                    if '%' in part:
                        coverage = float(part.strip('%'))
                        return coverage >= 80, coverage

        return False, 0.0

    def red_phase(self, feature: str) -> bool:
        """RED Phase: Write failing test"""
        self.print_phase("RED", f"Writing test for: {feature}")

        print(f"{Colors.YELLOW}Instructions:")
        print("1. Write a test that defines the desired behavior")
        print("2. The test MUST fail meaningfully")
        print(f"3. Mark test with @pytest.mark.red{Colors.END}")

        input("\nPress Enter when test is written...")

        # Run the test - it should fail
        passed, output = self.run_tests("red")

        if passed:
            print(f"{Colors.RED}❌ ERROR: Test passed but should fail in RED phase!")
            print("Tests must fail before implementation.{Colors.END}")
            return False
        else:
            print(f"{Colors.GREEN}✅ Good! Test failed as expected.")
            print(f"Proceeding to GREEN phase...{Colors.END}")

            # Commit RED phase
            self.commit(f"test: [{feature}] add failing tests (RED)")
            return True

    def green_phase(self, feature: str) -> bool:
        """GREEN Phase: Minimal implementation"""
        self.print_phase("GREEN", f"Implementing minimal code for: {feature}")

        print(f"{Colors.YELLOW}Instructions:")
        print("1. Write MINIMAL code to make the test pass")
        print("2. No extra features or optimizations")
        print(f"3. Update test marker to @pytest.mark.green{Colors.END}")

        input("\nPress Enter when implementation is done...")

        # Run the test - it should pass now
        passed, output = self.run_tests("green")

        if not passed:
            print(f"{Colors.RED}❌ ERROR: Test still failing!")
            print("Implementation must make the test pass.{Colors.END}")
            print("\nFailed tests output:")
            print(output)
            return False
        else:
            print(f"{Colors.GREEN}✅ Excellent! Test passing.")
            print(f"Proceeding to REFACTOR phase...{Colors.END}")

            # Commit GREEN phase
            self.commit(f"feat: [{feature}] implement minimal solution (GREEN)")
            return True

    def refactor_phase(self, feature: str) -> bool:
        """REFACTOR Phase: Improve code quality"""
        self.print_phase("REFACTOR", f"Refactoring: {feature}")

        print(f"{Colors.YELLOW}Instructions:")
        print("1. Improve code structure and quality")
        print("2. Tests must remain green")
        print("3. Check code coverage (must be >= 80%)")
        print(f"4. Update test marker to @pytest.mark.refactor{Colors.END}")

        input("\nPress Enter when refactoring is done...")

        # Run all tests
        passed, output = self.run_tests()

        if not passed:
            print(f"{Colors.RED}❌ ERROR: Tests failing after refactoring!")
            print("All tests must remain green.{Colors.END}")
            return False

        # Check coverage
        coverage_ok, coverage_pct = self.check_coverage()

        print(f"\n📊 Coverage: {coverage_pct:.2f}%")

        if not coverage_ok:
            print(f"{Colors.YELLOW}⚠️ Warning: Coverage below 80%")
            print(f"Consider adding more tests.{Colors.END}")
        else:
            print(f"{Colors.GREEN}✅ Coverage meets requirements!{Colors.END}")

        # Commit REFACTOR phase
        self.commit(f"refactor: [{feature}] improve code quality (REFACTOR)")

        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 TDD Cycle Complete for: {feature}{Colors.END}")
        return True

    def commit(self, message: str):
        """Git commit with TDD phase message"""
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", message])
        print(f"📝 Committed: {message}")

    def full_cycle(self, feature: str):
        """Run full TDD cycle for a feature"""
        print(f"\n{Colors.BOLD}Starting TDD Cycle for: {feature}{Colors.END}")

        # RED Phase
        if not self.red_phase(feature):
            print(f"{Colors.RED}Failed at RED phase. Please fix and retry.{Colors.END}")
            return False

        time.sleep(1)

        # GREEN Phase
        if not self.green_phase(feature):
            print(f"{Colors.RED}Failed at GREEN phase. Please fix and retry.{Colors.END}")
            return False

        time.sleep(1)

        # REFACTOR Phase
        if not self.refactor_phase(feature):
            print(f"{Colors.RED}Failed at REFACTOR phase. Please fix and retry.{Colors.END}")
            return False

        return True

    def watch_mode(self):
        """Run tests in watch mode"""
        print(f"{Colors.YELLOW}Starting watch mode...")
        print(f"Tests will run automatically on file changes.{Colors.END}")
        subprocess.run(["pytest-watch", "--", "-v", "--tb=short"])

def main():
    parser = argparse.ArgumentParser(description="TDD Workflow Helper")
    parser.add_argument("command", choices=["cycle", "red", "green", "refactor", "watch"],
                       help="TDD command to run")
    parser.add_argument("feature", nargs="?", help="Feature name")
    parser.add_argument("--path", default="tests", help="Test path")

    args = parser.parse_args()

    runner = TDDRunner(args.path)

    if args.command == "cycle":
        if not args.feature:
            print("Error: Feature name required for cycle command")
            sys.exit(1)
        runner.full_cycle(args.feature)
    elif args.command == "red":
        if not args.feature:
            print("Error: Feature name required for red phase")
            sys.exit(1)
        runner.red_phase(args.feature)
    elif args.command == "green":
        if not args.feature:
            print("Error: Feature name required for green phase")
            sys.exit(1)
        runner.green_phase(args.feature)
    elif args.command == "refactor":
        if not args.feature:
            print("Error: Feature name required for refactor phase")
            sys.exit(1)
        runner.refactor_phase(args.feature)
    elif args.command == "watch":
        runner.watch_mode()

if __name__ == "__main__":
    main()
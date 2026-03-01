#!/usr/bin/env python3
"""
Code Quality Analyzer - Automated code quality assessment and metrics
Analyzes complexity, maintainability, performance, and code smells
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Optional
import hashlib
import json
import time
import sys
import statistics


class ComplexityLevel(Enum):
    """Code complexity classification"""
    SIMPLE = "SIMPLE"
    MODERATE = "MODERATE"
    COMPLEX = "COMPLEX"
    VERY_COMPLEX = "VERY_COMPLEX"


class IssueType(Enum):
    """Types of code quality issues"""
    HIGH_COMPLEXITY = "HIGH_COMPLEXITY"
    LONG_METHOD = "LONG_METHOD"
    DUPLICATE_CODE = "DUPLICATE_CODE"
    DEAD_CODE = "DEAD_CODE"
    LONG_PARAMETER_LIST = "LONG_PARAMETER_LIST"
    DEEP_NESTING = "DEEP_NESTING"
    MAGIC_NUMBERS = "MAGIC_NUMBERS"
    INCONSISTENT_NAMING = "INCONSISTENT_NAMING"
    MISSING_DOCUMENTATION = "MISSING_DOCUMENTATION"
    PERFORMANCE_ISSUE = "PERFORMANCE_ISSUE"


class CodeMetricType(Enum):
    """Types of code metrics"""
    CYCLOMATIC_COMPLEXITY = "CYCLOMATIC_COMPLEXITY"
    COGNITIVE_COMPLEXITY = "COGNITIVE_COMPLEXITY"
    LINES_OF_CODE = "LINES_OF_CODE"
    FUNCTION_COUNT = "FUNCTION_COUNT"
    COMMENT_RATIO = "COMMENT_RATIO"
    DUPLICATE_RATIO = "DUPLICATE_RATIO"
    TEST_COVERAGE = "TEST_COVERAGE"


@dataclass
class CodeIssue:
    """Represents a code quality issue"""
    issue_id: str
    issue_type: IssueType
    severity: str  # "CRITICAL", "MAJOR", "MINOR"
    file_path: str
    line_number: int
    description: str
    affected_code: str
    suggestion: str
    priority: int = 1  # 1-5, 5 is highest


@dataclass
class FunctionMetrics:
    """Metrics for a single function"""
    name: str
    file_path: str
    line_start: int
    line_end: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    lines_of_code: int
    parameter_count: int
    nesting_depth: int
    has_documentation: bool
    test_coverage: float  # 0-100


@dataclass
class FileMetrics:
    """Metrics for a single file"""
    file_path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    functions: List[FunctionMetrics] = field(default_factory=list)
    classes: int = 0
    avg_cyclomatic_complexity: float = 0.0
    avg_cognitive_complexity: float = 0.0
    duplicate_lines: int = 0
    test_coverage: float = 0.0


@dataclass
class QualityScore:
    """Overall quality score"""
    overall_score: float  # 0-100
    maintainability_index: float  # 0-100
    reliability_score: float  # 0-100
    security_score: float  # 0-100
    performance_score: float  # 0-100
    test_coverage: float  # 0-100
    technical_debt_hours: float  # Estimated hours to fix issues
    grade: str  # A, B, C, D, F


@dataclass
class QualityAnalysisResult:
    """Complete quality analysis result"""
    analysis_id: str
    timestamp: float
    project_path: str
    files_analyzed: Dict[str, FileMetrics] = field(default_factory=dict)
    issues: List[CodeIssue] = field(default_factory=list)
    quality_score: Optional[QualityScore] = None
    improvement_suggestions: List[str] = field(default_factory=list)


class CodeQualityAnalyzer:
    """
    Comprehensive code quality analyzer

    Analyzes:
    - Cyclomatic and cognitive complexity
    - Code smells and anti-patterns
    - Test coverage and documentation
    - Duplicate code detection
    - Performance anti-patterns
    - Naming consistency
    - Code metrics aggregation
    """

    def __init__(self):
        self.analysis_results: Dict[str, QualityAnalysisResult] = {}
        self.complexity_thresholds = {
            ComplexityLevel.SIMPLE: 1,
            ComplexityLevel.MODERATE: 5,
            ComplexityLevel.COMPLEX: 10,
            ComplexityLevel.VERY_COMPLEX: 15,
        }

    def analyze_code(self, code_files: Dict[str, str], test_coverage: Optional[Dict[str, float]] = None) -> QualityAnalysisResult:
        """
        Analyze code quality across multiple files

        Args:
            code_files: Dict of file path to code content
            test_coverage: Optional dict of file path to coverage percentage

        Returns:
            QualityAnalysisResult with metrics and issues
        """
        analysis_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]
        result = QualityAnalysisResult(
            analysis_id=analysis_id,
            timestamp=time.time(),
            project_path="."
        )

        # Analyze each file
        for file_path, code_content in code_files.items():
            file_metrics = self._analyze_file(file_path, code_content)
            if test_coverage and file_path in test_coverage:
                file_metrics.test_coverage = test_coverage[file_path]
            result.files_analyzed[file_path] = file_metrics

            # Find issues in file
            issues = self._find_code_issues(file_path, code_content, file_metrics)
            result.issues.extend(issues)

        # Calculate overall quality score
        result.quality_score = self._calculate_quality_score(result)

        # Generate improvement suggestions
        result.improvement_suggestions = self._generate_suggestions(result)

        self.analysis_results[analysis_id] = result
        return result

    def _analyze_file(self, file_path: str, code_content: str) -> FileMetrics:
        """Analyze a single file"""
        lines = code_content.split('\n')
        metrics = FileMetrics(file_path=file_path, total_lines=len(lines))

        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        functions = []
        in_comment = False

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Count line types
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('#') or stripped.startswith('//'):
                comment_lines += 1
            else:
                code_lines += 1

            # Find functions
            if 'def ' in line or 'function ' in line:
                func_metrics = self._analyze_function(
                    line_num, code_content, line
                )
                functions.append(func_metrics)

            # Count classes
            if 'class ' in line:
                metrics.classes += 1

        metrics.code_lines = code_lines
        metrics.comment_lines = comment_lines
        metrics.blank_lines = blank_lines
        metrics.functions = functions

        # Calculate averages
        if functions:
            metrics.avg_cyclomatic_complexity = statistics.mean(
                [f.cyclomatic_complexity for f in functions]
            )
            metrics.avg_cognitive_complexity = statistics.mean(
                [f.cognitive_complexity for f in functions]
            )

        # Detect duplicate code
        metrics.duplicate_lines = self._detect_duplicates(code_content)

        return metrics

    def _analyze_function(self, line_num: int, code_content: str, func_line: str) -> FunctionMetrics:
        """Analyze a single function"""
        # Extract function name
        func_name = func_line.split('(')[0].replace('def ', '').replace('function ', '').strip()

        lines = code_content.split('\n')
        func_lines = [func_line]
        current_indent = len(func_line) - len(func_line.lstrip())
        max_nesting = 1

        # Find function body
        end_line = line_num
        for i in range(line_num, min(line_num + 100, len(lines))):
            line = lines[i]
            if line.strip() and not line.startswith(' ' * (current_indent + 1)) and i > line_num:
                break
            func_lines.append(line)
            end_line = i + 1

            # Track nesting depth
            indent = len(line) - len(line.lstrip())
            nesting = (indent - current_indent) // 4
            max_nesting = max(max_nesting, nesting)

        # Calculate complexity metrics
        cyclomatic = self._calculate_cyclomatic_complexity(func_lines)
        cognitive = self._calculate_cognitive_complexity(func_lines)

        # Count parameters
        param_str = func_line.split('(')[1].split(')')[0] if '(' in func_line else ""
        param_count = len([p for p in param_str.split(',') if p.strip()])

        # Check documentation
        has_doc = any('"""' in line or "'''" in line for line in func_lines[:3])

        return FunctionMetrics(
            name=func_name,
            file_path="",
            line_start=line_num,
            line_end=end_line,
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            lines_of_code=len(func_lines),
            parameter_count=param_count,
            nesting_depth=max_nesting,
            has_documentation=has_doc,
            test_coverage=0.0
        )

    def _calculate_cyclomatic_complexity(self, func_lines: List[str]) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        keywords = ['if ', 'elif ', 'except ', 'for ', 'while ', 'and ', 'or ', 'case ']

        for line in func_lines:
            for keyword in keywords:
                complexity += line.count(keyword)

        return min(complexity, 20)  # Cap at 20

    def _calculate_cognitive_complexity(self, func_lines: List[str]) -> int:
        """Calculate cognitive complexity"""
        cognitive = 0
        nesting_level = 0

        for line in func_lines:
            indent = len(line) - len(line.lstrip())
            nesting_level = indent // 4

            keywords = {
                'if ': 1,
                'elif ': 1,
                'else': 1,
                'for ': 1,
                'while ': 1,
                'except ': 1,
                'catch': 1,
                'switch': 1,
            }

            for keyword, weight in keywords.items():
                if keyword in line:
                    cognitive += weight * (1 + nesting_level * 0.5)

        return int(min(cognitive, 30))

    def _detect_duplicates(self, code_content: str) -> int:
        """Detect duplicate code lines"""
        lines = code_content.split('\n')
        line_counts = {}
        duplicates = 0

        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                line_counts[stripped] = line_counts.get(stripped, 0) + 1

        for line, count in line_counts.items():
            if count > 1:
                duplicates += (count - 1)

        return duplicates

    def _find_code_issues(self, file_path: str, code_content: str, metrics: FileMetrics) -> List[CodeIssue]:
        """Find code quality issues"""
        issues = []
        lines = code_content.split('\n')

        # Check for high complexity functions
        for func in metrics.functions:
            if func.cyclomatic_complexity > 10:
                issues.append(CodeIssue(
                    issue_id=f"{file_path}:{func.line_start}:complexity",
                    issue_type=IssueType.HIGH_COMPLEXITY,
                    severity="MAJOR",
                    file_path=file_path,
                    line_number=func.line_start,
                    description=f"Function '{func.name}' has high cyclomatic complexity ({func.cyclomatic_complexity})",
                    affected_code=f"def {func.name}(...)",
                    suggestion="Refactor into smaller functions or reduce branching",
                    priority=4
                ))

            # Check for long methods
            if func.lines_of_code > 50:
                issues.append(CodeIssue(
                    issue_id=f"{file_path}:{func.line_start}:long_method",
                    issue_type=IssueType.LONG_METHOD,
                    severity="MAJOR",
                    file_path=file_path,
                    line_number=func.line_start,
                    description=f"Function '{func.name}' is too long ({func.lines_of_code} lines)",
                    affected_code=f"def {func.name}(...)",
                    suggestion="Split function into smaller, single-responsibility methods",
                    priority=3
                ))

            # Check for long parameter lists
            if func.parameter_count > 5:
                issues.append(CodeIssue(
                    issue_id=f"{file_path}:{func.line_start}:params",
                    issue_type=IssueType.LONG_PARAMETER_LIST,
                    severity="MINOR",
                    file_path=file_path,
                    line_number=func.line_start,
                    description=f"Function '{func.name}' has too many parameters ({func.parameter_count})",
                    affected_code=f"def {func.name}(...)",
                    suggestion="Use objects or data classes to group related parameters",
                    priority=2
                ))

            # Check for missing documentation
            if not func.has_documentation:
                issues.append(CodeIssue(
                    issue_id=f"{file_path}:{func.line_start}:docs",
                    issue_type=IssueType.MISSING_DOCUMENTATION,
                    severity="MINOR",
                    file_path=file_path,
                    line_number=func.line_start,
                    description=f"Function '{func.name}' lacks documentation",
                    affected_code=f"def {func.name}(...)",
                    suggestion="Add docstring with description, parameters, and return value",
                    priority=1
                ))

            # Check for deep nesting
            if func.nesting_depth > 4:
                issues.append(CodeIssue(
                    issue_id=f"{file_path}:{func.line_start}:nesting",
                    issue_type=IssueType.DEEP_NESTING,
                    severity="MAJOR",
                    file_path=file_path,
                    line_number=func.line_start,
                    description=f"Function '{func.name}' has deep nesting (depth: {func.nesting_depth})",
                    affected_code=f"def {func.name}(...)",
                    suggestion="Use early returns or extract nested logic to separate functions",
                    priority=3
                ))

        # Check for duplicate code
        if metrics.duplicate_lines > 10:
            issues.append(CodeIssue(
                issue_id=f"{file_path}:duplicates",
                issue_type=IssueType.DUPLICATE_CODE,
                severity="MAJOR",
                file_path=file_path,
                line_number=1,
                description=f"File contains {metrics.duplicate_lines} duplicate lines",
                affected_code="Multiple locations",
                suggestion="Extract duplicate code into reusable functions or base classes",
                priority=4
            ))

        # Check for magic numbers
        for line_num, line in enumerate(lines, 1):
            if any(str(num) in line for num in ['42', '100', '256', '1000', '9999']):
                if 'CONSTANT' not in line and '=' in line:
                    issues.append(CodeIssue(
                        issue_id=f"{file_path}:{line_num}:magic",
                        issue_type=IssueType.MAGIC_NUMBERS,
                        severity="MINOR",
                        file_path=file_path,
                        line_number=line_num,
                        description="Magic number in code",
                        affected_code=line.strip(),
                        suggestion="Replace with named constant",
                        priority=1
                    ))
                    break  # Only flag one per file

        return issues

    def _calculate_quality_score(self, result: QualityAnalysisResult) -> QualityScore:
        """Calculate overall quality score"""
        if not result.files_analyzed:
            return QualityScore(0, 0, 0, 0, 0, 0, 0, "F")

        # Calculate component scores
        files = list(result.files_analyzed.values())

        # Maintainability: based on complexity and documentation
        avg_complexity = statistics.mean([f.avg_cyclomatic_complexity for f in files if f.avg_cyclomatic_complexity > 0] or [5])
        maintainability = max(0, 100 - (avg_complexity * 5))

        # Reliability: based on test coverage
        avg_coverage = statistics.mean([f.test_coverage for f in files]) if files else 0
        reliability = avg_coverage * 0.8  # Test coverage contributes 80%
        reliability += (100 - len(result.issues) * 2) * 0.2  # Issues contribute 20%

        # Security: based on code issues
        security = max(0, 100 - len(result.issues) * 3)

        # Performance: based on complexity and nesting
        avg_nesting = statistics.mean([
            max([f.nesting_depth for f in func_list], default=1)
            for func_list in [f.functions for f in files]
        ]) if files else 1
        performance = max(0, 100 - (avg_nesting * 10))

        # Overall score
        overall = (maintainability + reliability + security + performance) / 4

        # Technical debt estimation
        issue_hours = len(result.issues) * 2

        # Determine grade
        if overall >= 90:
            grade = "A"
        elif overall >= 80:
            grade = "B"
        elif overall >= 70:
            grade = "C"
        elif overall >= 60:
            grade = "D"
        else:
            grade = "F"

        return QualityScore(
            overall_score=overall,
            maintainability_index=maintainability,
            reliability_score=reliability,
            security_score=security,
            performance_score=performance,
            test_coverage=avg_coverage,
            technical_debt_hours=issue_hours,
            grade=grade
        )

    def _generate_suggestions(self, result: QualityAnalysisResult) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []

        if not result.quality_score:
            return suggestions

        if result.quality_score.maintainability_index < 70:
            suggestions.append("🔴 Reduce complexity by breaking functions into smaller pieces")

        if result.quality_score.test_coverage < 70:
            suggestions.append("🟡 Increase test coverage to at least 80% (currently {:.0f}%)".format(result.quality_score.test_coverage))

        if result.quality_score.reliability_score < 80:
            suggestions.append("🟠 Add more comprehensive unit tests for edge cases")

        # Issue-specific suggestions
        issue_types = {}
        for issue in result.issues:
            issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1

        if IssueType.HIGH_COMPLEXITY in issue_types:
            suggestions.append(f"⚠️  {issue_types[IssueType.HIGH_COMPLEXITY]} functions have high complexity")

        if IssueType.LONG_METHOD in issue_types:
            suggestions.append(f"⚠️  {issue_types[IssueType.LONG_METHOD]} functions are too long")

        if IssueType.DUPLICATE_CODE in issue_types:
            suggestions.append("🔄 Refactor duplicate code into reusable components")

        return suggestions

    def generate_report(self, analysis_id: str) -> str:
        """Generate detailed quality report"""
        result = self.analysis_results.get(analysis_id)
        if not result or not result.quality_score:
            return f"❌ Analysis {analysis_id} not found"

        score = result.quality_score
        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                        CODE QUALITY REPORT                                 ║
║                        Analysis ID: {analysis_id}                                 ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 OVERALL QUALITY: {score.overall_score:.1f}/100  [{score.grade}]
├─ 🏗️  Maintainability: {score.maintainability_index:.1f}/100
├─ ✅ Reliability: {score.reliability_score:.1f}/100
├─ 🔒 Security: {score.security_score:.1f}/100
└─ ⚡ Performance: {score.performance_score:.1f}/100

📈 METRICS:
├─ Files Analyzed: {len(result.files_analyzed)}
├─ Test Coverage: {score.test_coverage:.1f}%
├─ Technical Debt: {score.technical_debt_hours:.0f} hours
└─ Issues Found: {len(result.issues)}

🐛 TOP ISSUES:
"""

        # Group issues by severity
        issues_by_severity = {}
        for issue in result.issues:
            if issue.severity not in issues_by_severity:
                issues_by_severity[issue.severity] = []
            issues_by_severity[issue.severity].append(issue)

        for severity in ["CRITICAL", "MAJOR", "MINOR"]:
            if severity in issues_by_severity:
                emoji = "🔴" if severity == "CRITICAL" else "🟠" if severity == "MAJOR" else "🟡"
                issues = issues_by_severity[severity][:3]
                report += f"\n{emoji} {severity} ({len(issues_by_severity[severity])}):\n"
                for issue in issues:
                    report += f"  • {issue.issue_type.value} (L{issue.line_number})\n"
                    report += f"    {issue.description}\n"
                    report += f"    💡 {issue.suggestion}\n"

        # Suggestions
        report += f"\n💭 IMPROVEMENT SUGGESTIONS:\n"
        for suggestion in result.improvement_suggestions:
            report += f"  {suggestion}\n"

        return report

    def export_analysis(self, analysis_id: str) -> str:
        """Export analysis to JSON"""
        result = self.analysis_results.get(analysis_id)
        if not result:
            return "{}"

        export_data = {
            "analysis_id": result.analysis_id,
            "timestamp": result.timestamp,
            "quality_score": {
                "overall": result.quality_score.overall_score,
                "grade": result.quality_score.grade,
                "maintainability": result.quality_score.maintainability_index,
                "reliability": result.quality_score.reliability_score,
                "security": result.quality_score.security_score,
                "performance": result.quality_score.performance_score,
                "test_coverage": result.quality_score.test_coverage,
                "technical_debt_hours": result.quality_score.technical_debt_hours,
            },
            "issues_summary": {
                "total": len(result.issues),
                "critical": sum(1 for i in result.issues if i.severity == "CRITICAL"),
                "major": sum(1 for i in result.issues if i.severity == "MAJOR"),
                "minor": sum(1 for i in result.issues if i.severity == "MINOR"),
            },
            "top_issues": [
                {
                    "type": i.issue_type.value,
                    "severity": i.severity,
                    "file": i.file_path,
                    "line": i.line_number,
                    "description": i.description,
                }
                for i in result.issues[:10]
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔍 Code Quality Analyzer - Comprehensive Code Assessment")
    print("=" * 70)

    analyzer = CodeQualityAnalyzer()

    # Sample code files
    sample_code = {
        "main.py": """
def process_data(a, b, c, d, e):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        result = a + b + c + d + e
                    else:
                        result = a + b + c + d
                else:
                    result = a + b + c
            else:
                result = a + b
        else:
            result = a
    return result * 42

x = 100
y = 256
z = 1000
""",
        "utils.py": """
def helper_one():
    data = []
    for i in range(10):
        data.append(i * 2)
    return data

def helper_two():
    data = []
    for i in range(10):
        data.append(i * 2)
    return data
""",
    }

    print("\n🔬 Analyzing code quality...")
    result = analyzer.analyze_code(
        sample_code,
        test_coverage={"main.py": 65, "utils.py": 45}
    )

    # Print report
    print(analyzer.generate_report(result.analysis_id))

    # Export
    print("\n📄 Exporting analysis results...")
    json_export = analyzer.export_analysis(result.analysis_id)
    print(f"✅ Exported {len(json_export)} characters of analysis data")

    print("\n" + "=" * 70)
    print("✨ Code quality analysis complete")


if __name__ == "__main__":
    main()

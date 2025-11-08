"""
performance_analyzer.py
----------------------
Real-time performance analyzer that watches logs and generates reports.
Helps identify bottlenecks by analyzing timing patterns.

Usage:
    python performance_analyzer.py
    
Then use the app normally. The analyzer will track all operations and
generate a summary report.
"""

import re
import sys
from collections import defaultdict
from datetime import datetime

class PerformanceAnalyzer:
    def __init__(self):
        self.operations = defaultdict(list)
        self.route_totals = defaultdict(list)
        self.api_calls = defaultdict(list)
        
    def parse_log_line(self, line):
        """Parse a log line and extract timing information."""
        # Match timing pattern: "operation - XXX.XXms"
        timing_match = re.search(r'(.+?)\s*-\s*(\d+\.\d+)ms', line)
        if not timing_match:
            return None
            
        operation = timing_match.group(1).strip()
        time_ms = float(timing_match.group(2))
        
        # Extract timestamp
        timestamp_match = re.match(r'(\d{2}:\d{2}:\d{2}\.\d{3})', line)
        timestamp = timestamp_match.group(1) if timestamp_match else None
        
        return {
            'operation': operation,
            'time_ms': time_ms,
            'timestamp': timestamp,
            'line': line
        }
    
    def categorize_operation(self, operation):
        """Categorize the operation type."""
        if 'route - TOTAL' in operation:
            return 'route_total'
        elif 'API:' in operation:
            return 'api_call'
        else:
            return 'sub_operation'
    
    def add_measurement(self, data):
        """Add a timing measurement."""
        operation = data['operation']
        time_ms = data['time_ms']
        category = self.categorize_operation(operation)
        
        if category == 'route_total':
            route_name = operation.split(':')[1].split('route')[0].strip()
            self.route_totals[route_name].append(time_ms)
        elif category == 'api_call':
            api_operation = operation.split('API:')[1].strip()
            self.api_calls[api_operation].append(time_ms)
        else:
            self.operations[operation].append(time_ms)
    
    def calculate_stats(self, times):
        """Calculate statistics for a list of times."""
        if not times:
            return None
        
        return {
            'count': len(times),
            'min': min(times),
            'max': max(times),
            'avg': sum(times) / len(times),
            'total': sum(times)
        }
    
    def get_performance_rating(self, avg_time, operation_type='general'):
        """Get performance rating based on average time."""
        thresholds = {
            'api_call': {'excellent': 100, 'good': 200, 'acceptable': 300},
            'route_total': {'excellent': 200, 'good': 400, 'acceptable': 600},
            'cached': {'excellent': 5, 'good': 10, 'acceptable': 20},
            'general': {'excellent': 50, 'good': 100, 'acceptable': 200}
        }
        
        t = thresholds.get(operation_type, thresholds['general'])
        
        if avg_time < t['excellent']:
            return '🚀 Excellent'
        elif avg_time < t['good']:
            return '✅ Good'
        elif avg_time < t['acceptable']:
            return '⚠️  Acceptable'
        else:
            return '❌ Slow'
    
    def generate_report(self):
        """Generate a comprehensive performance report."""
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE ANALYSIS REPORT")
        print("=" * 80)
        
        # Route Totals
        if self.route_totals:
            print("\n🎯 Route Performance (End-to-End):")
            print("-" * 80)
            for route, times in sorted(self.route_totals.items()):
                stats = self.calculate_stats(times)
                rating = self.get_performance_rating(stats['avg'], 'route_total')
                print(f"\n   {route}")
                print(f"   {rating}")
                print(f"   Calls: {stats['count']:3d} | Avg: {stats['avg']:7.2f}ms | "
                      f"Min: {stats['min']:7.2f}ms | Max: {stats['max']:7.2f}ms")
        
        # API Calls
        if self.api_calls:
            print("\n\n🔹 API Call Performance:")
            print("-" * 80)
            for api_call, times in sorted(self.api_calls.items()):
                stats = self.calculate_stats(times)
                
                # Detect if cached
                is_cached = 'cached' in api_call.lower() or stats['avg'] < 10
                op_type = 'cached' if is_cached else 'api_call'
                rating = self.get_performance_rating(stats['avg'], op_type)
                
                print(f"\n   {api_call}")
                print(f"   {rating}")
                print(f"   Calls: {stats['count']:3d} | Avg: {stats['avg']:7.2f}ms | "
                      f"Min: {stats['min']:7.2f}ms | Max: {stats['max']:7.2f}ms")
        
        # Sub-operations
        if self.operations:
            print("\n\n⚙️  Sub-Operation Performance:")
            print("-" * 80)
            for operation, times in sorted(self.operations.items()):
                stats = self.calculate_stats(times)
                rating = self.get_performance_rating(stats['avg'], 'general')
                print(f"\n   {operation}")
                print(f"   {rating}")
                print(f"   Calls: {stats['count']:3d} | Avg: {stats['avg']:7.2f}ms | "
                      f"Min: {stats['min']:7.2f}ms | Max: {stats['max']:7.2f}ms")
        
        # Top Bottlenecks
        print("\n\n🔥 Top Performance Bottlenecks:")
        print("-" * 80)
        
        all_operations = []
        
        for route, times in self.route_totals.items():
            stats = self.calculate_stats(times)
            all_operations.append(('Route: ' + route, stats))
        
        for api_call, times in self.api_calls.items():
            stats = self.calculate_stats(times)
            all_operations.append(('API: ' + api_call, stats))
        
        # Sort by average time (descending)
        all_operations.sort(key=lambda x: x[1]['avg'], reverse=True)
        
        print("\n   Slowest Operations (by average time):")
        for i, (name, stats) in enumerate(all_operations[:10], 1):
            rating_emoji = '🚀' if stats['avg'] < 100 else '✅' if stats['avg'] < 200 else '⚠️ ' if stats['avg'] < 400 else '❌'
            print(f"   {i:2d}. {rating_emoji} {name:50s} {stats['avg']:7.2f}ms (n={stats['count']})")
        
        # Summary
        print("\n\n📈 Performance Summary:")
        print("-" * 80)
        
        total_calls = sum(len(times) for times in self.api_calls.values())
        if total_calls > 0:
            avg_api_time = sum(sum(times) for times in self.api_calls.values()) / total_calls
            print(f"   Total API Calls: {total_calls}")
            print(f"   Average API Time: {avg_api_time:.2f}ms")
            
            # Cache effectiveness
            cached_calls = sum(len(times) for name, times in self.api_calls.items() 
                             if self.calculate_stats(times)['avg'] < 10)
            cache_ratio = (cached_calls / total_calls * 100) if total_calls > 0 else 0
            print(f"   Cached Calls: {cached_calls} ({cache_ratio:.1f}%)")
            
            if cache_ratio > 50:
                print("   Cache Status: ✅ Working well")
            elif cache_ratio > 20:
                print("   Cache Status: ⚠️  Partially working")
            else:
                print("   Cache Status: ❌ Not working effectively")
        
        total_routes = sum(len(times) for times in self.route_totals.values())
        if total_routes > 0:
            avg_route_time = sum(sum(times) for times in self.route_totals.values()) / total_routes
            print(f"\n   Total Route Calls: {total_routes}")
            print(f"   Average Route Time: {avg_route_time:.2f}ms")
            
            if avg_route_time < 200:
                print("   Overall Rating: 🚀 Excellent")
            elif avg_route_time < 400:
                print("   Overall Rating: ✅ Good")
            elif avg_route_time < 600:
                print("   Overall Rating: ⚠️  Acceptable")
            else:
                print("   Overall Rating: ❌ Needs Optimization")
        
        print("\n" + "=" * 80)
        print("💡 Tip: Operations > 200ms should be optimized")
        print("=" * 80 + "\n")


def main():
    """Main function to run the analyzer."""
    print("🔍 Performance Analyzer - Monitoring logs...")
    print("Use the app normally. Press Ctrl+C when done to see the report.\n")
    print("Watching for timing data...\n")
    
    analyzer = PerformanceAnalyzer()
    line_count = 0
    
    try:
        for line in sys.stdin:
            line = line.strip()
            
            # Parse the line
            data = analyzer.parse_log_line(line)
            if data:
                analyzer.add_measurement(data)
                line_count += 1
                
                # Show live feedback
                if '✅' in line or '❌' in line:
                    print(line)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped. Generating report...\n")
    
    if line_count > 0:
        analyzer.generate_report()
    else:
        print("No timing data collected. Make sure the app is running with logging enabled.")


if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                    Performance Analyzer v1.0                          ║
    ║                                                                       ║
    ║  This tool monitors your Flask app logs and generates a detailed     ║
    ║  performance report showing bottlenecks and optimization targets.    ║
    ║                                                                       ║
    ║  Usage:                                                               ║
    ║    python app.py 2>&1 | python performance_analyzer.py              ║
    ║                                                                       ║
    ║  Then use your app normally. Press Ctrl+C when done to see report.   ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """)
    main()

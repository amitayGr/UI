#!/usr/bin/env python3
"""
performance_test.py
------------------
Performance testing and benchmarking script for the API integration.
Tests response times, caching effectiveness, and overall system performance.

Usage:
    python performance_test.py
"""

import time
from api_client import api_client
import statistics

print("⚡ API Performance Testing Suite")
print("=" * 70)

def measure_time(func, *args, **kwargs):
    """Measure execution time of a function."""
    start = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        return elapsed, True, result
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return elapsed, False, str(e)

def run_benchmark(name, func, runs=3, *args, **kwargs):
    """Run a benchmark multiple times and report statistics."""
    times = []
    success_count = 0
    
    print(f"\n📊 Testing: {name}")
    print("-" * 70)
    
    for i in range(runs):
        elapsed, success, result = measure_time(func, *args, **kwargs)
        times.append(elapsed)
        if success:
            success_count += 1
        status = "✅" if success else "❌"
        print(f"   Run {i+1}: {elapsed:7.2f}ms {status}")
    
    if times:
        avg = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n   Average: {avg:7.2f}ms")
        print(f"   Min:     {min_time:7.2f}ms")
        print(f"   Max:     {max_time:7.2f}ms")
        print(f"   Success: {success_count}/{runs}")
        
        # Performance rating
        if avg < 100:
            rating = "🚀 Excellent"
        elif avg < 300:
            rating = "✅ Good"
        elif avg < 500:
            rating = "⚠️  Acceptable"
        else:
            rating = "❌ Slow"
        print(f"   Rating:  {rating}")
        
        return avg
    return None

# Clear cache before testing
print("\n🧹 Clearing cache for clean test...")
api_client.clear_cache()

# Test 1: Health Check
print("\n" + "=" * 70)
print("Test 1: Health Check (lightest endpoint)")
print("=" * 70)
health_time = run_benchmark("Health Check", api_client.health_check, runs=5)

# Test 2: Session Operations
print("\n" + "=" * 70)
print("Test 2: Session Operations")
print("=" * 70)

print("\n📝 Session Start")
session_start_time = run_benchmark("Session Start", api_client.start_session, runs=3)

print("\n📝 Session Status")
status_time = run_benchmark("Session Status", api_client.get_session_status, runs=3)

# Clean up session
try:
    api_client.end_session(save_to_db=False)
except:
    pass

# Test 3: Static Data (Cache Effectiveness)
print("\n" + "=" * 70)
print("Test 3: Cache Effectiveness (Static Data)")
print("=" * 70)

# Clear cache and test uncached
api_client.clear_cache()
print("\n🔥 First Call (Uncached):")
uncached_time = run_benchmark("Answer Options (uncached)", 
                              api_client.get_answer_options, runs=1)

print("\n⚡ Subsequent Calls (Cached):")
cached_time = run_benchmark("Answer Options (cached)", 
                           api_client.get_answer_options, runs=5)

if uncached_time and cached_time:
    improvement = ((uncached_time - cached_time) / uncached_time) * 100
    print(f"\n   Cache Improvement: {improvement:.1f}% faster")
    print(f"   Speed-up: {uncached_time/cached_time:.1f}x")

print("\n" + "=" * 70)
print("Test 4: Question Flow (Legacy vs Batched)")
print("=" * 70)

legacy_first_q_time = legacy_submit_time = legacy_next_q_time = None
bootstrap_time = enhanced_submit_time = None

try:
    # Legacy flow
    api_client.start_session()
    print("\n📝 Legacy First Question")
    legacy_first_q_time = run_benchmark("Legacy Get First Question", api_client.get_first_question, runs=3)
    print("\n📝 Legacy Submit Answer")
    legacy_submit_time = run_benchmark("Legacy Submit Answer", api_client.submit_answer, runs=3, question_id=1, answer_id=1)
    print("\n📝 Legacy Next Question")
    legacy_next_q_time = run_benchmark("Legacy Get Next Question", api_client.get_next_question, runs=3)
    api_client.end_session(save_to_db=False)
except Exception as e:
    print(f"   ⚠️ Legacy workflow failed: {e}")

try:
    # Batched flow using bootstrap + enhanced submit
    print("\n🧪 Bootstrap Initial (Batched)")
    bootstrap_time = run_benchmark("Bootstrap Initial", api_client.bootstrap_initial, runs=3)
    payload = api_client.bootstrap_initial()
    q_id_for_submit = payload.get('first_question', {}).get('question_id', 1)
    print("\n🧪 Enhanced Submit (Batched)")
    enhanced_submit_time = run_benchmark(
        "Submit Answer (enhanced)",
        api_client.submit_answer_enhanced,
        runs=3,
        question_id=q_id_for_submit,
        answer_id=1,
        include_next_question=True,
        include_answer_options=True
    )
    api_client.end_session(save_to_db=False)
except Exception as e:
    print(f"   ⚠️ Batched workflow failed: {e}")

# Test 5: Theorems (Larger Dataset)
print("\n" + "=" * 70)
print("Test 5: Large Data Retrieval (Theorems)")
print("=" * 70)

api_client.clear_cache()
print("\n🔥 Uncached:")
theorems_uncached = run_benchmark("Get All Theorems (uncached)", 
                                 api_client.get_all_theorems, runs=1)

print("\n⚡ Cached:")
theorems_cached = run_benchmark("Get All Theorems (cached)", 
                               api_client.get_all_theorems, runs=5)

# Test 6: Concurrent Requests Simulation
print("\n" + "=" * 70)
print("Test 6: Rapid Sequential Requests")
print("=" * 70)

import threading

def rapid_fire_test(iterations=10):
    """Test rapid sequential requests."""
    times = []
    start_total = time.time()
    
    for i in range(iterations):
        start = time.time()
        try:
            api_client.get_answer_options()  # Cached, should be fast
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
        except Exception as e:
            print(f"   ❌ Request {i+1} failed: {e}")
    
    total_time = (time.time() - start_total) * 1000
    
    if times:
        avg = statistics.mean(times)
        print(f"\n   Total Requests: {len(times)}")
        print(f"   Total Time:     {total_time:.2f}ms")
        print(f"   Average/Request: {avg:.2f}ms")
        print(f"   Throughput:     {len(times) / (total_time/1000):.2f} req/sec")
    
    return avg if times else None

rapid_time = rapid_fire_test(20)

# Summary Report
print("\n" + "=" * 70)
print("📊 PERFORMANCE SUMMARY")
print("=" * 70)

results = {
    "Health Check": health_time,
    "Session Start": session_start_time,
    "Session Status": status_time,
    "Legacy First Question": legacy_first_q_time,
    "Legacy Submit Answer": legacy_submit_time,
    "Legacy Next Question": legacy_next_q_time,
    "Bootstrap Initial": bootstrap_time,
    "Enhanced Submit": enhanced_submit_time,
    "Theorems (cached)": theorems_cached,
    "Rapid Fire (avg)": rapid_time,
}

print("\n Response Times:")
print("-" * 70)
for name, time_ms in results.items():
    if time_ms:
        if time_ms < 100:
            status = "🚀"
        elif time_ms < 300:
            status = "✅"
        elif time_ms < 500:
            status = "⚠️ "
        else:
            status = "❌"
        print(f"   {status} {name:25s}: {time_ms:7.2f}ms")

# Cache Effectiveness
print("\n Cache Performance:")
print("-" * 70)
if uncached_time and cached_time:
    print(f"   Uncached Request:  {uncached_time:7.2f}ms")
    print(f"   Cached Request:    {cached_time:7.2f}ms")
    print(f"   Speed Improvement: {uncached_time/cached_time:.1f}x faster")
    print(f"   Time Saved:        {uncached_time - cached_time:.2f}ms per request")

# Overall Assessment
print("\n Overall Assessment:")
print("-" * 70)

avg_times = [t for t in results.values() if t is not None]
if avg_times:
    overall_avg = statistics.mean(avg_times)
    
    if overall_avg < 150:
        grade = "A+ (Excellent)"
        emoji = "🏆"
    elif overall_avg < 250:
        grade = "A  (Very Good)"
        emoji = "🌟"
    elif overall_avg < 350:
        grade = "B  (Good)"
        emoji = "✅"
    elif overall_avg < 500:
        grade = "C  (Acceptable)"
        emoji = "⚠️ "
    else:
        grade = "D  (Needs Improvement)"
        emoji = "❌"
    
    print(f"   {emoji} Performance Grade: {grade}")
    print(f"   Average Response Time: {overall_avg:.2f}ms")

# Recommendations
print("\n Recommendations:")
print("-" * 70)

recommendations = []

if health_time and health_time > 100:
    recommendations.append("⚠️  High health check latency - check network/API server")

if cached_time and cached_time > 10:
    recommendations.append("⚠️  Cache overhead detected - consider optimizing cache implementation")

if uncached_time and uncached_time > 1000:
    recommendations.append("⚠️  Slow API responses - optimize API server database queries")

if rapid_time and rapid_time > 50:
    recommendations.append("⚠️  High rapid-fire latency - ensure connection pooling is active")

if not recommendations:
    print("   ✅ All metrics are within acceptable ranges!")
    print("   ✅ No immediate optimizations needed")
else:
    for rec in recommendations:
        print(f"   {rec}")

print("\n" + "=" * 70)
print("Performance testing complete! See PERFORMANCE_OPTIMIZATION.md for more details.")
print("=" * 70)

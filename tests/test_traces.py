"""Test the trace system functionality."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.traces.service import (
    get_all_traces,
    get_user_timeline,
    get_trace_by_id,
    get_trace_stats,
    TRACE_TYPE_CHAT,
    TRACE_TYPE_RECOMMENDATION,
    TRACE_TYPE_OVERRIDE,
    TRACE_TYPE_FLAG,
    TRACE_TYPE_PERSONA,
    TRACE_TYPE_FEATURES
)
from src.database.db import get_all_chat_logs, get_recommendation_traces, get_timeline_events
import json

def test_trace_service():
    """Test the trace service module."""
    print("\n" + "="*60)
    print("TESTING TRACE SERVICE")
    print("="*60)
    
    # Test 1: Get all traces
    print("\n1. Testing get_all_traces()...")
    try:
        result = get_all_traces(limit=10, offset=0)
        print(f"   ✓ Retrieved {len(result['traces'])} traces")
        print(f"   ✓ Total traces: {result['total']}")
        print(f"   ✓ Has more: {result['has_more']}")
        
        if result['traces']:
            first_trace = result['traces'][0]
            print(f"   ✓ First trace type: {first_trace['trace_type']}")
            print(f"   ✓ First trace user: {first_trace['user_id']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 2: Filter by trace type
    print("\n2. Testing trace type filtering...")
    trace_types_to_test = [
        TRACE_TYPE_CHAT,
        TRACE_TYPE_RECOMMENDATION,
        TRACE_TYPE_PERSONA
    ]
    
    for trace_type in trace_types_to_test:
        try:
            result = get_all_traces(trace_types=[trace_type], limit=5)
            matching = all(t['trace_type'] == trace_type for t in result['traces'])
            if matching or len(result['traces']) == 0:
                print(f"   ✓ {trace_type}: {len(result['traces'])} traces")
            else:
                print(f"   ✗ {trace_type}: filtering failed")
                return False
        except Exception as e:
            print(f"   ✗ {trace_type}: Error - {e}")
    
    # Test 3: Get user timeline
    print("\n3. Testing get_user_timeline()...")
    try:
        # Get a user_id from the first trace
        all_result = get_all_traces(limit=1)
        if all_result['traces']:
            test_user_id = all_result['traces'][0]['user_id']
            timeline = get_user_timeline(test_user_id)
            print(f"   ✓ Retrieved timeline for user {test_user_id}")
            print(f"   ✓ Timeline has {len(timeline)} events")
            
            # Verify chronological ordering
            if len(timeline) > 1:
                timestamps = [t['timestamp'] for t in timeline if t['timestamp']]
                is_sorted = all(timestamps[i] >= timestamps[i+1] for i in range(len(timestamps)-1))
                if is_sorted:
                    print("   ✓ Timeline is properly sorted (most recent first)")
                else:
                    print("   ✗ Timeline sorting failed")
                    return False
        else:
            print("   ! No traces available to test timeline")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 4: Get trace by ID
    print("\n4. Testing get_trace_by_id()...")
    try:
        all_result = get_all_traces(limit=1)
        if all_result['traces']:
            trace_id = all_result['traces'][0]['trace_id']
            trace = get_trace_by_id(trace_id)
            if trace:
                print(f"   ✓ Retrieved trace {trace_id}")
                print(f"   ✓ Trace type: {trace['trace_type']}")
            else:
                print(f"   ✗ Failed to retrieve trace {trace_id}")
                return False
        else:
            print("   ! No traces available to test")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 5: Get trace stats
    print("\n5. Testing get_trace_stats()...")
    try:
        stats = get_trace_stats()
        print(f"   ✓ Total traces: {stats['total']}")
        print(f"   ✓ Last 24h: {stats['last_24h']}")
        print(f"   ✓ Last 7d: {stats['last_7d']}")
        print(f"   ✓ Last 30d: {stats['last_30d']}")
        print(f"   ✓ By type: {json.dumps(stats['by_type'], indent=2)}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 6: Test pagination
    print("\n6. Testing pagination...")
    try:
        page1 = get_all_traces(limit=5, offset=0)
        page2 = get_all_traces(limit=5, offset=5)
        
        if page1['traces'] and page2['traces']:
            # Check that pages don't overlap
            page1_ids = set(t['trace_id'] for t in page1['traces'])
            page2_ids = set(t['trace_id'] for t in page2['traces'])
            overlap = page1_ids & page2_ids
            
            if not overlap:
                print(f"   ✓ Page 1: {len(page1['traces'])} traces")
                print(f"   ✓ Page 2: {len(page2['traces'])} traces")
                print("   ✓ No overlap between pages")
            else:
                print(f"   ✗ Pages overlap: {overlap}")
                return False
        else:
            print("   ! Not enough traces to test pagination")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 7: Test search
    print("\n7. Testing search functionality...")
    try:
        # Search for common terms
        search_terms = ["user", "credit", "persona"]
        for term in search_terms:
            result = get_all_traces(search_query=term, limit=5)
            print(f"   ✓ Search '{term}': {len(result['traces'])} results")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 8: Test date filtering
    print("\n8. Testing date filtering...")
    try:
        from datetime import datetime, timedelta
        today = datetime.now().date().isoformat()
        week_ago = (datetime.now().date() - timedelta(days=7)).isoformat()
        
        result = get_all_traces(start_date=week_ago, limit=10)
        print(f"   ✓ Traces since {week_ago}: {len(result['traces'])}")
        
        # Verify dates are within range
        if result['traces']:
            for trace in result['traces']:
                if trace['timestamp'] and trace['timestamp'] < week_ago:
                    print(f"   ✗ Date filtering failed: {trace['timestamp']} < {week_ago}")
                    return False
            print("   ✓ All traces are within date range")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED ✓")
    print("="*60)
    return True


def test_database_helpers():
    """Test the database helper functions."""
    print("\n" + "="*60)
    print("TESTING DATABASE HELPERS")
    print("="*60)
    
    # Test get_all_chat_logs
    print("\n1. Testing get_all_chat_logs()...")
    try:
        logs = get_all_chat_logs(limit=5)
        print(f"   ✓ Retrieved {len(logs)} chat logs")
        if logs:
            print(f"   ✓ First log user: {logs[0].get('user_id')}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test get_recommendation_traces
    print("\n2. Testing get_recommendation_traces()...")
    try:
        recs = get_recommendation_traces(limit=5)
        print(f"   ✓ Retrieved {len(recs)} recommendations")
        if recs:
            print(f"   ✓ First rec user: {recs[0].get('user_id')}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test get_timeline_events
    print("\n3. Testing get_timeline_events()...")
    try:
        # Get a user_id
        logs = get_all_chat_logs(limit=1)
        if logs:
            user_id = logs[0]['user_id']
            events = get_timeline_events(user_id)
            print(f"   ✓ Retrieved timeline for user {user_id}")
            print(f"   ✓ Chat logs: {len(events.get('chat_logs', []))}")
            print(f"   ✓ Recommendations: {len(events.get('recommendations', []))}")
            print(f"   ✓ Operator actions: {len(events.get('operator_actions', []))}")
        else:
            print("   ! No users available to test")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print("\n" + "="*60)
    print("DATABASE HELPER TESTS PASSED ✓")
    print("="*60)
    return True


def test_trace_formatting():
    """Test trace formatting and structure."""
    print("\n" + "="*60)
    print("TESTING TRACE FORMATTING")
    print("="*60)
    
    try:
        result = get_all_traces(limit=10)
        
        if not result['traces']:
            print("   ! No traces available to test formatting")
            return True
        
        print(f"\n1. Testing trace structure...")
        required_fields = ['trace_id', 'trace_type', 'user_id', 'timestamp', 'summary', 'details']
        
        for i, trace in enumerate(result['traces'][:3], 1):
            print(f"\n   Trace {i} ({trace['trace_type']}):")
            for field in required_fields:
                if field in trace:
                    print(f"      ✓ {field}: present")
                else:
                    print(f"      ✗ {field}: MISSING")
                    return False
            
            # Check details structure
            if 'details' in trace and isinstance(trace['details'], dict):
                print(f"      ✓ details: {len(trace['details'])} fields")
            else:
                print("      ✗ details: invalid structure")
                return False
        
        print("\n2. Testing trace ID format...")
        for trace in result['traces'][:5]:
            trace_id = trace['trace_id']
            if '_' in trace_id:
                prefix, suffix = trace_id.split('_', 1)
                print(f"   ✓ {trace_id}: valid format ({prefix}_...)")
            else:
                print(f"   ✗ {trace_id}: invalid format")
                return False
        
        print("\n3. Testing timestamp format...")
        for trace in result['traces'][:5]:
            if trace['timestamp']:
                # Try parsing ISO format
                from datetime import datetime
                try:
                    datetime.fromisoformat(trace['timestamp'].replace('Z', '+00:00'))
                    print(f"   ✓ {trace['timestamp']}: valid ISO format")
                except:
                    print(f"   ✗ {trace['timestamp']}: invalid format")
                    return False
            else:
                print(f"   ! Trace {trace['trace_id']}: no timestamp")
        
        print("\n" + "="*60)
        print("FORMATTING TESTS PASSED ✓")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("TRACE SYSTEM TEST SUITE")
    print("="*60)
    
    all_passed = True
    
    # Run all test suites
    if not test_database_helpers():
        all_passed = False
    
    if not test_trace_service():
        all_passed = False
    
    if not test_trace_formatting():
        all_passed = False
    
    # Final summary
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TEST SUITES PASSED")
        print("="*60)
        print("\nThe trace system is working correctly!")
        print("\nYou can now:")
        print("  1. Start the API: uvicorn src.api.main:app --reload")
        print("  2. Open operator_ui/templates/decision_traces.html")
        print("  3. Open operator_ui/templates/user_detail.html?user_id=<user_id>")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        print("="*60)
        sys.exit(1)








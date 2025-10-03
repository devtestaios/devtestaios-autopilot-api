#!/usr/bin/env python3
"""
Database Connectivity Test Script
Comprehensive verification of all database connections
Date: October 3, 2025
"""

import os
import sys
from typing import Dict, Any

def test_supabase_connection():
    """Test direct Supabase connection"""
    try:
        from supabase import create_client
        
        # Get environment variables
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            return {
                'status': 'error',
                'message': 'Missing Supabase credentials',
                'url_exists': bool(url),
                'key_exists': bool(key)
            }
        
        # Create client
        supabase = create_client(url, key)
        
        # Test basic query - count tables
        result = supabase.rpc('execute_sql', {
            'sql_query': "SELECT COUNT(*) as table_count FROM pg_tables WHERE schemaname = 'public';"
        })
        
        if result and result.data:
            table_count = result.data[0].get('table_count', 0)
            return {
                'status': 'connected',
                'message': f'Successfully connected to Supabase',
                'table_count': table_count,
                'connection_method': 'direct_supabase_client'
            }
        else:
            return {
                'status': 'error',
                'message': 'Connected but could not query tables',
                'result': str(result)
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Supabase connection failed: {str(e)}',
            'error_type': type(e).__name__
        }

def test_table_access():
    """Test access to specific AI tables"""
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            return {'status': 'error', 'message': 'Missing credentials'}
        
        supabase = create_client(url, key)
        
        # Test specific table queries
        tables_to_test = [
            'campaigns',
            'master_ai_cycles', 
            'ai_decision_logs',
            'email_campaigns'
        ]
        
        results = {}
        for table in tables_to_test:
            try:
                # Try to count rows in each table
                result = supabase.table(table).select('id', count='exact').limit(1).execute()
                results[table] = {
                    'accessible': True,
                    'count': getattr(result, 'count', 'unknown'),
                    'has_data': len(result.data) > 0 if result.data else False
                }
            except Exception as e:
                results[table] = {
                    'accessible': False,
                    'error': str(e)
                }
        
        return {
            'status': 'tested',
            'table_results': results
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Table access test failed: {str(e)}'
        }

def main():
    """Run comprehensive database connectivity tests"""
    print("🔍 COMPREHENSIVE DATABASE CONNECTIVITY TEST")
    print("=" * 50)
    
    # Test 1: Environment Variables
    print("\n1. 📋 Environment Variables Check:")
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    print(f"   SUPABASE_URL: {'✅ Present' if url else '❌ Missing'}")
    print(f"   SUPABASE_KEY: {'✅ Present' if key else '❌ Missing'}")
    
    if url:
        print(f"   URL starts with: {url[:20]}...")
    if key:
        print(f"   Key starts with: {key[:20]}...")
    
    # Test 2: Supabase Connection
    print("\n2. 🔗 Supabase Connection Test:")
    connection_result = test_supabase_connection()
    if connection_result['status'] == 'connected':
        print(f"   ✅ {connection_result['message']}")
        print(f"   📊 Tables found: {connection_result.get('table_count', 'unknown')}")
    else:
        print(f"   ❌ {connection_result['message']}")
        if 'error_type' in connection_result:
            print(f"   🔍 Error type: {connection_result['error_type']}")
    
    # Test 3: Table Access
    print("\n3. 📊 Table Access Test:")
    table_result = test_table_access()
    if table_result['status'] == 'tested':
        for table, result in table_result['table_results'].items():
            if result['accessible']:
                print(f"   ✅ {table}: Accessible (count: {result.get('count', 'unknown')})")
            else:
                print(f"   ❌ {table}: {result.get('error', 'Unknown error')}")
    else:
        print(f"   ❌ {table_result['message']}")
    
    # Summary
    print("\n4. 📋 Connection Summary:")
    if connection_result['status'] == 'connected':
        accessible_tables = sum(1 for r in table_result.get('table_results', {}).values() if r.get('accessible'))
        total_tables = len(table_result.get('table_results', {}))
        
        if accessible_tables == total_tables:
            print("   🎉 DATABASE 100% CONNECTED!")
            print("   ✅ All core tables accessible")
            print("   ✅ AI system ready for operations")
        elif accessible_tables > 0:
            print(f"   🔄 PARTIAL CONNECTION: {accessible_tables}/{total_tables} tables accessible")
            print("   ⚠️  Some tables may need schema updates")
        else:
            print("   ❌ NO TABLE ACCESS")
            print("   🔧 Schema deployment needed")
    else:
        print("   ❌ NO DATABASE CONNECTION")
        print("   🔧 Check credentials and network")

if __name__ == "__main__":
    main()
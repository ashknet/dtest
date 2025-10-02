"""
Test Script for MAT GraphQL Pagination

This script tests both offset-based and cursor-based pagination
to determine which one your MAT API supports.

Usage:
    python test_pagination.py

Prerequisites:
    - pip install requests
    - Set environment variables:
      - MAT_GRAPHQL_ENDPOINT
      - MAT_API_TOKEN
    - Or update the configuration below
"""

import os
import sys
import json
import time
import requests
from typing import Dict, Any, Tuple


# ===================================================================
# CONFIGURATION - Update these values
# ===================================================================

CONFIG = {
    'endpoint': os.getenv('MAT_GRAPHQL_ENDPOINT', 'YOUR_MAT_GRAPHQL_ENDPOINT_HERE'),
    'token': os.getenv('MAT_API_TOKEN', 'YOUR_TOKEN_HERE'),
    'client_id': '0008005369',
    'fiscal_year': '2025',
    'test_page_size': 10  # Small page size for testing
}


# ===================================================================
# TEST QUERIES
# ===================================================================

OFFSET_TEST_QUERY = """
query TestOffsetPagination($clientId: String!, $fiscalYear: String!, $skip: Int!, $take: Int!) {
  clients(where:{clientId:{eq:$clientId}}) {
    clientName
    clientProfiles(where: {clientAuditYear:{eq: $fiscalYear}}) {
      clientAuditYear
      engagements(
        where: {
          isNoLongerPerforming : {eq: false}
          isDeleted : {eq: false}
          isTerminated : {eq: false}
          isInvalidated : {eq: false}
          engagementTypeId: { neq: 6 }
          serviceTypeId: { nin: [10, 11, 12] }
        }
        skip: $skip
        take: $take
      ) {
        engagementNumber
        engagementName
      }
    }
  }
}
"""

CURSOR_TEST_QUERY = """
query TestCursorPagination($clientId: String!, $fiscalYear: String!, $first: Int!, $after: String) {
  clients(where:{clientId:{eq:$clientId}}) {
    clientName
    clientProfiles(where: {clientAuditYear:{eq: $fiscalYear}}) {
      clientAuditYear
      engagements(
        where: {
          isNoLongerPerforming : {eq: false}
          isDeleted : {eq: false}
          isTerminated : {eq: false}
          isInvalidated : {eq: false}
          engagementTypeId: { neq: 6 }
          serviceTypeId: { nin: [10, 11, 12] }
        }
        first: $first
        after: $after
      ) {
        edges {
          node {
            engagementNumber
            engagementName
          }
          cursor
        }
        pageInfo {
          hasNextPage
          endCursor
        }
        totalCount
      }
    }
  }
}
"""


# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

def make_graphql_request(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Make a GraphQL request to MAT API."""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {CONFIG['token']}",
        }

        payload = {
            'query': query,
            'variables': variables
        }

        response = requests.post(
            CONFIG['endpoint'],
            json=payload,
            headers=headers
        )

        if not response.ok:
            raise Exception(f"HTTP {response.status_code}: {response.reason}\n{response.text}")

        result = response.json()

        if 'errors' in result:
            raise Exception(f"GraphQL errors: {json.dumps(result['errors'], indent=2)}")

        return result

    except Exception as e:
        raise Exception(f"Request failed: {str(e)}")


# ===================================================================
# TEST FUNCTIONS
# ===================================================================

def test_offset_pagination() -> Dict[str, Any]:
    """Test offset-based pagination."""
    print('\n' + '=' * 60)
    print('Testing OFFSET-BASED Pagination (skip/take)')
    print('=' * 60)

    try:
        variables = {
            'clientId': CONFIG['client_id'],
            'fiscalYear': CONFIG['fiscal_year'],
            'skip': 0,
            'take': CONFIG['test_page_size']
        }

        print(f'\nSending request with variables: {json.dumps(variables, indent=2)}')

        result = make_graphql_request(OFFSET_TEST_QUERY, variables)

        clients = result.get('data', {}).get('clients', [])
        if not clients:
            print('❌ No clients found')
            return {'supported': False, 'reason': 'No clients found'}

        client_name = clients[0].get('clientName')
        engagements = clients[0].get('clientProfiles', [{}])[0].get('engagements', [])

        print(f'\n✅ SUCCESS! Offset pagination is supported!')
        print(f'   Client: {client_name}')
        print(f'   Engagements returned: {len(engagements)}')
        print(f'   First engagement: {engagements[0].get("engagementNumber", "N/A") if engagements else "N/A"}')

        if engagements:
            print('\n   Sample engagements:')
            for idx, eng in enumerate(engagements[:3], 1):
                print(f'   {idx}. {eng.get("engagementNumber")} - {eng.get("engagementName")}')

        return {'supported': True, 'count': len(engagements)}

    except Exception as e:
        print(f'\n❌ FAILED: {str(e)}')
        return {'supported': False, 'reason': str(e)}


def test_cursor_pagination() -> Dict[str, Any]:
    """Test cursor-based pagination."""
    print('\n' + '=' * 60)
    print('Testing CURSOR-BASED Pagination (first/after/edges)')
    print('=' * 60)

    try:
        variables = {
            'clientId': CONFIG['client_id'],
            'fiscalYear': CONFIG['fiscal_year'],
            'first': CONFIG['test_page_size'],
            'after': None
        }

        print(f'\nSending request with variables: {json.dumps(variables, indent=2)}')

        result = make_graphql_request(CURSOR_TEST_QUERY, variables)

        clients = result.get('data', {}).get('clients', [])
        if not clients:
            print('❌ No clients found')
            return {'supported': False, 'reason': 'No clients found'}

        client_name = clients[0].get('clientName')
        engagements_connection = clients[0].get('clientProfiles', [{}])[0].get('engagements', {})
        edges = engagements_connection.get('edges', [])
        page_info = engagements_connection.get('pageInfo', {})
        total_count = engagements_connection.get('totalCount')

        print(f'\n✅ SUCCESS! Cursor pagination is supported!')
        print(f'   Client: {client_name}')
        print(f'   Engagements returned: {len(edges)}')
        print(f'   Total count: {total_count or "Not provided"}')
        print(f'   Has next page: {page_info.get("hasNextPage", False)}')
        print(f'   End cursor: {page_info.get("endCursor", "None")}')

        if edges:
            print('\n   Sample engagements:')
            for idx, edge in enumerate(edges[:3], 1):
                node = edge.get('node', {})
                print(f'   {idx}. {node.get("engagementNumber")} - {node.get("engagementName")}')

        return {
            'supported': True,
            'count': len(edges),
            'totalCount': total_count,
            'hasNextPage': page_info.get('hasNextPage'),
            'endCursor': page_info.get('endCursor')
        }

    except Exception as e:
        print(f'\n❌ FAILED: {str(e)}')
        return {'supported': False, 'reason': str(e)}


# ===================================================================
# MAIN TEST RUNNER
# ===================================================================

def run_tests():
    """Run all pagination tests."""
    print('\n' + '═' * 60)
    print('MAT GraphQL Pagination Support Test')
    print('═' * 60)
    print('\nConfiguration:')
    print(f"  Endpoint: {CONFIG['endpoint']}")
    print(f"  Client ID: {CONFIG['client_id']}")
    print(f"  Fiscal Year: {CONFIG['fiscal_year']}")
    print(f"  Test Page Size: {CONFIG['test_page_size']}")

    # Validate configuration
    if 'YOUR_' in CONFIG['endpoint'] or 'YOUR_' in CONFIG['token']:
        print('\n❌ ERROR: Please update the configuration with your actual values!')
        print('   Set MAT_GRAPHQL_ENDPOINT and MAT_API_TOKEN environment variables,')
        print('   or update the CONFIG dict in this script.')
        sys.exit(1)

    # Run tests
    offset_result = test_offset_pagination()
    time.sleep(1)  # Wait 1 second between tests
    cursor_result = test_cursor_pagination()

    # Summary
    print('\n' + '═' * 60)
    print('TEST SUMMARY')
    print('═' * 60)

    print('\nOffset-based (skip/take):')
    if offset_result['supported']:
        print(f"  ✅ SUPPORTED - Returned {offset_result['count']} engagements")
    else:
        print(f"  ❌ NOT SUPPORTED - {offset_result['reason']}")

    print('\nCursor-based (first/after/edges):')
    if cursor_result['supported']:
        print(f"  ✅ SUPPORTED - Returned {cursor_result['count']} engagements")
        if cursor_result.get('totalCount'):
            print(f"     Total available: {cursor_result['totalCount']}")
        if cursor_result.get('hasNextPage'):
            print(f"     Has more pages: Yes")
    else:
        print(f"  ❌ NOT SUPPORTED - {cursor_result['reason']}")

    # Recommendation
    print('\n' + '═' * 60)
    print('RECOMMENDATION')
    print('═' * 60)

    if cursor_result['supported'] and offset_result['supported']:
        print('\n✨ Both pagination methods are supported!')
        print('   RECOMMENDED: Use cursor-based pagination for better reliability.')
        print('   - Use the cursor-based implementation from pagination_implementation_examples.py')
    elif cursor_result['supported']:
        print('\n✨ Use cursor-based pagination!')
        print('   - Use the cursor-based implementation from pagination_implementation_examples.py')
    elif offset_result['supported']:
        print('\n✨ Use offset-based pagination!')
        print('   - Use the offset-based implementation from pagination_implementation_examples.py')
    else:
        print('\n⚠️  WARNING: Neither pagination method worked!')
        print('   This could be due to:')
        print('   1. Incorrect endpoint or token')
        print('   2. Different pagination syntax required by MAT API')
        print('   3. Network/permission issues')
        print('\n   Please check:')
        print('   - MAT API documentation for pagination syntax')
        print('   - Your credentials and permissions')
        print('   - Network connectivity to MAT API')

    print('\n' + '═' * 60)
    print('For implementation details, see:')
    print('  - QUICK_REFERENCE.md')
    print('  - pagination_implementation_examples.js')
    print('  - pagination_implementation_examples.py')
    print('═' * 60 + '\n')


# ===================================================================
# ENTRY POINT
# ===================================================================

if __name__ == '__main__':
    try:
        run_tests()
    except Exception as e:
        print(f'\n❌ Unexpected error: {e}')
        sys.exit(1)

/**
 * Test Script for MAT GraphQL Pagination
 * 
 * This script tests both offset-based and cursor-based pagination
 * to determine which one your MAT API supports.
 * 
 * Usage:
 *   node test_pagination.js
 * 
 * Prerequisites:
 *   - Set environment variables:
 *     - MAT_GRAPHQL_ENDPOINT
 *     - MAT_API_TOKEN
 *   - Or update the configuration below
 */

const fetch = require('node-fetch'); // Or use native fetch in Node 18+

// ===================================================================
// CONFIGURATION - Update these values
// ===================================================================

const CONFIG = {
  endpoint: process.env.MAT_GRAPHQL_ENDPOINT || 'YOUR_MAT_GRAPHQL_ENDPOINT_HERE',
  token: process.env.MAT_API_TOKEN || 'YOUR_TOKEN_HERE',
  clientId: '0008005369',
  fiscalYear: '2025',
  testPageSize: 10  // Small page size for testing
};

// ===================================================================
// TEST QUERIES
// ===================================================================

const OFFSET_TEST_QUERY = `
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
`;

const CURSOR_TEST_QUERY = `
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
`;

// ===================================================================
// HELPER FUNCTIONS
// ===================================================================

async function makeGraphQLRequest(query, variables) {
  try {
    const response = await fetch(CONFIG.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${CONFIG.token}`,
      },
      body: JSON.stringify({ query, variables })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();

    if (result.errors) {
      throw new Error(`GraphQL errors: ${JSON.stringify(result.errors, null, 2)}`);
    }

    return result;
  } catch (error) {
    throw new Error(`Request failed: ${error.message}`);
  }
}

// ===================================================================
// TEST FUNCTIONS
// ===================================================================

async function testOffsetPagination() {
  console.log('\n' + '='.repeat(60));
  console.log('Testing OFFSET-BASED Pagination (skip/take)');
  console.log('='.repeat(60));

  try {
    const variables = {
      clientId: CONFIG.clientId,
      fiscalYear: CONFIG.fiscalYear,
      skip: 0,
      take: CONFIG.testPageSize
    };

    console.log('\nSending request with variables:', JSON.stringify(variables, null, 2));

    const result = await makeGraphQLRequest(OFFSET_TEST_QUERY, variables);

    const clients = result.data?.clients || [];
    if (clients.length === 0) {
      console.log('❌ No clients found');
      return { supported: false, reason: 'No clients found' };
    }

    const clientName = clients[0].clientName;
    const engagements = clients[0]?.clientProfiles?.[0]?.engagements || [];

    console.log(`\n✅ SUCCESS! Offset pagination is supported!`);
    console.log(`   Client: ${clientName}`);
    console.log(`   Engagements returned: ${engagements.length}`);
    console.log(`   First engagement: ${engagements[0]?.engagementNumber || 'N/A'}`);

    if (engagements.length > 0) {
      console.log('\n   Sample engagements:');
      engagements.slice(0, 3).forEach((eng, idx) => {
        console.log(`   ${idx + 1}. ${eng.engagementNumber} - ${eng.engagementName}`);
      });
    }

    return { supported: true, count: engagements.length };

  } catch (error) {
    console.log(`\n❌ FAILED: ${error.message}`);
    return { supported: false, reason: error.message };
  }
}

async function testCursorPagination() {
  console.log('\n' + '='.repeat(60));
  console.log('Testing CURSOR-BASED Pagination (first/after/edges)');
  console.log('='.repeat(60));

  try {
    const variables = {
      clientId: CONFIG.clientId,
      fiscalYear: CONFIG.fiscalYear,
      first: CONFIG.testPageSize,
      after: null
    };

    console.log('\nSending request with variables:', JSON.stringify(variables, null, 2));

    const result = await makeGraphQLRequest(CURSOR_TEST_QUERY, variables);

    const clients = result.data?.clients || [];
    if (clients.length === 0) {
      console.log('❌ No clients found');
      return { supported: false, reason: 'No clients found' };
    }

    const clientName = clients[0].clientName;
    const engagementsConnection = clients[0]?.clientProfiles?.[0]?.engagements;
    const edges = engagementsConnection?.edges || [];
    const pageInfo = engagementsConnection?.pageInfo || {};
    const totalCount = engagementsConnection?.totalCount;

    console.log(`\n✅ SUCCESS! Cursor pagination is supported!`);
    console.log(`   Client: ${clientName}`);
    console.log(`   Engagements returned: ${edges.length}`);
    console.log(`   Total count: ${totalCount || 'Not provided'}`);
    console.log(`   Has next page: ${pageInfo.hasNextPage || false}`);
    console.log(`   End cursor: ${pageInfo.endCursor || 'None'}`);

    if (edges.length > 0) {
      console.log('\n   Sample engagements:');
      edges.slice(0, 3).forEach((edge, idx) => {
        console.log(`   ${idx + 1}. ${edge.node.engagementNumber} - ${edge.node.engagementName}`);
      });
    }

    return {
      supported: true,
      count: edges.length,
      totalCount: totalCount,
      hasNextPage: pageInfo.hasNextPage,
      endCursor: pageInfo.endCursor
    };

  } catch (error) {
    console.log(`\n❌ FAILED: ${error.message}`);
    return { supported: false, reason: error.message };
  }
}

// ===================================================================
// MAIN TEST RUNNER
// ===================================================================

async function runTests() {
  console.log('\n' + '═'.repeat(60));
  console.log('MAT GraphQL Pagination Support Test');
  console.log('═'.repeat(60));
  console.log('\nConfiguration:');
  console.log(`  Endpoint: ${CONFIG.endpoint}`);
  console.log(`  Client ID: ${CONFIG.clientId}`);
  console.log(`  Fiscal Year: ${CONFIG.fiscalYear}`);
  console.log(`  Test Page Size: ${CONFIG.testPageSize}`);

  // Validate configuration
  if (CONFIG.endpoint.includes('YOUR_') || CONFIG.token.includes('YOUR_')) {
    console.log('\n❌ ERROR: Please update the configuration with your actual values!');
    console.log('   Set MAT_GRAPHQL_ENDPOINT and MAT_API_TOKEN environment variables,');
    console.log('   or update the CONFIG object in this script.');
    process.exit(1);
  }

  // Run tests
  const offsetResult = await testOffsetPagination();
  await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second between tests
  const cursorResult = await testCursorPagination();

  // Summary
  console.log('\n' + '═'.repeat(60));
  console.log('TEST SUMMARY');
  console.log('═'.repeat(60));

  console.log('\nOffset-based (skip/take):');
  if (offsetResult.supported) {
    console.log(`  ✅ SUPPORTED - Returned ${offsetResult.count} engagements`);
  } else {
    console.log(`  ❌ NOT SUPPORTED - ${offsetResult.reason}`);
  }

  console.log('\nCursor-based (first/after/edges):');
  if (cursorResult.supported) {
    console.log(`  ✅ SUPPORTED - Returned ${cursorResult.count} engagements`);
    if (cursorResult.totalCount) {
      console.log(`     Total available: ${cursorResult.totalCount}`);
    }
    if (cursorResult.hasNextPage) {
      console.log(`     Has more pages: Yes`);
    }
  } else {
    console.log(`  ❌ NOT SUPPORTED - ${cursorResult.reason}`);
  }

  // Recommendation
  console.log('\n' + '═'.repeat(60));
  console.log('RECOMMENDATION');
  console.log('═'.repeat(60));

  if (cursorResult.supported && offsetResult.supported) {
    console.log('\n✨ Both pagination methods are supported!');
    console.log('   RECOMMENDED: Use cursor-based pagination for better reliability.');
    console.log('   - Use the cursor-based implementation from pagination_implementation_examples.js');
  } else if (cursorResult.supported) {
    console.log('\n✨ Use cursor-based pagination!');
    console.log('   - Use the cursor-based implementation from pagination_implementation_examples.js');
  } else if (offsetResult.supported) {
    console.log('\n✨ Use offset-based pagination!');
    console.log('   - Use the offset-based implementation from pagination_implementation_examples.js');
  } else {
    console.log('\n⚠️  WARNING: Neither pagination method worked!');
    console.log('   This could be due to:');
    console.log('   1. Incorrect endpoint or token');
    console.log('   2. Different pagination syntax required by MAT API');
    console.log('   3. Network/permission issues');
    console.log('\n   Please check:');
    console.log('   - MAT API documentation for pagination syntax');
    console.log('   - Your credentials and permissions');
    console.log('   - Network connectivity to MAT API');
  }

  console.log('\n' + '═'.repeat(60));
  console.log('For implementation details, see:');
  console.log('  - QUICK_REFERENCE.md');
  console.log('  - pagination_implementation_examples.js');
  console.log('  - pagination_implementation_examples.py');
  console.log('═'.repeat(60) + '\n');
}

// ===================================================================
// RUN THE TESTS
// ===================================================================

if (require.main === module) {
  runTests().catch(error => {
    console.error('\n❌ Unexpected error:', error);
    process.exit(1);
  });
}

module.exports = {
  testOffsetPagination,
  testCursorPagination,
  makeGraphQLRequest
};

// ===================================================================
// PAGINATION IMPLEMENTATION EXAMPLES FOR MAT GRAPHQL API
// ===================================================================

// ===================================================================
// OPTION 1: OFFSET-BASED PAGINATION (SIMPLE)
// ===================================================================

/**
 * Fetch all engagements using offset-based pagination
 * @param {string} clientId - Client ID to search for
 * @param {string} fiscalYear - Fiscal year to search for
 * @param {number} pageSize - Number of engagements per page (default: 500)
 * @returns {Promise<Object>} - Complete response with all engagements
 */
async function fetchAllEngagementsOffsetBased(clientId, fiscalYear, pageSize = 500) {
  const query = `
    query MATGlobalClientRequest($clientId: String!, $fiscalYear: String!, $skip: Int!, $take: Int!) {
      clients(where:{clientId:{eq:$clientId}}) {
        clientFiscalYear
        parentClientId
        clientId
        clientName
        clientProfiles(where: {clientAuditYear:{eq: $fiscalYear}}) {
          clientProfileId
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
            engagementDescription
            engagementTypeName
            servicePeriodStartDate
            serviceName
            updatedDate
            isDeleted
            isTerminated
            isInvalidated
            isSpecialPurpose
            isNoLongerPerforming
            subjectMatterId
            subjectMatterName
            subjectMatterValue
            modelAuditRuleInsurance500Mln
            picAssigned
            parentEngagement {
              engagementNumber
              engagementName
              engagementTypeName
              serviceName
              isSpecialPurpose
              isDeleted
              isTerminated
              isInvalidated
              isNoLongerPerforming
              servicePeriodStartDate
              subjectMatterId
              subjectMatterName
              subjectMatterValue
              modelAuditRuleInsurance500Mln
              reportingEntity {
                entityName
                entityTypeId
                entityTypeName
                uISelectedTypeId
                uISelectedTypeName
                entityDerivedTypeId
                entityDerivedTypeName
              }
              pso {
                pSOName
                servicePeriodEnd
              }
            }
            pso {
              pSOName
              servicePeriodEnd
              industryId
              industryName
              issuingOfficeId
              regionId
              regionName
              sectorId
              sectorName
              officeName
              updatedDate
            }
            deliverables {
              deliverableSPSs {
                key
                value
              }
              updatedDate
            }
            reportingEntity {
              entityTypeId
              entityName
              entityTypeName
              entityDerivedTypeName
              entityDerivedTypeId
              uISelectedTypeId
            }
            spawnedEngagement {
              engagementNumber
            }
          }
        }
      }
    }
  `;

  let allEngagements = [];
  let skip = 0;
  let hasMore = true;
  let clientData = null;
  let requestCount = 0;

  console.log(`Starting paginated fetch for client ${clientId}, fiscal year ${fiscalYear}`);
  console.log(`Page size: ${pageSize}`);

  while (hasMore) {
    requestCount++;
    console.log(`\n--- Request ${requestCount} ---`);
    console.log(`Fetching engagements ${skip} to ${skip + pageSize - 1}...`);

    const variables = {
      clientId: clientId,
      fiscalYear: fiscalYear,
      skip: skip,
      take: pageSize
    };

    try {
      // Make the GraphQL request
      const response = await makeGraphQLRequest(query, variables);
      
      // Extract data
      const clients = response.data?.clients || [];
      
      if (clients.length === 0) {
        console.log('No clients found');
        break;
      }

      // Store client-level data from first request
      if (!clientData) {
        clientData = {
          clientFiscalYear: clients[0].clientFiscalYear,
          parentClientId: clients[0].parentClientId,
          clientId: clients[0].clientId,
          clientName: clients[0].clientName,
          clientProfileId: clients[0].clientProfiles[0]?.clientProfileId,
          clientAuditYear: clients[0].clientProfiles[0]?.clientAuditYear
        };
      }

      const engagements = clients[0]?.clientProfiles[0]?.engagements || [];
      
      console.log(`Retrieved ${engagements.length} engagements`);
      allEngagements = allEngagements.concat(engagements);
      console.log(`Total engagements so far: ${allEngagements.length}`);

      // Check if there are more results
      hasMore = engagements.length === pageSize;
      skip += pageSize;

    } catch (error) {
      console.error(`Error on request ${requestCount}:`, error);
      throw error;
    }
  }

  console.log(`\n=== Fetch Complete ===`);
  console.log(`Total API requests: ${requestCount}`);
  console.log(`Total engagements retrieved: ${allEngagements.length}`);

  // Reconstruct the full response
  return {
    data: {
      clients: [{
        clientFiscalYear: clientData.clientFiscalYear,
        parentClientId: clientData.parentClientId,
        clientId: clientData.clientId,
        clientName: clientData.clientName,
        clientProfiles: [{
          clientProfileId: clientData.clientProfileId,
          clientAuditYear: clientData.clientAuditYear,
          engagements: allEngagements
        }]
      }]
    }
  };
}

// ===================================================================
// OPTION 2: CURSOR-BASED PAGINATION (RECOMMENDED FOR PRODUCTION)
// ===================================================================

/**
 * Fetch all engagements using cursor-based pagination
 * @param {string} clientId - Client ID to search for
 * @param {string} fiscalYear - Fiscal year to search for
 * @param {number} pageSize - Number of engagements per page (default: 500)
 * @returns {Promise<Object>} - Complete response with all engagements
 */
async function fetchAllEngagementsCursorBased(clientId, fiscalYear, pageSize = 500) {
  const query = `
    query MATGlobalClientRequest($clientId: String!, $fiscalYear: String!, $first: Int!, $after: String) {
      clients(where:{clientId:{eq:$clientId}}) {
        clientFiscalYear
        parentClientId
        clientId
        clientName
        clientProfiles(where: {clientAuditYear:{eq: $fiscalYear}}) {
          clientProfileId
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
                engagementDescription
                engagementTypeName
                servicePeriodStartDate
                serviceName
                updatedDate
                isDeleted
                isTerminated
                isInvalidated
                isSpecialPurpose
                isNoLongerPerforming
                subjectMatterId
                subjectMatterName
                subjectMatterValue
                modelAuditRuleInsurance500Mln
                picAssigned
                parentEngagement {
                  engagementNumber
                  engagementName
                  engagementTypeName
                  serviceName
                  isSpecialPurpose
                  isDeleted
                  isTerminated
                  isInvalidated
                  isNoLongerPerforming
                  servicePeriodStartDate
                  subjectMatterId
                  subjectMatterName
                  subjectMatterValue
                  modelAuditRuleInsurance500Mln
                  reportingEntity {
                    entityName
                    entityTypeId
                    entityTypeName
                    uISelectedTypeId
                    uISelectedTypeName
                    entityDerivedTypeId
                    entityDerivedTypeName
                  }
                  pso {
                    pSOName
                    servicePeriodEnd
                  }
                }
                pso {
                  pSOName
                  servicePeriodEnd
                  industryId
                  industryName
                  issuingOfficeId
                  regionId
                  regionName
                  sectorId
                  sectorName
                  officeName
                  updatedDate
                }
                deliverables {
                  deliverableSPSs {
                    key
                    value
                  }
                  updatedDate
                }
                reportingEntity {
                  entityTypeId
                  entityName
                  entityTypeName
                  entityDerivedTypeName
                  entityDerivedTypeId
                  uISelectedTypeId
                }
                spawnedEngagement {
                  engagementNumber
                }
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

  let allEngagements = [];
  let cursor = null;
  let hasNextPage = true;
  let clientData = null;
  let requestCount = 0;
  let totalCount = null;

  console.log(`Starting cursor-based paginated fetch for client ${clientId}, fiscal year ${fiscalYear}`);
  console.log(`Page size: ${pageSize}`);

  while (hasNextPage) {
    requestCount++;
    console.log(`\n--- Request ${requestCount} ---`);
    console.log(`Cursor: ${cursor || 'null (first page)'}`);

    const variables = {
      clientId: clientId,
      fiscalYear: fiscalYear,
      first: pageSize,
      after: cursor
    };

    try {
      // Make the GraphQL request
      const response = await makeGraphQLRequest(query, variables);
      
      // Extract data
      const clients = response.data?.clients || [];
      
      if (clients.length === 0) {
        console.log('No clients found');
        break;
      }

      // Store client-level data from first request
      if (!clientData) {
        clientData = {
          clientFiscalYear: clients[0].clientFiscalYear,
          parentClientId: clients[0].parentClientId,
          clientId: clients[0].clientId,
          clientName: clients[0].clientName,
          clientProfileId: clients[0].clientProfiles[0]?.clientProfileId,
          clientAuditYear: clients[0].clientProfiles[0]?.clientAuditYear
        };
      }

      const engagementsConnection = clients[0]?.clientProfiles[0]?.engagements;
      const edges = engagementsConnection?.edges || [];
      const pageInfo = engagementsConnection?.pageInfo;
      
      if (totalCount === null && engagementsConnection?.totalCount !== undefined) {
        totalCount = engagementsConnection.totalCount;
        console.log(`Total engagements available: ${totalCount}`);
      }

      // Extract engagement nodes from edges
      const engagements = edges.map(edge => edge.node);
      
      console.log(`Retrieved ${engagements.length} engagements`);
      allEngagements = allEngagements.concat(engagements);
      console.log(`Total engagements so far: ${allEngagements.length}${totalCount ? ` / ${totalCount}` : ''}`);

      // Update pagination state
      hasNextPage = pageInfo?.hasNextPage || false;
      cursor = pageInfo?.endCursor || null;

      console.log(`Has next page: ${hasNextPage}`);

    } catch (error) {
      console.error(`Error on request ${requestCount}:`, error);
      throw error;
    }
  }

  console.log(`\n=== Fetch Complete ===`);
  console.log(`Total API requests: ${requestCount}`);
  console.log(`Total engagements retrieved: ${allEngagements.length}`);

  // Reconstruct the full response
  return {
    data: {
      clients: [{
        clientFiscalYear: clientData.clientFiscalYear,
        parentClientId: clientData.parentClientId,
        clientId: clientData.clientId,
        clientName: clientData.clientName,
        clientProfiles: [{
          clientProfileId: clientData.clientProfileId,
          clientAuditYear: clientData.clientAuditYear,
          engagements: allEngagements
        }]
      }]
    }
  };
}

// ===================================================================
// HELPER FUNCTION: MAKE GRAPHQL REQUEST
// ===================================================================

/**
 * Make a GraphQL request to MAT API
 * Replace this with your actual API client implementation
 */
async function makeGraphQLRequest(query, variables) {
  // Example using fetch (replace with your actual implementation)
  const response = await fetch('YOUR_MAT_GRAPHQL_ENDPOINT', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.MAT_API_TOKEN}`,
      // Add any other required headers
    },
    body: JSON.stringify({
      query: query,
      variables: variables
    })
  });

  if (!response.ok) {
    throw new Error(`GraphQL request failed: ${response.status} ${response.statusText}`);
  }

  const result = await response.json();

  if (result.errors) {
    throw new Error(`GraphQL errors: ${JSON.stringify(result.errors)}`);
  }

  return result;
}

// ===================================================================
// USAGE EXAMPLES
// ===================================================================

// Example 1: Using offset-based pagination
async function example1() {
  try {
    const result = await fetchAllEngagementsOffsetBased(
      '0008005369',  // clientId
      '2025',        // fiscalYear
      500            // pageSize
    );
    
    console.log('\nFinal result:');
    console.log(`Client: ${result.data.clients[0].clientName}`);
    console.log(`Total engagements: ${result.data.clients[0].clientProfiles[0].engagements.length}`);
    
    // Save to file or process further
    // fs.writeFileSync('result.json', JSON.stringify(result, null, 2));
    
  } catch (error) {
    console.error('Failed to fetch engagements:', error);
  }
}

// Example 2: Using cursor-based pagination
async function example2() {
  try {
    const result = await fetchAllEngagementsCursorBased(
      '0008005369',  // clientId
      '2025',        // fiscalYear
      500            // pageSize
    );
    
    console.log('\nFinal result:');
    console.log(`Client: ${result.data.clients[0].clientName}`);
    console.log(`Total engagements: ${result.data.clients[0].clientProfiles[0].engagements.length}`);
    
    // Save to file or process further
    // fs.writeFileSync('result.json', JSON.stringify(result, null, 2));
    
  } catch (error) {
    console.error('Failed to fetch engagements:', error);
  }
}

// Example 3: Parallel processing with smaller chunks
async function example3ParallelProcessing() {
  const clientId = '0008005369';
  const fiscalYear = '2025';
  const pageSize = 500;
  
  // Fetch with pagination
  const result = await fetchAllEngagementsOffsetBased(clientId, fiscalYear, pageSize);
  const engagements = result.data.clients[0].clientProfiles[0].engagements;
  
  // Process engagements in chunks (e.g., for further API calls)
  const chunkSize = 100;
  for (let i = 0; i < engagements.length; i += chunkSize) {
    const chunk = engagements.slice(i, i + chunkSize);
    console.log(`Processing engagements ${i} to ${i + chunk.length - 1}`);
    // Process chunk...
  }
}

// ===================================================================
// EXPORTS
// ===================================================================

module.exports = {
  fetchAllEngagementsOffsetBased,
  fetchAllEngagementsCursorBased,
  makeGraphQLRequest
};

# GraphQL Query Pagination Analysis

## Problem Summary
Your GraphQL query is returning **1,479 engagements** in a single response, resulting in a **104,578-line JSON file (>2MB)**. This is causing your PRT API to fail due to volume.

## Data Structure Analysis
```
{
  data: {
    clients: [1 client] {
      clientProfiles: [1 profile] {
        engagements: [1,479 engagements] ← **THIS IS THE BOTTLENECK**
      }
    }
  }
}
```

## Recommended Solution: Paginate at the `engagements` Level

The **engagements** array is the source of the volume issue. You need to add pagination at this level.

---

## Option 1: Cursor-Based Pagination (Recommended)

### Modified Query with Cursor Pagination
```graphql
query MATGlobalClientRequest($cursor: String, $pageSize: Int!) {
  clients(where:{clientId:{eq:"##SEARCHCRITERIACLIENT##"}}) {
    clientFiscalYear
    parentClientId
    clientId
    clientName
    clientProfiles(where: {clientAuditYear:{eq: "##SEARCHFISCALYEAR##"}}) {
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
        first: $pageSize
        after: $cursor
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
```

### Usage (Cursor-Based):
```javascript
// First call
const variables1 = {
  cursor: null,
  pageSize: 500
};

// Second call (use endCursor from previous response)
const variables2 = {
  cursor: "previous_end_cursor_value",
  pageSize: 500
};

// Continue until hasNextPage = false
```

### Benefits of Cursor-Based Pagination:
- ✅ Handles real-time data changes gracefully
- ✅ More efficient for large datasets
- ✅ No skipped/duplicate records even if data changes between requests
- ✅ Industry standard for GraphQL

---

## Option 2: Offset-Based Pagination (Simpler)

### Modified Query with Offset Pagination
```graphql
query MATGlobalClientRequest($skip: Int!, $take: Int!) {
  clients(where:{clientId:{eq:"##SEARCHCRITERIACLIENT##"}}) {
    clientFiscalYear
    parentClientId
    clientId
    clientName
    clientProfiles(where: {clientAuditYear:{eq: "##SEARCHFISCALYEAR##"}}) {
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
```

### Usage (Offset-Based):
```javascript
// First batch: 0-499
const variables1 = { skip: 0, take: 500 };

// Second batch: 500-999
const variables2 = { skip: 500, take: 500 };

// Third batch: 1000-1479
const variables3 = { skip: 1000, take: 500 };
```

### Benefits of Offset-Based Pagination:
- ✅ Simpler to implement
- ✅ Easy to calculate pages (page 1, page 2, etc.)
- ✅ Can jump to any page directly
- ⚠️ Can have issues if data changes between requests

---

## Recommended Page Sizes

Given **1,479 engagements**:

### Option A: 3 Chunks
- **Page size: 500**
- Chunks: 500 + 500 + 479 = 1,479 total
- API calls needed: **3 calls**

### Option B: 2 Chunks  
- **Page size: 750**
- Chunks: 750 + 729 = 1,479 total
- API calls needed: **2 calls**

### Option C: 4 Chunks (Conservative)
- **Page size: 400**
- Chunks: 400 + 400 + 400 + 279 = 1,479 total
- API calls needed: **4 calls**

**Recommendation**: Start with **500 engagements per page** (3 chunks). If that still causes issues, reduce to 400.

---

## Implementation Steps

### 1. Check MAT API Pagination Support
First, verify which pagination parameters MAT GraphQL API supports:
- `first`/`after` (cursor-based)
- `skip`/`take` or `offset`/`limit` (offset-based)

### 2. Update Your Query
Add pagination parameters to the `engagements` field.

### 3. Update Your PRT API Logic
```javascript
async function fetchAllEngagements(clientId, fiscalYear) {
  let allEngagements = [];
  let skip = 0;
  const take = 500;
  let hasMore = true;

  while (hasMore) {
    const response = await fetchMATData(clientId, fiscalYear, skip, take);
    const engagements = response.data.clients[0]?.clientProfiles[0]?.engagements || [];
    
    allEngagements = allEngagements.concat(engagements);
    
    // Check if there are more results
    hasMore = engagements.length === take;
    skip += take;
    
    console.log(`Fetched ${engagements.length} engagements. Total: ${allEngagements.length}`);
  }

  return allEngagements;
}
```

### 4. Handle the Combined Response
Merge the paginated results back into the original structure:
```javascript
const combinedResponse = {
  data: {
    clients: [{
      clientFiscalYear: "...",
      parentClientId: "...",
      clientId: "...",
      clientName: "...",
      clientProfiles: [{
        clientProfileId: "...",
        clientAuditYear: "...",
        engagements: allEngagements  // Combined from all pages
      }]
    }]
  }
};
```

---

## Alternative: Paginate at Client Level (Not Recommended)

You could also paginate at the `clients` level, but since you're filtering by a specific `clientId`, you'll only ever get 1 client. This wouldn't solve the volume issue.

---

## Why Not Paginate clientProfiles?

Since you're filtering by a specific `clientAuditYear`, you only get 1 profile. Pagination here wouldn't help with the volume issue.

---

## Summary

**Answer: Add pagination to the `engagements` field**

✅ **Where**: Inside the `engagements(...)` field  
✅ **Parameters**: Either `skip/take` or `first/after`  
✅ **Page Size**: 500 engagements per request (3 total requests)  
✅ **Total Calls**: 3 API calls to fetch all 1,479 engagements

This will reduce your response size from **>2MB** to approximately **700KB per request**, making it manageable for your PRT API.

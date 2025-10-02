# GraphQL Query: Before and After Pagination

## 🔴 BEFORE (Current - Causing Failures)

### Query
```graphql
query MATGlobalClientRequest {
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
      ) {
        engagementNumber
        engagementName
        # ... all other fields ...
      }
    }
  }
}
```

### Issues
❌ Returns **1,479 engagements** in single response  
❌ Response size: **>2MB** (104,578 lines)  
❌ Causes API timeout/failure  
❌ No way to chunk the data  

---

## 🟢 AFTER - Option 1: Offset-Based Pagination (Simpler)

### Query
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
        skip: $skip     # ← NEW: Offset pagination
        take: $take     # ← NEW: Page size
      ) {
        engagementNumber
        engagementName
        # ... all other fields ...
      }
    }
  }
}
```

### Changes Made
```diff
  engagements(
    where: {
      isNoLongerPerforming : {eq: false}
      isDeleted : {eq: false}
      isTerminated : {eq: false}
      isInvalidated : {eq: false}
      engagementTypeId: { neq: 6 }
      serviceTypeId: { nin: [10, 11, 12] }
    }
+   skip: $skip
+   take: $take
  ) {
```

### API Calls Required
```javascript
// Call 1: Get first 500 engagements
{ skip: 0, take: 500 }

// Call 2: Get next 500 engagements
{ skip: 500, take: 500 }

// Call 3: Get remaining 479 engagements
{ skip: 1000, take: 500 }
```

### Benefits
✅ Returns **~500 engagements** per response  
✅ Response size: **~700KB** per request (manageable)  
✅ **3 API calls** to get all data  
✅ Simple to implement  
✅ Can calculate exact page numbers  

---

## 🟢 AFTER - Option 2: Cursor-Based Pagination (Recommended)

### Query
```graphql
query MATGlobalClientRequest($first: Int!, $after: String) {
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
        first: $first     # ← NEW: Page size
        after: $after     # ← NEW: Cursor (null for first page)
      ) {
        edges {           # ← NEW: Cursor pagination structure
          node {
            engagementNumber
            engagementName
            # ... all other fields ...
          }
          cursor          # ← NEW: Cursor for this item
        }
        pageInfo {        # ← NEW: Pagination metadata
          hasNextPage
          endCursor
        }
        totalCount        # ← NEW: Total items available
      }
    }
  }
}
```

### Changes Made
```diff
  engagements(
    where: {
      isNoLongerPerforming : {eq: false}
      isDeleted : {eq: false}
      isTerminated : {eq: false}
      isInvalidated : {eq: false}
      engagementTypeId: { neq: 6 }
      serviceTypeId: { nin: [10, 11, 12] }
    }
+   first: $first
+   after: $after
  ) {
+   edges {
+     node {
        engagementNumber
        engagementName
        # ... all other fields ...
+     }
+     cursor
+   }
+   pageInfo {
+     hasNextPage
+     endCursor
+   }
+   totalCount
  }
```

### API Calls Required
```javascript
// Call 1: Get first 500 engagements
{ first: 500, after: null }
// Response includes: pageInfo.endCursor = "cursor_500"

// Call 2: Get next 500 engagements
{ first: 500, after: "cursor_500" }
// Response includes: pageInfo.endCursor = "cursor_1000"

// Call 3: Get remaining engagements
{ first: 500, after: "cursor_1000" }
// Response includes: pageInfo.hasNextPage = false
```

### Benefits
✅ Returns **~500 engagements** per response  
✅ Response size: **~700KB** per request (manageable)  
✅ **3 API calls** to get all data  
✅ Handles real-time data changes gracefully  
✅ No duplicates/skips even if data changes  
✅ Includes `totalCount` for progress tracking  
✅ Industry standard for GraphQL  

---

## Comparison Table

| Feature | Before | After (Offset) | After (Cursor) |
|---------|--------|----------------|----------------|
| Engagements per response | 1,479 | ~500 | ~500 |
| Response size | >2MB | ~700KB | ~700KB |
| API calls needed | 1 | 3 | 3 |
| Works with large data | ❌ No | ✅ Yes | ✅ Yes |
| Handles data changes | N/A | ⚠️ May skip/duplicate | ✅ Yes |
| Implementation complexity | Simple | Simple | Moderate |
| Total count available | No | No | ✅ Yes |
| Progress tracking | No | Manual calculation | ✅ Built-in |

---

## Which Option Should You Choose?

### Choose **Offset-Based** (`skip`/`take`) if:
- MAT API doesn't support cursor pagination
- Your data is relatively stable (not frequently changing)
- You want simpler implementation
- You need to jump to specific pages

### Choose **Cursor-Based** (`first`/`after`) if:
- MAT API supports cursor pagination (check documentation)
- Your data changes frequently
- You want production-grade reliability
- You need progress tracking (`totalCount`)

---

## How to Determine Which MAT Supports

Test both queries against MAT API:

### Test Offset Pagination
```graphql
query TestOffset {
  clients(where:{clientId:{eq:"YOUR_CLIENT_ID"}}) {
    clientProfiles(where: {clientAuditYear:{eq: "2025"}}) {
      engagements(skip: 0, take: 10) {
        engagementNumber
      }
    }
  }
}
```

### Test Cursor Pagination
```graphql
query TestCursor {
  clients(where:{clientId:{eq:"YOUR_CLIENT_ID"}}) {
    clientProfiles(where: {clientAuditYear:{eq: "2025"}}) {
      engagements(first: 10) {
        edges {
          node {
            engagementNumber
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
}
```

Run both queries and see which one works!

---

## Summary

### The Key Change
**Add pagination parameters to the `engagements` field** - this is where the volume bottleneck exists.

### Recommended Approach
1. ✅ Test which pagination style MAT supports
2. ✅ Use **cursor-based** if available (better for production)
3. ✅ Use **offset-based** if cursor is not supported
4. ✅ Set page size to **500 engagements**
5. ✅ Make **3 API calls** instead of 1
6. ✅ Combine results in your PRT API before returning to client

This will reduce your response size from >2MB to ~700KB per request, solving your volume issue!

# MAT GraphQL Pagination Solution

## Problem Statement

Your PRT API is calling MAT GraphQL with a query that returns **1,479 engagements** in a single response, resulting in a **>2MB JSON file**. This is causing your API to fail due to volume.

## Solution

**Add pagination to the `engagements` field** in your GraphQL query.

## Quick Start

### Step 1: Identify Which Pagination MAT Supports

Run these test queries:

**Test Offset Pagination:**
```graphql
query Test {
  clients(where:{clientId:{eq:"0008005369"}}) {
    clientProfiles(where:{clientAuditYear:{eq:"2025"}}) {
      engagements(skip: 0, take: 5) {
        engagementNumber
      }
    }
  }
}
```

**Test Cursor Pagination:**
```graphql
query Test {
  clients(where:{clientId:{eq:"0008005369"}}) {
    clientProfiles(where:{clientAuditYear:{eq:"2025"}}) {
      engagements(first: 5) {
        edges { node { engagementNumber } }
        pageInfo { hasNextPage }
      }
    }
  }
}
```

### Step 2: Implement the Solution

Choose the implementation based on what MAT supports:

- **Offset-Based**: See `pagination_implementation_examples.js` or `.py`
- **Cursor-Based**: See `pagination_implementation_examples.js` or `.py`

### Step 3: Test and Deploy

1. Test with page size of 500
2. Verify you get all 1,479 engagements across 3 requests
3. Deploy to your PRT API

## Files in This Repository

| File | Description |
|------|-------------|
| **QUICK_REFERENCE.md** | ⚡ Start here! Quick reference card with minimal changes needed |
| **BEFORE_AND_AFTER_COMPARISON.md** | Side-by-side comparison of queries before and after pagination |
| **pagination_analysis.md** | Detailed analysis of the problem and solutions |
| **pagination_implementation_examples.js** | Complete JavaScript/Node.js implementation with examples |
| **pagination_implementation_examples.py** | Complete Python implementation with examples |
| **client 0008005369.json** | Your original 2MB JSON output (1,479 engagements) |

## Key Insights

### Data Structure
```
{
  clients: [1] {
    clientProfiles: [1] {
      engagements: [1,479] ← BOTTLENECK HERE
    }
  }
}
```

### Why Paginate at `engagements`?

- **clients**: Only 1 (filtered by specific clientId)
- **clientProfiles**: Only 1 (filtered by specific fiscalYear)
- **engagements**: **1,479** ← This is causing the volume issue

### Recommended Settings

- **Page Size**: 500 engagements
- **API Calls**: 3 requests
- **Batches**: 500 + 500 + 479 = 1,479 total
- **Response Size**: ~700KB per request (down from 2MB+)

## Implementation Approaches

### Option 1: Offset-Based (Simpler)

```graphql
engagements(
  where: { /* your filters */ }
  skip: $skip
  take: $take
)
```

**Pros:**
- ✅ Simple to implement
- ✅ Easy to understand
- ✅ Can jump to any page

**Cons:**
- ⚠️ May have issues if data changes between requests

### Option 2: Cursor-Based (Recommended)

```graphql
engagements(
  where: { /* your filters */ }
  first: $first
  after: $after
) {
  edges {
    node { /* fields */ }
  }
  pageInfo {
    hasNextPage
    endCursor
  }
}
```

**Pros:**
- ✅ Handles real-time data changes gracefully
- ✅ No duplicates or skipped records
- ✅ Industry standard
- ✅ Includes progress tracking

**Cons:**
- ⚠️ Slightly more complex to implement

## Expected Results

### Before Pagination
- 1 API call
- 1,479 engagements in one response
- >2MB response size
- ❌ API fails due to volume

### After Pagination
- 3 API calls
- ~500 engagements per response
- ~700KB per response
- ✅ API succeeds

## Support

If you need help:

1. Check **QUICK_REFERENCE.md** for minimal changes
2. Review **BEFORE_AND_AFTER_COMPARISON.md** for detailed query differences
3. Use the code in **pagination_implementation_examples.js** or **.py**
4. Read **pagination_analysis.md** for in-depth explanation

## Summary

**Answer to your question: "Where should I add pagination?"**

➡️ **Add pagination to the `engagements` field**

This field contains 1,479 items and is the source of your volume problem. By paginating at this level with a page size of 500, you'll split the response into 3 manageable chunks (~700KB each).

---

**Need the absolute minimal change?**

1. Add `skip: $skip, take: $take` to the `engagements` field
2. Call the API 3 times with different skip values (0, 500, 1000)
3. Combine the results

That's it! 🎉

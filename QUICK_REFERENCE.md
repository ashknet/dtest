# Pagination Quick Reference Card

## ⚡ Quick Answer

**Where to add pagination?** → On the `engagements` field  
**Why?** → You have 1,479 engagements causing a >2MB response  
**Page size?** → 500 engagements per request  
**API calls needed?** → 3 calls (500 + 500 + 479)

---

## 📝 Minimal Code Changes

### Offset-Based (Simplest)

**Add to query:**
```graphql
engagements(
  where: { /* existing filters */ }
  skip: $skip    # ← ADD THIS
  take: $take    # ← ADD THIS
)
```

**Variables to send:**
```javascript
// Call 1
{ skip: 0, take: 500 }

// Call 2
{ skip: 500, take: 500 }

// Call 3
{ skip: 1000, take: 500 }
```

---

### Cursor-Based (Better)

**Add to query:**
```graphql
engagements(
  where: { /* existing filters */ }
  first: $first   # ← ADD THIS
  after: $after   # ← ADD THIS
) {
  edges {         # ← WRAP FIELDS
    node {
      # Your existing fields here
    }
  }
  pageInfo {      # ← ADD THIS
    hasNextPage
    endCursor
  }
}
```

**Variables to send:**
```javascript
// Call 1
{ first: 500, after: null }

// Call 2 (use endCursor from previous response)
{ first: 500, after: "cursor_from_previous" }

// Continue until hasNextPage = false
```

---

## 🔍 Test Which One Works

Run this quick test against MAT API:

```graphql
# Test 1: Does skip/take work?
query TestOffset {
  clients(where:{clientId:{eq:"0008005369"}}) {
    clientProfiles(where:{clientAuditYear:{eq:"2025"}}) {
      engagements(skip: 0, take: 5) {
        engagementNumber
      }
    }
  }
}

# Test 2: Does first/after work?
query TestCursor {
  clients(where:{clientId:{eq:"0008005369"}}) {
    clientProfiles(where:{clientAuditYear:{eq:"2025"}}) {
      engagements(first: 5) {
        edges {
          node { engagementNumber }
        }
        pageInfo { hasNextPage }
      }
    }
  }
}
```

Whichever returns data successfully, use that approach!

---

## 📊 Your Data Breakdown

```
clients [1 client]
  └─ clientProfiles [1 profile]
       └─ engagements [1,479 engagements] ← PAGINATE HERE
            ├─ parentEngagement (nested object)
            ├─ pso (nested object)
            ├─ deliverables (array)
            ├─ reportingEntity (nested object)
            └─ spawnedEngagement (nested object)
```

---

## 💡 Why Not Paginate Elsewhere?

| Level | Count | Reason Not to Paginate |
|-------|-------|------------------------|
| `clients` | 1 | You filter by specific clientId |
| `clientProfiles` | 1 | You filter by specific fiscalYear |
| `engagements` | **1,479** | **← This is the problem!** |

---

## 🎯 Expected Outcome

### Before
- ❌ 1 API call
- ❌ 1,479 engagements
- ❌ 104,578 lines
- ❌ >2MB response
- ❌ API timeout/failure

### After
- ✅ 3 API calls
- ✅ ~500 engagements per call
- ✅ ~35,000 lines per response
- ✅ ~700KB per response
- ✅ API succeeds

---

## 📦 Files Created for You

1. **pagination_analysis.md** - Detailed analysis and recommendations
2. **pagination_implementation_examples.js** - Complete JavaScript/Node.js code
3. **pagination_implementation_examples.py** - Complete Python code
4. **BEFORE_AND_AFTER_COMPARISON.md** - Side-by-side query comparison
5. **QUICK_REFERENCE.md** - This quick reference (you are here!)

---

## 🚀 Next Steps

1. **Test** which pagination style MAT supports (offset vs cursor)
2. **Update** your GraphQL query with pagination parameters
3. **Implement** loop to fetch all pages
4. **Combine** results before returning to your client
5. **Test** with the real client ID and fiscal year

---

## 💭 Still Unsure?

**The simplest possible change:**

Change this:
```graphql
engagements(where: { /* filters */ }) {
```

To this:
```graphql
engagements(where: { /* filters */ }, skip: $skip, take: $take) {
```

And call it 3 times with:
- `skip: 0, take: 500`
- `skip: 500, take: 500`
- `skip: 1000, take: 500`

That's it! 🎉

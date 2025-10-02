# Visual Guide to Pagination Solution

## 🔴 Current Problem

```
┌─────────────────────────────────────────────┐
│         YOUR PRT API                        │
│                                             │
│  Makes 1 GraphQL request to MAT API         │
└─────────────┬───────────────────────────────┘
              │
              │ Single Request
              │
              ▼
┌─────────────────────────────────────────────┐
│         MAT GraphQL API                     │
│                                             │
│  Returns ALL data at once:                  │
│  • 1 client                                 │
│  • 1 clientProfile                          │
│  • 1,479 engagements ◄── TOO MUCH!         │
│                                             │
│  Response Size: >2MB                        │
│  Lines: 104,578                             │
└─────────────┬───────────────────────────────┘
              │
              │ ❌ FAILS - Too large!
              │
              ▼
┌─────────────────────────────────────────────┐
│         ERROR / TIMEOUT                     │
└─────────────────────────────────────────────┘
```

---

## 🟢 Solution with Pagination

```
┌─────────────────────────────────────────────────────────────┐
│              YOUR PRT API                                   │
│                                                             │
│  Makes 3 paginated GraphQL requests to MAT API              │
└──────┬────────────────┬────────────────┬────────────────────┘
       │                │                │
       │ Request 1      │ Request 2      │ Request 3
       │ skip: 0        │ skip: 500      │ skip: 1000
       │ take: 500      │ take: 500      │ take: 500
       │                │                │
       ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│              MAT GraphQL API                                │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Response 1  │  │  Response 2  │  │  Response 3  │     │
│  │              │  │              │  │              │     │
│  │ 500 engs     │  │ 500 engs     │  │ 479 engs     │     │
│  │ ~700KB       │  │ ~700KB       │  │ ~670KB       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────┬────────────────┬────────────────┬────────────────────┘
       │                │                │
       │ ✅ Success!    │ ✅ Success!    │ ✅ Success!
       │                │                │
       ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│              YOUR PRT API                                   │
│                                                             │
│  Combines all responses:                                    │
│  • 500 + 500 + 479 = 1,479 total engagements               │
│                                                             │
│  Returns complete dataset to client                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Structure Breakdown

```
Response Structure
│
├── data
│   └── clients [Array - Length: 1]
│       └── clients[0]
│           ├── clientFiscalYear: "12/31"
│           ├── parentClientId: "0008005369"
│           ├── clientId: "0001211917"
│           ├── clientName: "Blackstone Inc."
│           │
│           └── clientProfiles [Array - Length: 1]
│               └── clientProfiles[0]
│                   ├── clientProfileId: 40384
│                   ├── clientAuditYear: "2025"
│                   │
│                   └── engagements [Array - Length: 1,479] ◄── PAGINATE HERE!
│                       ├── engagements[0]
│                       │   ├── engagementNumber
│                       │   ├── engagementName
│                       │   ├── parentEngagement { ... }
│                       │   ├── pso { ... }
│                       │   ├── deliverables [...]
│                       │   ├── reportingEntity { ... }
│                       │   └── spawnedEngagement { ... }
│                       │
│                       ├── engagements[1]
│                       ├── engagements[2]
│                       ├── ...
│                       └── engagements[1478]
```

**Why paginate at `engagements`?**
- It's the only array with significant size (1,479 items)
- Each engagement has nested objects, making it heavy
- `clients` and `clientProfiles` are already filtered to 1 item each

---

## 🔄 Pagination Flow - Offset Based

```
┌─────────────────────────────────────────────────────────────┐
│                    All 1,479 Engagements                    │
│  (Conceptually - never fetched all at once)                 │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   Chunk 1      │  │   Chunk 2      │  │   Chunk 3      │
│                │  │                │  │                │
│  skip: 0       │  │  skip: 500     │  │  skip: 1000    │
│  take: 500     │  │  take: 500     │  │  take: 500     │
│                │  │                │  │                │
│  Engagements   │  │  Engagements   │  │  Engagements   │
│  0 - 499       │  │  500 - 999     │  │  1000 - 1478   │
│                │  │                │  │                │
│  (500 items)   │  │  (500 items)   │  │  (479 items)   │
└────────────────┘  └────────────────┘  └────────────────┘

Request 1:          Request 2:          Request 3:
variables: {        variables: {        variables: {
  skip: 0,            skip: 500,          skip: 1000,
  take: 500           take: 500           take: 500
}                   }                   }
```

---

## 🔄 Pagination Flow - Cursor Based

```
┌─────────────────────────────────────────────────────────────┐
│                    All 1,479 Engagements                    │
│  (Conceptually - never fetched all at once)                 │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   Page 1       │  │   Page 2       │  │   Page 3       │
│                │  │                │  │                │
│  first: 500    │  │  first: 500    │  │  first: 500    │
│  after: null   │  │  after: cursor1│  │  after: cursor2│
│                │  │                │  │                │
│  Returns:      │  │  Returns:      │  │  Returns:      │
│  • 500 items   │  │  • 500 items   │  │  • 479 items   │
│  • endCursor   │──┼─▶• endCursor   │──┼─▶• endCursor   │
│  • hasNextPage │  │  • hasNextPage │  │  • hasNextPage │
│    = true      │  │    = true      │  │    = false ◄── STOP!
└────────────────┘  └────────────────┘  └────────────────┘
```

**Key Differences:**
- Offset: You calculate the skip value (0, 500, 1000)
- Cursor: MAT API tells you the cursor for next page

---

## 📈 Size Comparison

```
┌─────────────────────────────────────────────────────────────┐
│                     Response Size                           │
└─────────────────────────────────────────────────────────────┘

BEFORE (No Pagination):
████████████████████████████████████████████████████████████
2,100 KB (>2MB) - TOO LARGE! ❌


AFTER (With Pagination - 3 requests):
Request 1: ████████████████████  700 KB  ✅
Request 2: ████████████████████  700 KB  ✅
Request 3: ███████████████████   670 KB  ✅
           ─────────────────────
Total:     2,070 KB (but delivered in manageable chunks!)
```

---

## 🎯 Implementation Decision Tree

```
                    Start Here
                        │
                        ▼
        ┌───────────────────────────────┐
        │ Does MAT API support          │
        │ cursor pagination?            │
        │ (first/after/edges/pageInfo)  │
        └───────────┬───────────────────┘
                    │
          ┌─────────┴─────────┐
          │                   │
         YES                 NO
          │                   │
          ▼                   ▼
    ┌──────────┐      ┌──────────┐
    │  USE     │      │  USE     │
    │  CURSOR  │      │  OFFSET  │
    │  BASED   │      │  BASED   │
    └──────────┘      └──────────┘
          │                   │
          │                   │
          ▼                   ▼
    first: $first         skip: $skip
    after: $after         take: $take
          │                   │
          ▼                   ▼
    Loop until            Loop until
    hasNextPage           response
    = false               length < take
```

---

## 💻 Code Flow Diagram

### Offset-Based Flow

```
START
  │
  ├─ Initialize: skip = 0, allEngagements = []
  │
  └─ WHILE hasMore:
       │
       ├─ Make API call with (skip, take=500)
       │     │
       │     ▼
       │  ┌──────────────────────────┐
       │  │  MAT API returns         │
       │  │  up to 500 engagements   │
       │  └──────────────────────────┘
       │     │
       ├─────┤
       │
       ├─ Append engagements to allEngagements
       │
       ├─ If (returned count < 500):
       │     hasMore = false  ◄── STOP LOOP
       │  Else:
       │     skip += 500      ◄── CONTINUE
       │
       └─ END WHILE
          │
          ▼
       Return combined allEngagements (1,479 total)
```

### Cursor-Based Flow

```
START
  │
  ├─ Initialize: cursor = null, allEngagements = []
  │
  └─ WHILE hasNextPage:
       │
       ├─ Make API call with (first=500, after=cursor)
       │     │
       │     ▼
       │  ┌──────────────────────────┐
       │  │  MAT API returns:        │
       │  │  • edges (engagements)   │
       │  │  • pageInfo.hasNextPage  │
       │  │  • pageInfo.endCursor    │
       │  └──────────────────────────┘
       │     │
       ├─────┤
       │
       ├─ Extract engagements from edges
       │
       ├─ Append to allEngagements
       │
       ├─ Update:
       │     cursor = pageInfo.endCursor
       │     hasNextPage = pageInfo.hasNextPage
       │
       └─ END WHILE
          │
          ▼
       Return combined allEngagements (1,479 total)
```

---

## 📋 Summary Table

| Metric | Before | After |
|--------|--------|-------|
| API Calls | 1 | 3 |
| Items per call | 1,479 | ~500 |
| Response size | >2MB | ~700KB |
| Status | ❌ Fails | ✅ Works |
| Time to first data | Slow (or timeout) | Fast (500 items in ~2s) |
| Progress tracking | None | Yes (page 1/3, 2/3, 3/3) |

---

## 🚀 Next Steps

1. **Test** which pagination MAT supports (run test queries)
2. **Choose** implementation (offset or cursor)
3. **Update** your GraphQL query
4. **Implement** pagination loop in your PRT API
5. **Combine** results before returning to client
6. **Deploy** and monitor

✅ Done! Your API will now handle large datasets reliably.

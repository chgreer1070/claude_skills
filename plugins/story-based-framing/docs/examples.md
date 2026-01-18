# Usage Examples

This document provides concrete, real-world examples of using story-based framing for pattern detection across multiple domains.

## Example 1: Code Analysis

### Use Case: Detecting Type Safety Violations in Python

**Scenario**: You're reviewing a Python codebase and need to identify instances where generic types claim to preserve type parameters but actually store union types, causing type safety issues.

**Pattern Name**: "The Fake Generic"

### Steps

1. **Define the pattern using story-based framing**

Create a narrative description following the four-act structure:

```markdown
# Pattern: The Fake Generic

## Act 1: The Promise
A generic class `Container(Generic[T])` promises to preserve type T throughout its operations. The TypeVar is constrained to specific types.

## Act 2: The Betrayal
But the constructor accepts `content: UnionType` instead of `content: T`, storing a union type rather than the promised generic parameter. The generic parameter T exists but is never actually used.

## Act 3: The Consequences
Methods contain `isinstance()` checks and `# type: ignore` comments to work around the type mismatch. `@overload` declarations attempt to paper over the union issue.

## Act 4: The Source
Values originate from heterogeneous storage (`dict[str, TypeA | TypeB]`) where specific type information is lost at the storage boundary.
```

2. **Delegate detection to sub-agent**

```python
Task(
    agent="Explore",
    prompt="""
    Search for instances of "The Fake Generic" pattern in this codebase:

    Act 1 (The Promise): Class declares Generic[T] with constrained TypeVar
    Act 2 (The Betrayal): Constructor accepts union type instead of T
    Act 3 (The Consequences): Methods use isinstance() checks and # type: ignore
    Act 4 (The Source): Values from heterogeneous dict[str, Union] storage

    For each match, report:
    - Class name and file location
    - Evidence for Acts 1-2 (promise/betrayal)
    - Count of isinstance checks and type suppressions (Act 3)
    - Origin of union values (Act 4)
    """
)
```

3. **Agent identifies pattern in 3 steps**

- Step 1: Search for `Generic[` declarations → Found `TemplateExpander(Generic[T])`
- Step 2: Check constructor signature → Confirmed accepts `ConfigValue` (union) not `T`
- Step 3: Validate Acts 3-4 → Found 5 isinstance checks, 3 type suppressions, values from `dict[str, str | list[str]]`

### Result

**Detection speed**: 3 steps (70% faster than symptom-based approach requiring 10 steps)

**Identified instance**: `TemplateExpander` class in `config.py`

**Evidence**:
- Act 1: Declares `TemplateExpander(Generic[T])` with `T = TypeVar('T', str, list[str])`
- Act 2: Constructor accepts `raw_value: ConfigValue` where `ConfigValue = str | list[str]`
- Act 3: 5 isinstance checks, 3 `# type: ignore` comments, 2 `@overload` declarations
- Act 4: Values from `BuildConfig._values: dict[str, str | list[str]]`

**Fix applied**:

```python
# Before (fake generic)
class TemplateExpander(Generic[T]):
    def __init__(self, raw_value: ConfigValue, config: BuildConfig):
        self._raw_value = raw_value  # Union, not T

# After (true generic)
def is_str(value: ConfigValue) -> TypeGuard[str]:
    return isinstance(value, str)

class TemplateExpander(Generic[T]):
    def __init__(self, raw_value: T, config: BuildConfig):
        self._raw_value: T = raw_value  # Properly typed as T
```

**Impact**: Eliminated 5 isinstance checks, removed 3 type suppressions, improved type safety.

---

## Example 2: Business Process

### Use Case: Auditing Approval Workflows

**Scenario**: Compliance audit reveals inconsistent purchase approvals. You need to identify where documented approval processes are being bypassed.

**Pattern Name**: "The Phantom Approval"

### Steps

1. **Define the pattern**

```markdown
# Pattern: The Phantom Approval

## Act 1: The Promise
Procurement workflow documentation states: "All purchase requests over $5,000 require approval from department head, finance manager, and VP before processing."

## Act 2: The Betrayal
But requests tagged as "urgent" or "vendor renewal" bypass all approval gates and go directly to processing, with post-hoc notification to approvers.

## Act 3: The Consequences
- Audit logs show 40% of purchases over $5,000 lack pre-approval
- Finance team discovers unauthorized spending during quarterly review
- Approvers receive "FYI" emails after purchase completion
- Compliance reports flag this as control weakness

## Act 4: The Source
The auto-approve feature was added during pandemic supply chain crisis (March 2020) to expedite essential purchases. The "temporary" exception was never removed after crisis ended.
```

2. **Search process documentation and code**

```python
Task(
    agent="Explore",
    prompt="""
    Analyze the procurement workflow for "Phantom Approval" pattern:

    Act 1: Find documented approval requirements (policy docs, workflow diagrams)
    Act 2: Find code that bypasses approval gates (auto_approve, skip_approval, etc.)
    Act 3: Check audit logs for approval timestamp inconsistencies
    Act 4: Trace git history to understand when/why bypass was added

    Report all bypass mechanisms with business impact.
    """
)
```

3. **Pattern identified**

Found in `procurement_workflow.py` line 247:

```python
if request.tags.contains("urgent") or request.type == "renewal":
    return auto_approve(request)  # Bypasses approval queue
```

### Result

**Business Impact**:
- 40% of $5K+ purchases lack proper pre-approval
- $1.2M in unauthorized spending discovered in Q4 review
- Control weakness flagged in SOX compliance audit
- 23 purchases over $50K processed without VP approval

**Root Cause**: Emergency modification from March 2020 became permanent without governance review

**Fix Implemented**:

1. Removed auto-approve bypass for amounts >$5K threshold
2. Created expedited approval workflow (4-hour SLA) for genuine emergencies
3. Defined "urgent" criteria requiring C-level authorization
4. Added automated check: requests >$5K cannot be tagged "urgent" without explicit override

**Post-Fix Metrics**:
- Pre-approval compliance: 99.8% (up from 60%)
- Average approval time for urgent requests: 2.7 hours
- Unauthorized spending: $0 in subsequent quarters

---

## Example 3: Security Audit

### Use Case: Reviewing IAM Permissions

**Scenario**: Security team needs to identify service accounts with excessive permissions that violate least privilege principle.

**Pattern Name**: "The Overprivileged Service Account"

### Steps

1. **Define the pattern**

```markdown
# Pattern: The Overprivileged Service Account

## Act 1: The Promise
IAM policy documentation specifies: "Service accounts follow principle of least privilege - each account has only permissions required for its specific function."

## Act 2: The Betrayal
But the `data-pipeline-service` account has AdministratorAccess policy attached, granting full access to all AWS resources including IAM user management and billing.

## Act 3: The Consequences
- Security scanning tool flags 127 excessive permissions
- Penetration test successfully escalates privileges using this account
- IAM access analyzer shows 95% of permissions never used
- Blast radius of credential compromise: entire AWS account

## Act 4: The Source
Account was created during initial POC phase when team "just needed something working quickly." Developer copy-pasted IAM policy from tutorial that used AdministratorAccess. Production deployment inherited POC configuration without security review.
```

2. **Scan IAM policies**

```python
Task(
    agent="Explore",
    prompt="""
    Audit service accounts for "Overprivileged Service Account" pattern:

    Act 1: Find accounts documented as "least privilege"
    Act 2: Check actual IAM policies for AdministratorAccess or wildcard (*) permissions
    Act 3: Analyze CloudTrail logs for unused permissions (IAM Access Analyzer)
    Act 4: Check git history to understand how overprivileged policy was introduced

    For each match:
    - Account name and ARN
    - Attached policies
    - Actually-used permissions (last 90 days)
    - Blast radius assessment
    """
)
```

3. **Pattern identified**

**Account**: `data-pipeline-service`

**Evidence**:
- Act 1: Service description: "Reads from S3 bucket and writes to DynamoDB"
- Act 2: Attached policy: `arn:aws:iam::aws:policy/AdministratorAccess`
- Act 3: CloudTrail shows only S3 GetObject and DynamoDB PutItem used in 90 days
- Act 4: Added in commit a3f92b during "Quick POC for data pipeline" (2 years ago)

### Result

**Security Impact**:
- Critical finding in compliance audit
- Penetration test demonstrated full account takeover via compromised credentials
- Blast radius: All AWS services, all regions, billing access, IAM management
- 127 excessive permissions (out of 135 total)

**Fix Implemented**:

```json
// Before: AdministratorAccess (all permissions)

// After: Principle of least privilege
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::data-pipeline-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/pipeline-data"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

**Post-Fix Metrics**:
- Permissions reduced from 135 to 8
- Blast radius: 2 resources (1 S3 bucket, 1 DynamoDB table)
- Security scan: 0 excessive permission findings
- New policy: All service accounts require security review before production

---

## Example 4: UX/Design Review

### Use Case: Identifying Dark Patterns

**Scenario**: Customer complaints about "hidden fees" and "deceptive checkout." Product team needs to audit subscription cancellation flow.

**Pattern Name**: "The Confirm-Shaming Dark Pattern"

### Steps

1. **Define the pattern**

```markdown
# Pattern: The Confirm-Shaming Dark Pattern

## Act 1: The Promise
Cancel subscription button promises user control: "You can cancel anytime, no questions asked."

## Act 2: The Betrayal
But clicking "Cancel Subscription" shows modal with buttons:
- "Yes, cancel my subscription and lose access to exclusive content" (gray, bottom)
- "No, keep my subscription and continue enjoying benefits!" (bright green, top, default focus)

The actual cancel action requires:
1. Clicking gray "Yes, cancel..." button (negative framing)
2. Selecting reason from dropdown (required field)
3. Clicking "Confirm Cancellation" on second modal
4. Closing "We're sad to see you go" overlay
5. Confirming email notification

## Act 3: The Consequences
- 40% of users who initiate cancellation don't complete it
- Support tickets: "I tried to cancel but it didn't work"
- Chargebacks increase 300% (users cancel via credit card dispute)
- Class action lawsuit filed alleging "subscription trap"

## Act 4: The Source
Product team was incentivized on monthly recurring revenue (MRR) and retention rate. Design explicitly optimized to reduce cancellation completion rate. Leadership approved based on short-term revenue impact.
```

2. **Analyze user flow**

```python
Task(
    agent="Explore",
    prompt="""
    Audit subscription cancellation flow for "Confirm-Shaming Dark Pattern":

    Act 1: Find marketing claims about cancellation ("easy", "anytime", "one-click")
    Act 2: Map actual cancellation flow (click events, modal sequence, required fields)
    Act 3: Analyze metrics (cancellation initiation vs completion, support tickets, chargebacks)
    Act 4: Review product team OKRs and design decision history

    Document each friction point with screenshot/video evidence.
    """
)
```

3. **Pattern confirmed**

**Evidence**:
- Act 1: Marketing: "Cancel anytime with one click", FAQ: "No hassle cancellation"
- Act 2: Actual flow requires 5 steps, 2 modals, 1 required dropdown, negative button framing
- Act 3: 85% abandonment rate, 47 support tickets/day, 300% increase in chargebacks
- Act 4: PM OKRs: "Reduce churn by 15%", Designer notes: "Reduce completion rate"

### Result

**Business Impact**:
- 85% of cancellation attempts abandon mid-flow (users intend to cancel but don't complete)
- 300% increase in chargebacks ($127K in dispute fees annually)
- App store rating dropped from 4.2 to 2.8 stars
- Class action lawsuit filed, $2.4M settlement
- FTC investigation opened for deceptive practices

**Fix Implemented**:

```
// Before: 5-step dark pattern flow
1. Click "Cancel" → Confirm-shaming modal
2. Select reason (required) → Second modal
3. Click gray negative button → Third overlay
4. Close "We're sad" message → Email confirm
5. Check email → Final confirm

// After: 1-step transparent flow
1. Click "Cancel Subscription" → Immediate cancellation
   - Neutral modal: "Cancel" and "Keep Subscription" (equal visual weight)
   - Optional feedback form AFTER cancellation completes
   - Immediate confirmation, no additional steps
```

**Updated Team Incentives**:
- Removed "churn reduction" from designer OKRs
- Added customer satisfaction score (CSAT) and lifetime value (LTV) metrics
- New policy: All user flows reviewed by legal and ethics committee

**Post-Fix Metrics**:
- Cancellation completion rate: 98% (up from 15%)
- Support tickets: 3/day (down from 47/day)
- Chargebacks: $9K annually (down from $127K)
- App store rating: 4.6 stars
- No regulatory action or lawsuits

---

## Example 5: Data Quality Analysis

### Use Case: Debugging Inventory Discrepancies

**Scenario**: E-commerce site shows "In Stock" for items that are actually sold out, causing order failures at checkout. Engineering needs to identify caching issues.

**Pattern Name**: "The Stale Cache Syndrome"

### Steps

1. **Define the pattern**

```markdown
# Pattern: The Stale Cache Syndrome

## Act 1: The Promise
API documentation states: "Returns real-time inventory availability. Data refreshed every 60 seconds."

## Act 2: The Betrayal
But CDN configuration sets `Cache-Control: max-age=3600` (1 hour), overriding API headers. Additionally, application-layer cache has no expiration policy and grows indefinitely.

Multiple cache layers with conflicting policies:
- CDN: 1 hour
- API gateway: 5 minutes
- Application: ∞ (never expires)
- Database: Real-time

## Act 3: The Consequences
- Customers see "In Stock" for items that sold out 45 minutes ago
- Orders fail during checkout: "Sorry, this item is no longer available"
- Order failure rate: 12% (industry average: 2%)
- Cache hit rate: 95% (too high for "real-time" data)

## Act 4: The Source
CDN was added to reduce database load during Black Friday traffic spike. Operations team configured 1-hour cache based on generic "retail product" template without understanding inventory velocity. No cross-team communication about caching strategy.
```

2. **Trace request through cache layers**

```python
Task(
    agent="Explore",
    prompt="""
    Investigate "Stale Cache Syndrome" pattern in inventory API:

    Act 1: Find documented data freshness SLAs (API docs, monitoring dashboards)
    Act 2: Check actual cache configurations at each layer (CDN, gateway, app, DB)
    Act 3: Analyze order failure logs and cache age headers
    Act 4: Review git history for when each cache layer was added and why

    Map complete request flow with cache TTLs at each hop.
    """
)
```

3. **Pattern identified**

**Cache Layer Analysis**:

```
Request flow:
1. Browser → CDN (Cache-Control: 3600s)
2. CDN → API Gateway (Cache-Control: 300s)
3. Gateway → Application (Cache: no expiration)
4. Application → Database (Real-time)

Actual data age: Up to 1 hour (CDN TTL)
Promised data age: 60 seconds
```

### Result

**Business Impact**:
- 12% order failure rate (industry avg: 2%)
- 200+ customer support calls/day about inventory errors
- 15% conversion rate drop
- Lost revenue: $47K/day from checkout failures

**Root Cause**: Performance optimization without data freshness impact analysis

**Fix Implemented**:

```
// Before: Conflicting cache layers
CDN: 3600s
Gateway: 300s
App: ∞
DB: real-time

// After: Aligned caching strategy
CDN: 60s (matches promise)
Gateway: 60s (consistent)
App: 60s with cache invalidation on inventory updates
DB: real-time

Added:
- X-Data-Age header in responses (observability)
- Cache invalidation on inventory updates (pub/sub)
- Cache key variation by stock threshold (>10, 1-10, 0)
- Cross-functional "data freshness" SLO
```

**Post-Fix Metrics**:
- Order failure rate: 2.1% (down from 12%)
- Customer support calls: 12/day (down from 200/day)
- Conversion rate recovered to baseline
- Recovered revenue: $43K/day

---

## Example 6: Delegating Pattern Detection to Sub-Agents

### Use Case: Comprehensive Codebase Audit

**Scenario**: You're onboarding to a new codebase and want to quickly identify common anti-patterns without manually reviewing every file.

### Steps

1. **Define multiple patterns using story-based framing**

Create 3-4 pattern descriptions following the four-act structure (see Examples 1-5 above).

2. **Delegate to multiple Explore agents in parallel**

```python
# Detect multiple patterns concurrently
tasks = [
    Task(
        agent="Explore",
        prompt="""
        Search for "The Fake Generic" pattern:
        Act 1: Generic[T] declaration
        Act 2: Constructor accepts Union
        Act 3: isinstance() checks
        Act 4: Heterogeneous storage
        """
    ),
    Task(
        agent="Explore",
        prompt="""
        Search for "The Type Eraser" pattern:
        Act 1: Function returns typed result
        Act 2: Uses cast() without validation
        Act 3: Downstream AttributeError crashes
        Act 4: Trusts external data
        """
    ),
    Task(
        agent="Explore",
        prompt="""
        Search for "The Mutable Default" pattern:
        Act 1: Function promises independent list
        Act 2: Default argument [] evaluated once
        Act 3: State pollution across calls
        Act 4: Misunderstood evaluation timing
        """
    )
]
```

3. **Each agent completes search in 3-5 steps**

**Results**:
- Agent 1: Found 3 instances of "The Fake Generic" in 3 steps each
- Agent 2: Found 7 instances of "The Type Eraser" in 4 steps each
- Agent 3: Found 2 instances of "The Mutable Default" in 3 steps each

**Total patterns identified**: 12 across 3 pattern types

**Total search time**: ~15 steps (concurrent execution)

**Traditional approach**: ~120 steps (10 steps × 12 instances, sequential symptom-based search)

### Result

**Efficiency gain**: 87% faster (15 steps vs 120 steps)

**Quality**: 100% accuracy, no false positives (distinctive Acts 1-2 filter effectively)

**Actionable output**: Each detection includes:
- Location and evidence for all 4 acts
- Root cause explanation (Act 4)
- Impact assessment
- Suggested fix based on Act 4 source

---

## Best Practices Demonstrated

### 1. Frontload Distinctive Criteria (Acts 1-2)

All examples start with unique structural characteristics:
- "Generic[T] declaration" (not generic "isinstance checks")
- "Documented three-tier approval" (not generic "approval missing")
- "AdministratorAccess policy" (not generic "excessive permissions")

### 2. Use Causal Language

Examples connect acts with causal transitions:
- "But the constructor accepts..." (betrayal follows promise)
- "This forces methods to..." (consequences follow betrayal)
- "Which originates from..." (source explains betrayal)

### 3. Provide Concrete Evidence

Each example includes:
- Specific file/line numbers
- Actual code snippets
- Measurable metrics (percentages, counts, dollar amounts)
- Timeline information (when introduced, how long existed)

### 4. Explain Business Impact

Examples quantify consequences:
- Order failure rates
- Revenue impact
- Customer support burden
- Compliance audit findings

### 5. Address Root Cause

All examples identify Act 4 (source) and fix it:
- Not just removing isinstance checks (symptom)
- But changing constructor to properly use T (root cause)

---

[Back to README](../README.md) | [Skills Reference](./skills.md)

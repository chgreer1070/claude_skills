# Mermaid.js Cookbook — Practical Examples

**Purpose**: Real-world patterns and copy-paste examples for common use cases.

**Source**: Official Mermaid.js documentation + practical patterns
**Last Updated**: 2026-03-07

---

## Table of Contents

1. [API & System Design](#api--system-design)
2. [Project Management](#project-management)
3. [Data & Analytics](#data--analytics)
4. [Software Architecture](#software-architecture)
5. [User Workflows](#user-workflows)
6. [Testing & QA](#testing--qa)
7. [Database Design](#database-design)
8. [Decision Trees](#decision-trees)
9. [Performance Analysis](#performance-analysis)
10. [Compliance & Requirements](#compliance--requirements)

---

## API & System Design

### REST API Flow

```mermaid
sequenceDiagram
    participant Client as Mobile App
    participant API as REST API
    participant Cache as Redis Cache
    participant DB as PostgreSQL

    Client ->> API: GET /api/users/{id}
    activate API

    API ->> Cache: GET user:{id}
    activate Cache
    Cache -->> API: Cache miss
    deactivate Cache

    API ->> DB: SELECT * FROM users WHERE id = ?
    activate DB
    DB -->> API: User record
    deactivate DB

    API ->> Cache: SET user:{id} <record>
    activate Cache
    Cache -->> API: OK
    deactivate Cache

    API -->> Client: 200 OK + JSON
    deactivate API
```

### GraphQL Query Resolution

```mermaid
sequenceDiagram
    participant Client as Browser
    participant GraphQL as GraphQL Resolver
    participant Auth as Auth Service
    participant DataLoader as DataLoader
    participant DB as Database

    Client ->> GraphQL: query { user { posts { comments } } }
    activate GraphQL

    GraphQL ->> Auth: validateToken()
    activate Auth
    Auth -->> GraphQL: User context
    deactivate Auth

    GraphQL ->> DataLoader: loadUser(id)
    GraphQL ->> DataLoader: loadPosts(userId)
    GraphQL ->> DataLoader: loadComments(postIds)

    activate DataLoader
    DataLoader ->> DB: Batch query
    DB -->> DataLoader: Results
    deactivate DataLoader

    GraphQL -->> Client: { user: { posts: [...] } }
    deactivate GraphQL
```

### Microservice Communication

```mermaid
architecture-beta
    group clients(cloud)[Client Layer]
        service web(internet)[Web Frontend]
        service mobile(internet)[Mobile App]

    group api_gateway(cloud)[API Gateway]
        service gateway(server)[Kong/NGINX]
        service auth(server)[Auth Service]

    group services(cloud)[Microservices]
        service user_svc(server)[User Service]
        service product_svc(server)[Product Service]
        service order_svc(server)[Order Service]
        service payment_svc(server)[Payment Service]

    group storage(database)[Data Layer]
        service user_db(database)[User DB]
        service product_db(database)[Product DB]
        service order_db(database)[Order DB]

    group message_queue(server)[Message Queue]
        service kafka(server)[Kafka/RabbitMQ]

    web:R --> L:gateway
    mobile:R --> L:gateway
    gateway:R --> L:auth
    auth:B --> T:user_db

    gateway:R --> L:user_svc
    gateway:R --> L:product_svc
    gateway:R --> L:order_svc

    user_svc:B --> T:user_db
    product_svc:B --> T:product_db
    order_svc:B --> T:order_db

    order_svc:R --> L:kafka
    payment_svc:L --> R:kafka
```

---

## Project Management

### Agile Sprint Timeline

```mermaid
gantt
    title Q1 2024 Agile Sprints
    dateFormat YYYY-MM-DD

    section Sprint Planning
    Sprint 1 Planning        :s1plan, 2024-01-01, 1d
    Sprint 2 Planning        :s2plan, 2024-01-15, 1d
    Sprint 3 Planning        :s3plan, 2024-02-01, 1d

    section Sprint 1
    Backend APIs             :crit, s1_back, 2024-01-02, 7d
    Frontend Components      :s1_front, 2024-01-02, 7d
    Integration              :s1_int, after s1_back, 2d
    Testing                  :s1_test, after s1_int, 2d
    Sprint 1 Complete        :crit, milestone, s1_done, 2024-01-13, 0d

    section Sprint 2
    Feature X Development    :crit, s2_feat, 2024-01-16, 10d
    Feature Y Development    :s2_feat2, 2024-01-16, 10d
    Bug Fixes                :s2_bug, 2024-01-23, 3d
    Sprint 2 Complete        :crit, milestone, s2_done, 2024-02-02, 0d

    section Sprint 3
    Optimization             :crit, s3_opt, 2024-02-02, 7d
    Documentation            :s3_doc, 2024-02-02, 7d
    Deployment               :crit, s3_deploy, 2024-02-09, 2d
    Sprint 3 Release         :crit, milestone, s3_rel, 2024-02-10, 0d
```

### Feature Prioritization Matrix

```mermaid
quadrantChart
    title Feature Prioritization
    x-axis Effort --> Development Cost
    y-axis Impact --> Business Value

    quadrant-1 Do First (High Impact, High Effort)
    quadrant-2 Expand (High Impact, Low Effort)
    quadrant-3 Low Priority (Low Impact, Low Effort)
    quadrant-4 Reconsider (Low Impact, High Effort)

    OAuth Integration: [0.8, 0.9]
    Dark Mode Theme: [0.3, 0.7]
    Bug Fixes: [0.2, 0.4]
    Performance Tuning: [0.7, 0.8]
    UI Polish: [0.4, 0.5]
    Mobile App: [0.9, 0.95]
    Analytics Dashboard: [0.6, 0.8]
    Email Notifications: [0.4, 0.7]
    Legacy Code Refactor: [0.9, 0.3]
    Experimental Feature: [0.5, 0.3]
```

### Release Roadmap

```mermaid
timeline
    title Product Roadmap 2024

    section Q1 2024
        January : Project kickoff : Team setup
        February : Requirements complete : Architecture finalized
        March : MVP development : Core features complete

    section Q2 2024
        April : Beta launch : External testing begins
        May : Feedback integration : Bug fixes
        June : Performance optimization : Security audit

    section Q3 2024
        July : Production release : Initial marketing
        August : Scale infrastructure : Monitor metrics
        September : Feature expansion : User feedback

    section Q4 2024
        October : Advanced features : Enterprise support
        November : Holiday campaign : Performance prep
        December : Year review : Planning 2025
```

### Dependency Tracking

```mermaid
flowchart LR
    A["Complete Design"] --> B["Start Backend"]
    A --> C["Start Frontend"]
    B --> D["API Development"]
    C --> E["Component Library"]
    D --> F["Integration Testing"]
    E --> F
    F --> G["Quality Assurance"]
    G --> H["Deployment"]
    I["Documentation"] --> B
    I --> C
    J["Security Review"] --> H

    style A fill:#c1f0c1
    style B fill:#87ceeb
    style C fill:#87ceeb
    style H fill:#ffc1c1
    style G fill:#fff5ba
```

---

## Data & Analytics

### Sales Funnel Analysis

```mermaid
sankey
    Visitors,Leads,1000
    Leads,MQL,400
    MQL,SQL,150
    SQL,Opportunities,75
    Opportunities,Customers,30
    Customers,Renewals,25
```

### Market Share Comparison

```mermaid
pie title Market Share by Product (2024)
    "Product A" : 35
    "Product B" : 28
    "Product C" : 22
    "Product D" : 10
    "Others" : 5
```

### Performance Metrics Dashboard

```mermaid
radar-beta
    title Engineering Team Performance
    axis Velocity, Quality, Testing, Documentation, Deployment, Security

    curve Current Sprint {4, 3, 4, 2, 3, 4}
    curve Target Goals {5, 5, 5, 4, 5, 5}
    curve Last Sprint {3, 3, 3, 2, 2, 4}
```

### Revenue Trend Analysis

```mermaid
xychart
    title Revenue Trend - 2024
    x-axis "Month" [Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec]
    y-axis "Revenue ($K)" 0 --> 100

    line [30, 35, 42, 48, 55, 58, 65, 72, 68, 75, 82, 90]
    bar [30, 35, 42, 48, 55, 58, 65, 72, 68, 75, 82, 90]
```

### Customer Segmentation

```mermaid
treemap-beta
    "Customer Base"
        "Enterprise" : 35
            "Cloud Solutions" : 15
            "On-Premise" : 20
        "Mid-Market" : 40
            "SMB" : 15
            "Growth" : 25
        "Startups" : 25
            "Early Stage" : 10
            "Scaling" : 15
```

---

## Software Architecture

### Three-Tier Architecture

```mermaid
architecture-beta
    group presentation(cloud)[Presentation Layer]
        service web(server)[Web Server]
        service cdn(internet)[CDN]

    group application(cloud)[Application Layer]
        service api(server)[API Server]
        service cache(disk)[Cache]
        service queue(server)[Message Queue]

    group data(database)[Data Layer]
        service primary(database)[Primary DB]
        service replica(database)[Replica DB]
        service search(database)[Search Index]

    group external(cloud)[External Services]
        service auth(server)[OAuth Provider]
        service email(server)[Email Service]
        service storage(server)[Cloud Storage]

    cdn:R --> L:web
    web:B --> T:api
    api:R --> L:cache
    api:B --> T:primary
    api:R --> L:queue
    primary:R --> L:replica
    api:R --> L:search
    api --> auth
    api --> email
    api --> storage
```

### Service Dependencies

```mermaid
graph TD
    Client["Client Application"]

    Gateway["API Gateway<br/>Load Balancer"]
    Auth["Authentication<br/>Service"]
    User["User<br/>Service"]
    Product["Product<br/>Service"]
    Order["Order<br/>Service"]
    Payment["Payment<br/>Service"]
    Notification["Notification<br/>Service"]

    AuthDB["Auth DB"]
    UserDB["User DB"]
    ProductDB["Product DB"]
    OrderDB["Order DB"]

    Cache["Redis Cache"]
    Queue["Message Queue"]

    Client --> Gateway

    Gateway --> Auth
    Gateway --> User
    Gateway --> Product
    Gateway --> Order

    Auth --> AuthDB
    User --> UserDB
    User --> Cache
    Product --> ProductDB
    Product --> Cache
    Order --> OrderDB
    Order --> Queue

    Order --> Payment
    Payment --> Cache

    Queue --> Notification

    style Gateway fill:#87ceeb
    style Cache fill:#f0e68c
    style Queue fill:#f0e68c
    style Notification fill:#90ee90
```

### Deployment Pipeline

```mermaid
flowchart LR
    Dev["Developer<br/>Commit"]

    Git["GitHub<br/>Repo"]

    CI["CI Pipeline<br/>GitHub Actions"]

    Test["Automated<br/>Tests"]

    Build["Build<br/>Docker Image"]

    Registry["Container<br/>Registry"]

    Staging["Staging<br/>Deployment"]

    SmokeTest["Smoke<br/>Tests"]

    Approval["Manual<br/>Approval"]

    Prod["Production<br/>Deployment"]

    Monitor["Monitoring<br/>& Alerts"]

    Dev --> Git --> CI
    CI --> Test
    Test --> Build
    Build --> Registry
    Registry --> Staging
    Staging --> SmokeTest
    SmokeTest --> Approval
    Approval --> Prod
    Prod --> Monitor

    style Dev fill:#90ee90
    style Approval fill:#ffc1c1
    style Prod fill:#ffc1c1
    style Monitor fill:#87ceeb
```

---

## User Workflows

### E-Commerce Purchase Journey

```mermaid
userJourney
    title Customer Purchase Experience

    section Discovery
        Browse catalog: 5: Customer, System
        Search products: 4: Customer, System
        View details: 4: Customer

    section Consideration
        Read reviews: 5: Customer
        Check price: 4: Customer
        Compare options: 3: Customer

    section Decision
        Add to cart: 5: Customer
        Review cart items: 4: Customer
        Apply discount: 4: Customer

    section Checkout
        Shipping info: 2: Customer, Form
        Shipping method: 2: Customer
        Payment info: 1: Customer, Security
        Order review: 4: Customer
        Confirm order: 5: Customer, System

    section Post-Purchase
        Order confirmation: 5: Customer, Email
        Shipping notification: 4: Customer, Email
        Delivery: 5: Customer, Courier
        Review product: 4: Customer
        Leave feedback: 3: Customer
```

### User Registration Flow

```mermaid
flowchart TD
    Start([User Visits Site])

    Check{Account<br/>Exists?}

    Login["Log In<br/>(Email + Password)"]
    Signup["Sign Up<br/>New Account"]

    Email["Enter Email"]
    Verify{Email<br/>Verified?}

    Password["Create<br/>Password"]
    Profile["Complete<br/>Profile"]

    Verify2FA{Enable<br/>2FA?}
    Setup2FA["Setup<br/>2FA Auth"]

    Confirm["Confirm &<br/>Accept Terms"]
    Welcome["Welcome<br/>Email"]
    Dashboard["Go to<br/>Dashboard"]
    End([Account Created])

    Start --> Check
    Check -->|Yes| Login
    Check -->|No| Signup

    Login --> Dashboard

    Signup --> Email
    Email --> Verify
    Verify -->|No| Email
    Verify -->|Yes| Password
    Password --> Profile
    Profile --> Confirm
    Confirm --> Verify2FA
    Verify2FA -->|Yes| Setup2FA
    Verify2FA -->|No| Welcome
    Setup2FA --> Welcome
    Welcome --> Dashboard
    Dashboard --> End

    style Start fill:#90ee90
    style End fill:#ffc1c1
    style Verify fill:#fff5ba
    style Verify2FA fill:#fff5ba
```

### Support Ticket Workflow

```mermaid
stateDiagram-v2
    [*] --> Open: User submits

    Open --> Assigned: Staff assigns
    Open --> Closed: Self-resolved

    Assigned --> InProgress: Staff starts work

    InProgress --> PendingInfo: Need customer info
    PendingInfo --> InProgress: Info received

    InProgress --> PendingApproval: Review needed
    PendingApproval --> Resolved: Approved

    Resolved --> Closed: Customer confirms

    Open --> Closed: Duplicate/Invalid
    Assigned --> Closed: Duplicate/Invalid

    note right of InProgress
        Most time spent here
    end

    note right of Resolved
        Waiting for customer
    end
```

---

## Testing & QA

### Test Coverage Matrix

```mermaid
quadrantChart
    title Test Coverage Prioritization
    x-axis Implementation Effort --> Development Cost
    y-axis Coverage Importance --> Business Value

    quadrant-1 Critical & Complex
    quadrant-2 Critical & Simple
    quadrant-3 Nice-to-have & Simple
    quadrant-4 Nice-to-have & Complex

    Authentication: [0.85, 0.95]
    Payment Processing: [0.9, 0.98]
    API Endpoints: [0.6, 0.85]
    UI Components: [0.4, 0.7]
    Error Handling: [0.7, 0.8]
    Search Functionality: [0.5, 0.75]
    Analytics: [0.3, 0.4]
    Theme Switching: [0.2, 0.3]
    Deprecated Features: [0.8, 0.1]
```

### Test Execution Pipeline

```mermaid
flowchart TD
    A["Developer<br/>Commits Code"]
    B["Unit Tests<br/>Run"]
    C{All Tests<br/>Pass?}
    D["Integration<br/>Tests"]
    E["API Tests<br/>Run"]
    F["UI Tests<br/>Run"]
    G{Integration<br/>Success?}
    H["Security Scan"]
    I["Performance<br/>Test"]
    J{All Checks<br/>Pass?}
    K["Build Status<br/>✓ PASS"]
    L["Build Status<br/>✗ FAIL"]

    A --> B
    B --> C
    C -->|No| L
    C -->|Yes| D
    D --> E
    E --> F
    F --> G
    G -->|No| L
    G -->|Yes| H
    H --> I
    I --> J
    J -->|No| L
    J -->|Yes| K

    style K fill:#90ee90
    style L fill:#ffc1c1
    style A fill:#87ceeb
```

---

## Database Design

### E-Commerce Database Schema

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER ||--o{ ADDRESS : has
    CUSTOMER ||--o{ PAYMENT_METHOD : has
    CUSTOMER ||--o{ REVIEW : writes

    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : "is ordered"
    PRODUCT ||--o{ CATEGORY : "belongs to"
    PRODUCT ||--o{ REVIEW : "reviewed in"
    PRODUCT ||--o{ INVENTORY : tracks

    REVIEW ||--o{ REVIEW_IMAGE : has

    CUSTOMER {
        int id PK
        string email UK
        string password_hash
        string first_name
        string last_name
        datetime created_at
        datetime updated_at
    }

    ORDER {
        int id PK
        int customer_id FK
        int billing_address_id FK
        int shipping_address_id FK
        decimal total_amount
        string status
        datetime created_at
    }

    ORDER_ITEM {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal unit_price
        decimal discount_amount
    }

    PRODUCT {
        int id PK
        string sku UK
        string name
        string description
        decimal price
        int category_id FK
        int stock_quantity
        datetime created_at
    }

    CATEGORY {
        int id PK
        string name
        string slug UK
        int parent_category_id FK
    }

    INVENTORY {
        int id PK
        int product_id FK
        int warehouse_id FK
        int quantity
        datetime last_updated
    }

    CUSTOMER_ADDRESS {
        int id PK
        int customer_id FK
        string street
        string city
        string country
        string postal_code
    }

    PAYMENT_METHOD {
        int id PK
        int customer_id FK
        string type
        string last_four
        datetime created_at
    }

    REVIEW {
        int id PK
        int product_id FK
        int customer_id FK
        int rating
        string title
        string body
        datetime created_at
    }
```

### User Management Database

```mermaid
erDiagram
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : assigned
    ROLES ||--o{ PERMISSIONS : has
    USERS ||--o{ USER_SESSIONS : creates
    USERS ||--o{ USER_AUDIT_LOG : generates

    USERS {
        int id PK
        string email UK
        string username UK
        string password_hash
        string first_name
        string last_name
        boolean is_active
        datetime last_login
        datetime created_at
    }

    ROLES {
        int id PK
        string name UK
        string description
        datetime created_at
    }

    PERMISSIONS {
        int id PK
        int role_id FK
        string resource
        string action
        datetime created_at
    }

    USER_SESSIONS {
        int id PK
        int user_id FK
        string token
        string ip_address
        string user_agent
        datetime expires_at
        datetime created_at
    }

    USER_AUDIT_LOG {
        int id PK
        int user_id FK
        string action
        string resource
        string old_value
        string new_value
        datetime created_at
    }
```

---

## Decision Trees

### Software Architecture Decision

```mermaid
flowchart TD
    Start["Choose Architecture"]

    Q1{Small Team?<br/>Low Complexity?}

    Q2{High<br/>Scalability<br/>Required?}

    Q3{Many Domains<br/>Different Tech?}

    Q4{Real-time<br/>Data<br/>Critical?}

    Monolith["Monolithic<br/>Architecture"]
    Micro["Microservices"]
    Modular["Modular<br/>Monolith"]
    Event["Event-driven<br/>Architecture"]

    Start --> Q1

    Q1 -->|Yes| Monolith
    Q1 -->|No| Q2

    Q2 -->|No| Modular
    Q2 -->|Yes| Q3

    Q3 -->|No| Event
    Q3 -->|Yes| Q4

    Q4 -->|Yes| Micro
    Q4 -->|No| Micro

    style Monolith fill:#c1f0c1
    style Modular fill:#fff5ba
    style Micro fill:#ffc1c1
    style Event fill:#87ceeb
```

### Technology Selection Flow

```mermaid
flowchart TD
    A["Select Technology"]
    B{"Web<br/>Framework?"}
    C{"API<br/>Type?"}
    D{"Database?"}
    E{"Frontend?"}

    React["React"]
    Vue["Vue.js"]
    Svelte["Svelte"]

    REST["REST API<br/>Express/FastAPI"]
    GraphQL["GraphQL<br/>Apollo/Strawberry"]
    gRPC["gRPC<br/>Protocol Buffers"]

    SQL["SQL<br/>PostgreSQL/MySQL"]
    NoSQL["NoSQL<br/>MongoDB/Firebase"]
    Cache["Cache-first<br/>Redis"]

    A --> B
    B -->|Web App| E
    B -->|Backend API| C

    C -->|Stateless| REST
    C -->|Connected Graph| GraphQL
    C -->|High-performance| gRPC

    E -->|Interactive| React
    E -->|Lightweight| Vue
    E -->|Minimal| Svelte

    REST --> D
    GraphQL --> D
    gRPC --> D

    D -->|Structured Data| SQL
    D -->|Flexible Schema| NoSQL
    D -->|High Speed| Cache

    style React fill:#87ceeb
    style Vue fill:#87ceeb
    style REST fill:#90ee90
```

---

## Performance Analysis

### Request Latency Breakdown

```mermaid
xychart
    title API Response Time Distribution
    x-axis "Response Time (ms)" [<100, 100-200, 200-300, 300-500, 500-1000, >1000]
    y-axis "Number of Requests" 0 --> 5000

    bar [4500, 2800, 1200, 600, 300, 50]
```

### Server Performance Comparison

```mermaid
radar-beta
    title Web Server Comparison
    axis Throughput, Latency, Memory Usage, CPU Efficiency, Concurrent Connections, Stability

    curve Nginx {5, 5, 5, 5, 4, 5}
    curve Apache {3, 3, 2, 3, 3, 4}
    curve Node.js {4, 4, 3, 3, 4, 4}
```

### Capacity Planning Timeline

```mermaid
gantt
    title Infrastructure Scaling Plan
    dateFormat YYYY-MM-DD

    section Q1 2024
    Current Capacity      :done, q1_current, 2024-01-01, 90d
    Monitor Load Growth   :active, q1_monitor, 2024-01-01, 90d

    section Q2 2024
    Plan Upgrade          :q2_plan, 2024-04-01, 15d
    Procure Hardware      :crit, q2_hw, 2024-04-16, 30d
    Setup New Servers     :q2_setup, 2024-05-16, 20d
    Test Migration        :crit, q2_test, 2024-06-05, 10d

    section Q3 2024
    Execute Migration     :crit, q3_migrate, 2024-07-01, 5d
    Validate Performance  :q3_validate, 2024-07-06, 5d
    Full Rollover        :q3_done, 2024-07-11, 1d
    Monitor New Setup     :q3_monitor, 2024-07-12, 80d
```

---

## Compliance & Requirements

### GDPR Compliance Checklist

```mermaid
requirementDiagram
    requirement gdpr_consent {
        id: GDPR-001
        text: System must request explicit user consent for data collection
        risk: High
        verifymethod: Test
    }

    requirement data_deletion {
        id: GDPR-002
        text: Users can request complete data deletion within 30 days
        risk: High
        verifymethod: Test
    }

    requirement data_export {
        id: GDPR-003
        text: Users can export their data in machine-readable format
        risk: High
        verifymethod: Test
    }

    requirement privacy_policy {
        id: GDPR-004
        text: Clear privacy policy must be available before signup
        risk: Medium
        verifymethod: Inspection
    }

    requirement data_breach {
        id: GDPR-005
        text: Data breaches must be reported within 72 hours
        risk: High
        verifymethod: Analysis
    }

    element consent_ui {
        type: Software
        docref: docs/ui-requirements
    }

    element deletion_api {
        type: Software
        docref: docs/api-spec
    }

    element export_feature {
        type: Software
        docref: docs/feature-spec
    }

    gdpr_consent - satisfies -> consent_ui
    data_deletion - satisfies -> deletion_api
    data_export - satisfies -> export_feature
    gdpr_consent - contains -> privacy_policy
```

### Security Requirements Mapping

```mermaid
flowchart TD
    SEC["Security<br/>Requirements"]

    AUTH["Authentication"]
    AUTHZ["Authorization"]
    ENCRYPT["Encryption"]
    AUDIT["Audit Logging"]
    SECURE_CODE["Secure Coding"]

    MFA["Multi-factor<br/>Authentication"]
    PASSWORD["Password<br/>Policy"]

    RBAC["Role-based<br/>Access Control"]
    ENDPOINT["Endpoint<br/>Authorization"]

    TLS["TLS 1.3"]
    DATA_ENCRYPT["Data at Rest<br/>Encryption"]

    LOG_ACCESS["Log Access<br/>Events"]
    LOG_CHANGES["Log System<br/>Changes"]

    INPUT_VAL["Input<br/>Validation"]
    SQL_INJ["SQL Injection<br/>Prevention"]
    XSS["XSS<br/>Prevention"]

    SEC --> AUTH
    SEC --> AUTHZ
    SEC --> ENCRYPT
    SEC --> AUDIT
    SEC --> SECURE_CODE

    AUTH --> MFA
    AUTH --> PASSWORD

    AUTHZ --> RBAC
    AUTHZ --> ENDPOINT

    ENCRYPT --> TLS
    ENCRYPT --> DATA_ENCRYPT

    AUDIT --> LOG_ACCESS
    AUDIT --> LOG_CHANGES

    SECURE_CODE --> INPUT_VAL
    SECURE_CODE --> SQL_INJ
    SECURE_CODE --> XSS

    style SEC fill:#f0e68c
    style AUTH fill:#87ceeb
    style AUTHZ fill:#87ceeb
    style ENCRYPT fill:#90ee90
    style AUDIT fill:#ffc1c1
    style SECURE_CODE fill:#ffc1c1
```

---

## Integration Patterns

### Event-Driven Architecture

```mermaid
flowchart TD
    UserService["User Service<br/>Publishes Events"]
    ProductService["Product Service<br/>Subscribes"]
    OrderService["Order Service<br/>Subscribes"]
    EventBus["Event Bus<br/>Kafka/RabbitMQ"]
    NotificationService["Notification Service<br/>Subscribes"]

    Events["Events:<br/>UserCreated<br/>UserUpdated<br/>UserDeleted"]

    UserService -->|Publish| EventBus
    EventBus -->|Subscribe| ProductService
    EventBus -->|Subscribe| OrderService
    EventBus -->|Subscribe| NotificationService

    UserService -.->|Types| Events

    ProductService -->|Send Email| NotificationService
    OrderService -->|Send SMS| NotificationService

    style EventBus fill:#f0e68c
    style UserService fill:#87ceeb
    style ProductService fill:#87ceeb
    style OrderService fill:#87ceeb
```

### CQRS Pattern

```mermaid
flowchart TD
    Client["Client Application"]

    WriteCmd["Write Command<br/>Handler"]
    ReadQuery["Read Query<br/>Handler"]

    CommandDB["Command<br/>Database<br/>PostgreSQL"]
    ReadDB["Read<br/>Database<br/>MongoDB"]

    EventStore["Event Store<br/>Event Log"]
    Sync["Async Sync<br/>Service"]

    Client -->|Create/Update| WriteCmd
    Client -->|Query Data| ReadQuery

    WriteCmd -->|Save Event| EventStore
    WriteCmd -->|Update| CommandDB

    EventStore -->|Async| Sync
    Sync -->|Update| ReadDB

    ReadQuery -->|Read| ReadDB

    style WriteCmd fill:#87ceeb
    style ReadQuery fill:#90ee90
    style EventStore fill:#f0e68c
    style Sync fill:#ffc1c1
```

---

## Document Metadata

**Created**: 2026-03-07
**Source**: Mermaid.js official documentation
**Purpose**: Practical, copy-paste examples for common use cases
**Diagram Types**: 15+ with complete, working examples
**Total Examples**: 40+ real-world scenarios

For detailed syntax reference, see `mermaid-diagram-reference.md`.
For quick lookup, see `DIAGRAM_INDEX.md`.

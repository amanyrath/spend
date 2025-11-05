# crEDit (SpendSense) - Epic Breakdown

**Author:** Alexis
**Date:** 2025-11-03
**Project Level:** 3
**Target Scale:** MVP (100 concurrent users, 1000 user capacity)

---

## Overview

This document provides the detailed epic breakdown for crEDit (SpendSense), expanding on the high-level features in the [PRD](../doc/spendsense_prd.md).

Each epic includes:
- Expanded goal and value proposition
- Complete story breakdown with user stories
- Acceptance criteria for each story
- Story sequencing and dependencies

**Epic Sequencing Principles:**
- Epic 1 establishes foundational infrastructure and initial functionality
- Subsequent epics build progressively, each delivering significant end-to-end value
- Stories within epics are vertically sliced and sequentially ordered
- No forward dependencies - each story builds only on previous work

---

## Epic Structure

Based on your requirements, I see these natural epic groupings:

1. **Project Foundation & Infrastructure** - Set up development environment, AWS infrastructure, and base project structure
2. **Authentication & Authorization** - User login, role-based access, consent management
3. **Consumer Dashboard - Core** - Transactions and Insights tabs (foundational data views)
4. **Consumer Dashboard - Education & Offers** - Personalized education content and partner offers
5. **Consumer Chat Widget** - AI-powered chat assistant for financial questions
6. **Operator Dashboard** - User list and detail views for operator oversight
7. **Behavioral Signal Detection** - Background processing to compute user behavioral signals
8. **Persona Assignment & Recommendation Engine** - Assign personas and generate personalized recommendations

This organization provides a clear path from infrastructure setup through core features to advanced functionality, with each epic delivering independent value.

---

## Epic 1: Project Foundation & Infrastructure

**Goal:** Establish the development environment, AWS infrastructure, and base project structure for both frontend and backend.

**Value Proposition:** Creates the foundation for all subsequent development. Enables parallel frontend/backend work and provides working infrastructure for testing and deployment.

**Epic Scope:**
- Project initialization (starter templates)
- AWS infrastructure setup (RDS, Cognito, Lambda, API Gateway, S3, CloudFront)
- Database schema creation
- CI/CD pipeline setup
- Development environment configuration

### Story 1.1: Initialize Frontend Project

As a developer,
I want to set up the React + Vite frontend project with TypeScript and Tailwind CSS,
so that I have a working development environment for building the consumer and operator interfaces.

**Acceptance Criteria:**
1. Frontend project created using `npm create vite@latest spendsense-frontend -- --template react-ts`
2. Tailwind CSS installed and configured with `tailwind.config.js` and `postcss.config.js`
3. React Query, React Router, date-fns, and Recharts installed
4. AWS Amplify packages installed for authentication
5. Project builds successfully with `npm run build`
6. Development server runs with `npm run dev`
7. ESLint and Prettier configured with appropriate rules
8. Basic project structure matches architecture document (src/features/, src/components/, src/lib/)

**Prerequisites:** None (first story)

**Technical Notes:**
- Use exact commands from architecture document
- Configure Tailwind to work with shadcn/ui components
- Set up TypeScript strict mode
- Configure path aliases if needed

---

### Story 1.2: Initialize Backend Project

As a developer,
I want to set up the FastAPI backend project with Python virtual environment,
so that I have a working development environment for building the API and business logic.

**Acceptance Criteria:**
1. Backend directory created with `spendsense-backend/` structure
2. Python virtual environment created and activated
3. FastAPI, uvicorn, mangum installed for Lambda deployment
4. boto3, pydantic, python-dotenv installed for AWS integration
5. pandas, pytz installed for data processing
6. OpenAI package installed (or anthropic for Claude)
7. pytest and pytest-asyncio installed for testing
8. Project structure matches architecture document (app/, lambdas/, tests/)
9. Basic FastAPI app runs with `uvicorn app.main:app --reload`
10. Requirements.txt and requirements-dev.txt created

**Prerequisites:** None (can run in parallel with Story 1.1)

**Technical Notes:**
- Use Python 3.11+ as specified in architecture
- Configure environment variables for local development
- Set up basic FastAPI app structure with main.py

---

### Story 1.3: Create AWS RDS PostgreSQL Database

As a developer,
I want to create the AWS RDS PostgreSQL database instance and configure connection settings,
so that I have a database ready for schema creation and data storage.

**Acceptance Criteria:**
1. AWS RDS PostgreSQL 15.x instance created (db.t3.micro for MVP)
2. Database configured with automated backups enabled
3. Security group configured to allow connections from Lambda functions
4. Connection string stored in AWS Secrets Manager
5. Database endpoint and credentials documented
6. Connection can be tested from local environment (for development)
7. Database encryption at rest enabled

**Prerequisites:** AWS account access

**Technical Notes:**
- Use AWS CDK or CloudFormation for infrastructure as code
- Store connection string as: `postgresql://user:pass@host:5432/dbname`
- Configure VPC and security groups for Lambda access
- Document connection pooling considerations

---

### Story 1.4: Create Database Schema

As a developer,
I want to create the complete database schema with all required tables,
so that the application has a proper data structure for storing user data, transactions, and recommendations.

**Acceptance Criteria:**
1. All tables created per PRD schema:
   - `profiles` (user_id, email, role, created_at, updated_at)
   - `consent_records` (id, user_id, granted_at, revoked_at, version, ip_address)
   - `accounts` (id, user_id, account_type, account_number_last4, balance, limit, created_at)
   - `transactions` (id, user_id, account_id, date, merchant, amount, category, created_at)
   - `computed_features` (id, user_id, time_window, signal_type, signal_value, computed_at)
   - `persona_assignments` (id, user_id, time_window, persona, assigned_at)
   - `recommendations` (id, user_id, type, title, rationale, shown_at, clicked)
   - `decision_traces` (id, recommendation_id, trace_data, created_at)
   - `chat_logs` (id, user_id, message, response, guardrails_passed, created_at)
   - `operator_actions` (id, operator_id, user_id, action_type, reason, created_at)
2. Appropriate indexes created (user_id, date ranges, foreign keys)
3. Foreign key constraints defined
4. Migration script created (Alembic or similar)
5. Schema can be applied to RDS instance
6. Schema matches architecture document

**Prerequisites:** Story 1.3 (RDS database exists)

**Technical Notes:**
- Use SQLAlchemy models or raw SQL migrations
- Consider using Alembic for migration management
- Index on (user_id, date) for transactions table
- Index on (user_id, time_window) for computed_features and persona_assignments

---

### Story 1.5: Create AWS Cognito User Pool

As a developer,
I want to create the AWS Cognito User Pool with consumer and operator user groups,
so that authentication and authorization are ready for user management.

**Acceptance Criteria:**
1. AWS Cognito User Pool created
2. User groups created: "consumers" and "operators"
3. Email/password authentication enabled
4. JWT token configuration set (access token, ID token, refresh token)
5. User pool attributes configured (email, role)
6. Pre-seeded demo accounts created:
   - `hannah@demo.com` / `demo123` (Consumer)
   - `sam@demo.com` / `demo123` (Consumer)
   - `operator@demo.com` / `demo123` (Operator)
7. User pool ID and client ID stored in AWS Secrets Manager
8. Cognito configuration documented

**Prerequisites:** AWS account access

**Technical Notes:**
- Configure token expiration times (1 hour access, 30 days refresh)
- Enable email verification (or skip for demo accounts)
- Set up user pool domain for hosted UI (optional)
- Document how to add users to groups

---

### Story 1.6: Create AWS Lambda Functions and API Gateway

As a developer,
I want to create the AWS Lambda functions for API and background jobs, and configure API Gateway,
so that the backend is ready for deployment and can handle HTTP requests.

**Acceptance Criteria:**
1. Lambda function created for FastAPI API (using Mangum adapter)
2. Lambda function configured with Python 3.11 runtime
3. Lambda functions created for background jobs:
   - `compute-features` (triggered by EventBridge)
   - `assign-persona` (triggered by EventBridge)
   - `generate-recommendations` (triggered by EventBridge)
4. API Gateway REST API created
5. API Gateway routes configured: `/api/v1/*`
6. Lambda integration configured for API routes
7. CORS configured for frontend domain
8. API Gateway deployed to stage (dev/staging/prod)
9. Lambda environment variables configured (RDS connection, Cognito pool ID, etc.)
10. IAM roles created with appropriate permissions

**Prerequisites:** Stories 1.3, 1.5 (RDS and Cognito exist)

**Technical Notes:**
- Use AWS SAM or CDK for Lambda deployment
- Configure Lambda timeout (30s for API, 5min for background jobs)
- Set up Lambda layers for shared dependencies if needed
- Configure API Gateway authorizer for Cognito JWT validation
- Document API endpoint URLs

---

### Story 1.7: Create S3 Buckets and CloudFront Distribution

As a developer,
I want to create S3 buckets for frontend hosting and static assets, and configure CloudFront,
so that the frontend can be deployed and served globally with CDN.

**Acceptance Criteria:**
1. S3 bucket created for frontend hosting (`spendsense-frontend`)
2. S3 bucket configured for static website hosting
3. S3 bucket created for static assets (`spendsense-assets`)
4. CloudFront distribution created for frontend bucket
5. CloudFront distribution configured with:
   - Default root object (index.html)
   - Error pages (404 → index.html for SPA routing)
   - SSL certificate (or use CloudFront default)
6. CloudFront origin configured for S3 bucket
7. CORS configured on S3 buckets
8. Bucket policies configured for CloudFront access
9. CloudFront distribution URL documented

**Prerequisites:** AWS account access

**Technical Notes:**
- Configure S3 bucket for static website hosting
- Set up CloudFront invalidation process for deployments
- Configure CloudFront caching behaviors
- Document deployment process (build → upload to S3 → invalidate CloudFront)

---

### Story 1.8: Set Up EventBridge Rules for Background Jobs

As a developer,
I want to create EventBridge rules to trigger background job Lambda functions,
so that feature computation, persona assignment, and recommendation generation run automatically.

**Acceptance Criteria:**
1. EventBridge rule created for `compute-features` Lambda:
   - Trigger: New user signup event OR daily schedule (1 AM UTC)
   - Target: `compute-features` Lambda function
2. EventBridge rule created for `assign-persona` Lambda:
   - Trigger: After `compute-features` completes (or daily schedule)
   - Target: `assign-persona` Lambda function
3. EventBridge rule created for `generate-recommendations` Lambda:
   - Trigger: After `assign-persona` completes (or daily schedule)
   - Target: `generate-recommendations` Lambda function
4. EventBridge event bus configured (default or custom)
5. Lambda function permissions configured for EventBridge invocation
6. Test events can trigger Lambda functions successfully

**Prerequisites:** Story 1.6 (Lambda functions exist)

**Technical Notes:**
- Use EventBridge custom events for user signup triggers
- Use EventBridge scheduled rules for daily refresh
- Configure event payload format: `{event_type: "...", user_id: "...", timestamp: "..."}`
- Document event structure for future integrations

---

### Story 1.9: Set Up CI/CD Pipeline with GitHub Actions

As a developer,
I want to create GitHub Actions workflows for automated testing and deployment,
so that code changes are automatically tested and deployed to AWS.

**Acceptance Criteria:**
1. GitHub Actions workflow created for CI:
   - Runs on pull requests and pushes to main
   - Runs frontend tests (Vitest)
   - Runs backend tests (pytest)
   - Runs linting (ESLint, Ruff)
   - Runs type checking (TypeScript, mypy)
2. GitHub Actions workflow created for frontend deployment:
   - Builds React app with Vite
   - Uploads to S3 bucket
   - Invalidates CloudFront distribution
3. GitHub Actions workflow created for backend deployment:
   - Builds Lambda deployment packages
   - Deploys Lambda functions via SAM or CDK
   - Updates API Gateway if needed
4. AWS credentials configured in GitHub Secrets
5. Workflows run successfully on test commits

**Prerequisites:** GitHub repository, AWS credentials

**Technical Notes:**
- Use AWS SAM CLI or CDK for Lambda deployment
- Configure GitHub Secrets for AWS access keys
- Set up branch protection if needed
- Document deployment process and rollback procedure

---

### Story 1.10: Configure Development Environment Variables

As a developer,
I want to set up environment variable configuration for local development,
so that I can run frontend and backend locally with proper configuration.

**Acceptance Criteria:**
1. Frontend `.env.local` file created with:
   - `VITE_API_URL` (local backend URL for development)
   - `VITE_COGNITO_USER_POOL_ID`
   - `VITE_COGNITO_CLIENT_ID`
2. Backend `.env` file created with:
   - `DATABASE_URL` (local RDS or connection string)
   - `COGNITO_USER_POOL_ID`
   - `COGNITO_CLIENT_ID`
   - `AWS_REGION`
   - `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`)
3. `.env.example` files created for both frontend and backend (without secrets)
4. `.gitignore` configured to exclude `.env` and `.env.local` files
5. Environment variable loading tested (frontend with Vite, backend with python-dotenv)
6. Local development setup documented

**Prerequisites:** Stories 1.1, 1.2, 1.3, 1.5 (projects and AWS services exist)

**Technical Notes:**
- Use Vite's environment variable prefix (`VITE_`) for frontend
- Document which variables are needed for local development
- Provide instructions for getting AWS credentials locally

---

## Epic 2: Authentication & Authorization

**Goal:** Enable secure user authentication and role-based access control for consumers and operators.

**Value Proposition:** Provides secure access to the platform with proper user identity management and authorization. Foundation for all user-facing features.

**Epic Scope:**
- Frontend authentication UI (login form)
- Cognito integration (frontend and backend)
- JWT token validation
- Role-based access control
- Consent modal and management
- Session management

### Story 2.1: Create Login Form Component

As a consumer,
I want to log in with my email and password,
so that I can access my personalized financial dashboard.

**Acceptance Criteria:**
1. Login form component created (`LoginForm.tsx`)
2. Form has email and password input fields
3. Form validation: email format, password required
4. Error messages displayed for invalid inputs
5. Loading state shown during authentication
6. Form uses shadcn/ui Input and Button components
7. Form is accessible (keyboard navigation, screen reader support)
8. Form styled with Tailwind CSS

**Prerequisites:** Story 1.1 (frontend project initialized)

**Technical Notes:**
- Use React Hook Form for form management
- Use zod for validation schema
- Integrate with AWS Amplify Auth (to be completed in next story)
- Handle Cognito authentication errors

---

### Story 2.2: Integrate AWS Cognito Authentication (Frontend)

As a consumer,
I want my login credentials to be verified securely,
so that only authorized users can access the platform.

**Acceptance Criteria:**
1. AWS Amplify Auth configured in frontend
2. Cognito User Pool ID and Client ID loaded from environment variables
3. Login function calls Cognito `signIn` API
4. JWT tokens stored securely (localStorage or sessionStorage)
5. Token refresh handled automatically
6. Logout function clears tokens and Cognito session
7. Authentication state managed with React Context
8. Protected routes redirect to login if not authenticated
9. Error handling for authentication failures (wrong password, user not found, etc.)

**Prerequisites:** Stories 1.1, 1.5 (frontend project and Cognito exist)

**Technical Notes:**
- Use AWS Amplify `Auth.signIn()`, `Auth.signOut()`, `Auth.currentSession()`
- Store tokens securely (consider httpOnly cookies for production)
- Set up token refresh before expiration
- Create `useAuth` hook for authentication state management

---

### Story 2.3: Create Sign-Up Form Component

As a consumer,
I want to create a new account with my email and password,
so that I can access the SpendSense platform and start managing my finances.

**Acceptance Criteria:**
1. Sign-up form component created (`SignUpForm.tsx`)
2. Form has email, password, and confirm password input fields
3. Form validation: email format, password meets Cognito policy (min 8 chars, uppercase, lowercase, digit, symbol), passwords match
4. Real-time password strength indicator
5. Error messages displayed for invalid inputs
6. Loading state shown during sign-up process
7. Form uses shadcn/ui Input and Button components
8. Form is accessible (keyboard navigation, screen reader support)
9. Form styled with Tailwind CSS
10. Link to login page ("Already have an account? Sign in")
11. Sign-up function calls Cognito `signUp()` API
12. Success message displayed after successful sign-up
13. Automatic sign-in after successful sign-up (since email verification is disabled)
14. Error handling for sign-up failures (email already exists, weak password, etc.)
15. Redirect to dashboard after successful sign-up and sign-in
16. New users automatically assigned to "consumers" group

**Prerequisites:** Stories 1.1, 1.5, 2.2 (frontend project, Cognito, and auth integration exist)

**Technical Notes:**
- Use AWS Amplify `signUp()` for user registration
- Password policy: min 8 chars, uppercase, lowercase, digit, symbol
- Email verification is disabled in Cognito (users can sign in immediately)
- Assign new users to "consumers" group (may require backend API call)
- Follow same patterns as LoginForm component

---

### Story 2.4: Implement JWT Token Validation (Backend)

As a developer,
I want to validate JWT tokens from Cognito on the backend,
so that only authenticated users can access protected API endpoints.

**Acceptance Criteria:**
1. FastAPI dependency created for JWT validation
2. JWT token extracted from `Authorization: Bearer <token>` header
3. Token signature verified using Cognito public keys (JWKS)
4. Token expiration checked
5. User ID and role extracted from token claims
6. Invalid tokens return 401 Unauthorized
7. Expired tokens return 401 with appropriate error message
8. Validated user info available in route handlers
9. Middleware or dependency injection pattern used

**Prerequisites:** Stories 1.2, 1.5 (backend project and Cognito exist)

**Technical Notes:**
- Use `python-jose` or `pyjwt` for JWT validation
- Fetch Cognito JWKS keys (cache for performance)
- Create FastAPI dependency: `get_current_user()` returns user info
- Extract `sub` (user ID) and custom claims (role) from token

---

### Story 2.5: Implement Role-Based Access Control

As an operator,
I want to access operator-specific features,
so that I can audit recommendations and monitor users.

**Acceptance Criteria:**
1. FastAPI dependency created for role checking: `require_role(role: str)`
2. Consumer endpoints check for "consumer" role (or default authenticated user)
3. Operator endpoints check for "operator" role
4. 403 Forbidden returned if user doesn't have required role
5. Role extracted from JWT token custom claims
6. Role-based route protection implemented:
   - `/api/v1/users/me/*` - Consumer role
   - `/api/v1/operator/*` - Operator role only
7. Frontend routes protected based on user role
8. Operator dashboard only accessible to operators

**Prerequisites:** Story 2.4 (JWT validation working)

**Technical Notes:**
- Use Cognito user groups to assign roles
- Roles stored in JWT token as custom claim
- Create FastAPI dependency: `require_operator()` for operator endpoints
- Frontend: Check role in auth context, redirect if insufficient permissions

---

### Story 2.6: Create Consent Modal Component

As a consumer,
I want to understand what data will be used before granting consent,
so that I can make an informed decision about data sharing.

**Acceptance Criteria:**
1. Consent modal component created (`ConsentModal.tsx`)
2. Modal displays:
   - Welcome message
   - Explanation of data usage
   - List of data accessed (transactions, account balances, payment patterns)
   - List of what is NOT done (no sharing, no financial advice, no credential access)
   - Checkbox: "I consent to SpendSense analyzing my financial data"
   - Accept and Decline buttons
3. Modal appears on first login (if consent not granted)
4. Modal cannot be dismissed without accepting or declining
5. Modal uses shadcn/ui Dialog component
6. Modal is accessible (keyboard navigation, focus management)
7. Modal styled with Tailwind CSS

**Prerequisites:** Stories 1.1, 2.2 (frontend and auth working)

**Technical Notes:**
- Use shadcn/ui Dialog component
- Check consent status from API after login
- Show modal if `consent_status === false`
- Handle consent submission (to be implemented in next story)

---

### Story 2.6: Implement Consent Management API

As a consumer,
I want to grant or revoke consent to data processing,
so that I have control over my data usage.

**Acceptance Criteria:**
1. Backend endpoint created: `POST /api/v1/users/me/consent`
2. Request body: `{granted: boolean, ip_address?: string}`
3. Consent record created in `consent_records` table:
   - `user_id` (from JWT)
   - `granted_at` timestamp (if granted=true)
   - `revoked_at` timestamp (if granted=false)
   - `version` ("1.0" for MVP)
   - `ip_address` (from request or extracted from headers)
4. Response returns consent record
5. If consent declined, user cannot access dashboard (redirect to consent modal)
6. Frontend calls consent API after user accepts/declines
7. Consent status checked on dashboard load
8. Consent revocation endpoint works (sets `revoked_at` timestamp)

**Prerequisites:** Stories 1.4, 2.3 (database schema and auth working)

**Technical Notes:**
- Use FastAPI route with JWT authentication
- Insert/update consent_records table
- Check consent status in protected routes
- Frontend: Store consent status in auth context

---

### Story 2.7: Implement Session Management and Token Refresh

As a consumer,
I want my session to remain active without frequent re-logins,
so that I can use the platform continuously.

**Acceptance Criteria:**
1. Access token refresh handled automatically before expiration
2. Refresh token used to obtain new access tokens
3. Session timeout after refresh token expiration (30 days)
4. User redirected to login if session expired
5. Token refresh happens in background (non-blocking)
6. Multiple tabs share same session (tokens in localStorage)
7. Logout clears all tokens and invalidates session
8. Session state synchronized across tabs (storage events)

**Prerequisites:** Story 2.2 (Cognito auth integrated)

**Technical Notes:**
- Use AWS Amplify `Auth.currentSession()` to check token expiration
- Refresh token before expiration (e.g., 5 minutes before)
- Use `Auth.refreshSession()` to get new tokens
- Handle token refresh errors (redirect to login)

---

## Epic 3: Consumer Dashboard - Core

**Goal:** Enable consumers to view their transaction history and financial insights through visualizations.

**Value Proposition:** Provides consumers with visibility into their spending patterns and financial health through clear, actionable data visualizations.

**Epic Scope:**
- Transactions tab (table view with filters and pagination)
- Insights tab (charts and summary cards)
- Data fetching and caching
- Responsive design

### Story 3.1: Create Database Seeding Script for Demo Data

As a developer,
I want to seed the database with demo user data,
so that I can test the consumer dashboard with realistic transaction data.

**Acceptance Criteria:**
1. Seeding script created (`backend/scripts/seed_demo_data.py`)
2. Script creates 3 demo users in Cognito (if not exists):
   - Hannah Martinez (hannah@demo.com)
   - Sam Patel (sam@demo.com)
   - Sarah Chen (sarah@demo.com) - for Savings Builder persona
3. Script creates accounts for each user:
   - Hannah: Checking ($850), Savings ($1,200), Visa Credit ($3,400/$5,000)
   - Sam: Checking ($2,400), Savings ($5,000), Credit Card ($800/$8,000)
   - Sarah: Checking ($3,200), High-Yield Savings ($8,500), Credit Card ($400/$3,000)
4. Script creates ~200 transactions for Hannah, ~180 for Sam, ~150 for Sarah
5. Transactions include:
   - Various categories (Food & Drink, Shopping, Bills, Subscriptions)
   - Recurring subscriptions (Netflix, Spotify, etc.)
   - Credit card interest charges for Hannah
   - Realistic dates (spread over 90 days)
   - Realistic amounts
6. Script uses faker library for merchant names (no real PII)
7. Script can be run multiple times idempotently
8. Data matches PRD specifications for each demo user

**Prerequisites:** Stories 1.4, 1.5 (database schema and Cognito exist)

**Technical Notes:**
- Use pandas or raw SQL for data insertion
- Generate transactions with realistic patterns
- Include subscription detection patterns (recurring merchants)
- Store in CSV format for version control (optional)

---

### Story 3.2: Create Transactions API Endpoint

As a consumer,
I want to view my transaction history,
so that I can understand my spending patterns.

**Acceptance Criteria:**
1. Backend endpoint created: `GET /api/v1/users/me/transactions`
2. Query parameters supported:
   - `start_date` (ISO 8601, optional)
   - `end_date` (ISO 8601, optional)
   - `category` (optional filter)
   - `merchant` (optional search)
   - `page` (default: 1)
   - `limit` (default: 50, max: 100)
3. Response format:
   ```json
   {
     "data": {
       "transactions": [...],
       "pagination": {
         "page": 1,
         "limit": 50,
         "total": 200,
         "total_pages": 4
       }
     },
     "meta": {
       "timestamp": "2025-11-03T10:30:00Z"
     }
   }
   ```
4. Transactions filtered by authenticated user (application-layer security)
5. Default sort: date descending (newest first)
6. Pagination works correctly
7. Empty result handled (empty array)
8. Error handling for invalid dates or parameters

**Prerequisites:** Stories 1.4, 2.3, 3.1 (database, auth, and seed data exist)

**Technical Notes:**
- Use FastAPI query parameters with Pydantic models
- Use SQLAlchemy or raw SQL with parameterized queries
- Apply user_id filter from JWT token
- Implement efficient pagination with LIMIT/OFFSET or cursor-based

---

### Story 3.3: Create Transactions Tab Component

As a consumer,
I want to see my transaction history in a table with filters,
so that I can review my spending by date, category, and merchant.

**Acceptance Criteria:**
1. TransactionsTab component created (`TransactionsTab.tsx`)
2. Table displays columns:
   - Date (formatted: "Nov 3, 2025")
   - Merchant Name
   - Amount (color-coded: red for debit, green for credit)
   - Category (with icon)
   - Account (last 4 digits, e.g., "****4523")
3. Filters implemented:
   - Date range picker (30 days / 90 days buttons)
   - Category dropdown (all categories from transactions)
   - Search input for merchant name
4. Sort functionality:
   - Sort by date (default: newest first)
   - Sort by amount (ascending/descending)
5. Pagination controls (Previous/Next, page numbers)
6. Empty state: "No transactions found for this filter"
7. Loading state: Skeleton or spinner while fetching
8. Error state: Error message if API call fails
9. Uses shadcn/ui Table component
10. Responsive design (mobile-friendly)

**Prerequisites:** Stories 1.1, 3.2 (frontend and API endpoint exist)

**Technical Notes:**
- Use React Query for data fetching (`useQuery`)
- Implement debounced search for merchant filter
- Use date-fns for date formatting
- Handle loading and error states with React Query
- Memoize filtered/sorted data

---

### Story 3.4: Create Insights API Endpoint

As a consumer,
I want to view my spending insights and charts data,
so that I can understand my financial patterns visually.

**Acceptance Criteria:**
1. Backend endpoint created: `GET /api/v1/users/me/insights`
2. Query parameter: `period` ("30d" or "90d", default: "30d")
3. Response includes:
   - Summary cards data:
     - Total spending (period)
     - Average daily spend
     - Top category
     - Savings rate (if applicable)
   - Chart 1 data: Monthly Spending by Category (horizontal bar chart data)
   - Chart 2 data: Credit Utilization Trend (line chart data, if user has credit accounts)
   - Chart 3 data: Subscription Breakdown (donut chart data)
4. Data computed from user's transactions (filtered by period)
5. Response format:
   ```json
   {
     "data": {
       "summary": {...},
       "charts": {
         "spending_by_category": [...],
         "credit_utilization": [...],
         "subscriptions": {...}
       }
     },
     "meta": {...}
   }
   ```
6. Empty states handled (no transactions, no credit accounts)
7. Efficient query (aggregate at database level when possible)

**Prerequisites:** Stories 1.4, 2.3, 3.1 (database, auth, and seed data exist)

**Technical Notes:**
- Use SQL aggregation queries (SUM, COUNT, GROUP BY)
- Compute credit utilization from account balances
- Identify subscriptions from transaction patterns (or use computed_features if available)
- Cache results if appropriate (or compute on-demand)

---

### Story 3.5: Create Insights Tab with Charts

As a consumer,
I want to visualize my spending patterns through charts,
so that I can quickly understand my financial habits.

**Acceptance Criteria:**
1. InsightsTab component created (`InsightsTab.tsx`)
2. Summary cards displayed at top:
   - Total Spending (period)
   - Average Daily Spend
   - Top Category
   - Savings Rate (if applicable)
3. Time period toggle: 30 days / 90 days (buttons)
4. Chart 1: Monthly Spending by Category (horizontal bar chart)
   - X-axis: Amount ($)
   - Y-axis: Categories
   - Hover tooltip: exact amount + % of total
   - Uses Recharts BarChart
5. Chart 2: Credit Utilization Trend (line chart, only if user has credit accounts)
   - X-axis: Date (weekly buckets)
   - Y-axis: Utilization % (0-100%)
   - Reference lines: 30% (green), 50% (yellow), 80% (red)
   - Tooltip: "Week of [date]: 65% utilization ($3,400 / $5,000)"
   - Uses Recharts LineChart
6. Chart 3: Subscription Breakdown (donut chart)
   - Inner: Total monthly recurring ($)
   - Segments: Individual subscriptions
   - Legend: Merchant name + amount
   - Click segment → filter transactions (to be implemented later)
   - Uses Recharts PieChart
7. "What this means" expandable sections for each chart
8. Loading states for charts
9. Empty states handled (no data)
10. Responsive design (charts adapt to screen size)

**Prerequisites:** Stories 1.1, 3.4 (frontend and API endpoint exist)

**Technical Notes:**
- Use Recharts library for all charts
- Use React Query for data fetching
- Implement chart interactions (hover, tooltips)
- Use date-fns for date formatting
- Handle conditional rendering (credit chart only if applicable)

---

## Epic 4: Consumer Dashboard - Education & Offers

**Goal:** Deliver personalized financial education content and partner offers with clear rationales explaining why they're shown.

**Value Proposition:** Provides consumers with actionable financial education and relevant product offers based on their actual financial behavior, with full transparency about why content is shown.

**Epic Scope:**
- Education tab with personalized content cards
- Offers tab with partner products
- Rationale box component (novel pattern)
- Recommendation API integration
- Content catalog setup

### Story 4.1: Create Rationale Box Component

As a consumer,
I want to understand why I'm seeing specific education content,
so that I trust the recommendations are relevant to my situation.

**Acceptance Criteria:**
1. RationaleBox component created (`RationaleBox.tsx`)
2. Component displays:
   - Label: "Why we're showing this"
   - Content: Specific data point (e.g., "Your Visa ending in 4523 is at 65% utilization ($3,400 of $5,000 limit)")
3. Visual styling:
   - Light blue background (#eff6ff)
   - Left border accent (#1e40af)
   - Subtle shadow
   - Clear typography
4. Component is reusable (accepts content as prop)
5. Component is accessible (ARIA labels, keyboard navigation)
6. Component matches UX specification design

**Prerequisites:** Story 1.1 (frontend project initialized)

**Technical Notes:**
- Use Tailwind CSS for styling
- Match exact colors from UX spec (#eff6ff background, #1e40af border)
- Create as standalone component in `src/components/`

---

### Story 4.2: Create Education Card Component

As a consumer,
I want to see education content in an easy-to-read card format,
so that I can quickly understand and access financial education.

**Acceptance Criteria:**
1. EducationCard component created (`EducationCard.tsx`)
2. Card displays:
   - Icon (matched to category: credit, savings, budgeting, etc.)
   - Title (e.g., "Understanding Credit Utilization")
   - Brief description (2-3 sentences)
   - RationaleBox component with specific data point
   - "Learn More" button
   - Tags (e.g., #Credit #DebtManagement)
3. "Learn More" button expands full content (inline or modal)
4. Card states: default, expanded, loading
5. Card variants by category (color-coded)
6. Card uses shadcn/ui Card component
7. Card is accessible and responsive
8. Card matches UX specification

**Prerequisites:** Stories 1.1, 4.1 (frontend and RationaleBox exist)

**Technical Notes:**
- Use shadcn/ui Card component as base
- Integrate RationaleBox component
- Handle expand/collapse state
- Use icons from lucide-react or similar

---

### Story 4.3: Create Recommendations API Endpoint

As a consumer,
I want to receive personalized education and offers,
so that I get relevant financial guidance based on my behavior.

**Acceptance Criteria:**
1. Backend endpoint created: `GET /api/v1/users/me/recommendations`
2. Endpoint retrieves:
   - User's persona (from `persona_assignments` table, 30-day window)
   - User's behavioral signals (from `computed_features` table)
   - Recommendations from `recommendations` table (3-5 education, 2-3 offers)
3. Response format:
   ```json
   {
     "data": {
       "education": [
         {
           "id": "rec_123",
           "title": "Understanding Credit Utilization",
           "description": "...",
           "rationale": "Your Visa ending in 4523 is at 65% utilization...",
           "category": "credit",
           "tags": ["Credit", "DebtManagement"],
           "full_content": "..."
         }
       ],
       "offers": [
         {
           "id": "rec_456",
           "title": "Balance Transfer Credit Card",
           "description": "...",
           "rationale": "This might help because...",
           "eligibility": "eligible",
           "partner_logo_url": "..."
         }
       ]
     },
     "meta": {...}
   }
   ```
4. Recommendations sorted by priority (most relevant first)
5. Empty state handled (no recommendations available)
6. Data filtered by authenticated user

**Prerequisites:** Stories 1.4, 2.3 (database and auth exist, recommendations may be empty initially)

**Technical Notes:**
- Join recommendations table with decision_traces for rationale
- Sort by recommendation priority or signal strength
- Return full content for education items
- Include partner logo URLs for offers (S3 URLs)

---

### Story 4.4: Create Education Tab Component

As a consumer,
I want to view personalized financial education content,
so that I can learn about financial topics relevant to my situation.

**Acceptance Criteria:**
1. EducationTab component created (`EducationTab.tsx`)
2. Tab displays 3-5 education cards (from API)
3. Cards sorted by priority (most relevant first)
4. Each card shows:
   - Icon, title, description
   - RationaleBox with specific data point
   - "Learn More" button
   - Tags
5. "Learn More" expands full content (modal or inline expansion)
6. Loading state: Skeleton cards while fetching
7. Empty state: "No education content available" (if no recommendations)
8. Error state: Error message if API fails
9. Disclaimer at bottom: "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."
10. Responsive design (cards stack on mobile)

**Prerequisites:** Stories 1.1, 4.2, 4.3 (frontend, EducationCard, and API exist)

**Technical Notes:**
- Use React Query for data fetching
- Map API response to EducationCard components
- Handle loading, error, and empty states
- Use shadcn/ui Dialog for "Learn More" modal

---

### Story 4.5: Create Offers Tab Component

As a consumer,
I want to view relevant partner product offers,
so that I can explore products that might help my financial situation.

**Acceptance Criteria:**
1. OffersTab component created (`OffersTab.tsx`)
2. Tab displays 2-3 offer cards (from API)
3. Each card shows:
   - Partner logo (from S3)
   - Product name
   - Brief description
   - Eligibility status badge:
     - ✅ "You may be eligible" (green)
     - ⚠️ "Requirements not met" (yellow) + explanation
   - RationaleBox with data-driven reason
   - "Learn More" button (external link)
   - Disclosure: "SpendSense may receive compensation. This is not a recommendation."
4. Cards sorted by relevance
5. Loading, error, and empty states handled
6. Responsive design
7. External links open in new tab

**Prerequisites:** Stories 1.1, 4.1, 4.3 (frontend, RationaleBox, and API exist)

**Technical Notes:**
- Use shadcn/ui Card and Badge components
- Display partner logos from S3 URLs
- Handle external link clicks
- Match UX specification styling

---

## Epic 5: Consumer Chat Widget

**Goal:** Enable consumers to ask questions about their financial data through an AI-powered chat interface.

**Value Proposition:** Provides instant answers to financial questions with specific data citations, maintaining educational tone and ethical guardrails.

**Epic Scope:**
- Chat widget component (Messenger-style)
- OpenAI/Claude API integration
- Response generation with data citations
- Guardrails and validation
- Rate limiting

### Story 5.1: Create Chat Widget Component

As a consumer,
I want to ask questions about my financial data through a chat interface,
so that I can quickly get answers without navigating through multiple tabs.

**Acceptance Criteria:**
1. ChatWidget component created (`ChatWidget.tsx`)
2. Widget displays as fixed position: bottom-right corner
3. Widget is expandable/collapsible (button toggles visibility)
4. When expanded, shows chat interface:
   - Chat history (session-based)
   - Message input field
   - Send button
   - Typing indicator when processing
5. Messages displayed in conversation format (user messages right-aligned, bot messages left-aligned)
6. Widget uses Messenger-style design (from UX spec)
7. Widget is accessible (keyboard navigation, screen reader support)
8. Widget styled with Tailwind CSS
9. Widget persists chat history during session (cleared on page refresh)

**Prerequisites:** Story 1.1 (frontend project initialized)

**Technical Notes:**
- Use shadcn/ui components or custom implementation
- Match UX specification design (Option 5 - Messenger style)
- Implement slide-up animation
- Use React state for chat history management

---

### Story 5.2: Create Chat API Endpoint

As a consumer,
I want my chat questions to be answered with relevant information,
so that I understand my financial data better.

**Acceptance Criteria:**
1. Backend endpoint created: `POST /api/v1/chat`
2. Request body: `{message: string}`
3. Endpoint retrieves:
   - User's computed features (from `computed_features` table)
   - Recent transactions (last 30 transactions)
   - User's persona (from `persona_assignments` table)
4. Endpoint calls OpenAI or Claude API with:
   - System prompt with strict guidelines (education only, no financial advice, no shaming)
   - User's financial data context
   - User's question
5. Response format:
   ```json
   {
     "data": {
       "response": "Your credit utilization is 65%...",
       "citations": [
         {"data_point": "Visa ending in 4523", "value": "65% utilization"}
       ]
     },
     "meta": {...}
   }
   ```
6. Response includes disclaimer at end
7. Rate limiting: 10 messages per minute per user
8. Chat log stored in `chat_logs` table with guardrails status

**Prerequisites:** Stories 1.4, 2.3 (database and auth exist)

**Technical Notes:**
- Use OpenAI or Anthropic API
- Construct system prompt with guardrails
- Include user data in prompt context
- Validate response before returning (check for prohibited phrases)
- Store chat log with `guardrails_passed` boolean

---

### Story 5.3: Implement Chat Guardrails and Validation

As a consumer,
I want the chat to provide educational responses without financial advice or shaming,
so that I receive helpful, non-judgmental guidance.

**Acceptance Criteria:**
1. System prompt includes strict guidelines:
   - No financial advice (only education)
   - No shaming language (prohibited phrase list)
   - Cite specific data points
   - Include disclaimer
2. Response validation checks:
   - No prohibited phrases in response
   - Educational tone maintained
   - Data citations present
   - Disclaimer included
3. If validation fails, response is regenerated or filtered
4. Guardrails status stored in `chat_logs` table
5. Prohibited phrase list maintained (configurable)
6. Logging of guardrail violations (for monitoring)

**Prerequisites:** Story 5.2 (chat API endpoint exists)

**Technical Notes:**
- Define prohibited phrase list (e.g., "you're overspending", "bad habits")
- Use string matching or regex for validation
- Consider using OpenAI moderation API
- Log violations for operator review

---

### Story 5.4: Integrate Chat Widget with Dashboard

As a consumer,
I want the chat widget to be accessible from all dashboard tabs,
so that I can ask questions while viewing different sections.

**Acceptance Criteria:**
1. ChatWidget component added to DashboardLayout
2. Widget persists across tab navigation
3. Widget accessible from all consumer dashboard tabs
4. Chat can reference current tab context (e.g., "See Insights tab for more")
5. Widget does not interfere with dashboard functionality
6. Widget maintains chat history during navigation
7. Widget z-index ensures it's always visible
8. Widget responsive (adjusts position on mobile)

**Prerequisites:** Stories 1.1, 5.1 (frontend and ChatWidget exist)

**Technical Notes:**
- Add ChatWidget to DashboardLayout component
- Use React Context or state management for chat history
- Handle tab context awareness

---

## Epic 6: Operator Dashboard

**Goal:** Enable operators to audit recommendations and monitor users with full decision traceability.

**Value Proposition:** Provides operators with complete visibility into recommendation logic and user behavior, enabling oversight and audit capabilities.

**Epic Scope:**
- User list page (table with filters and search)
- User detail page (overview, signals, recommendations, traces)
- Decision trace viewer (JSON display)
- Operator actions (override, flag for review)

### Story 6.1: Create Operator User List API Endpoint

As an operator,
I want to view a list of all users with their personas and risk flags,
so that I can identify users who need review.

**Acceptance Criteria:**
1. Backend endpoint created: `GET /api/v1/operator/users`
2. Query parameters:
   - `search` (name or email, optional)
   - `persona` (filter by persona type, optional)
   - `risk_flag` (filter by risk flags, optional)
   - `page` (default: 1)
   - `limit` (default: 50)
3. Response includes:
   - User list with columns:
     - Full Name
     - Email
     - Primary Persona (30-day)
     - Risk Flags (badges: High Utilization, Overdue, etc.)
     - Last Active (timestamp)
4. Summary stats:
   - Total Users
   - Users by Persona (counts)
   - Active Users (last 7 days)
   - Flagged Users Requiring Review
5. Response sorted by any column (default: last active)
6. Pagination works correctly
7. Only accessible to operators (role check)

**Prerequisites:** Stories 1.4, 2.4 (database and RBAC exist)

**Technical Notes:**
- Use `require_operator()` dependency for authorization
- Join users with persona_assignments and computed_features
- Compute risk flags from signals
- Aggregate summary stats

---

### Story 6.2: Create Operator User List Page

As an operator,
I want to see all users in a searchable, filterable table,
so that I can quickly find users who need attention.

**Acceptance Criteria:**
1. UserListPage component created (`UserListPage.tsx`)
2. Table displays columns:
   - Full Name
   - Email
   - Primary Persona (30-day)
   - Risk Flags (badges with colors)
   - Last Active (relative time: "2 hours ago")
   - Actions (View Details button)
3. Filters implemented:
   - Search by name or email (debounced)
   - Filter by persona type (dropdown)
   - Filter by risk flags (multi-select)
4. Sort functionality for all columns
5. Summary stats displayed at top:
   - Total Users (card)
   - Users by Persona (bar chart)
   - Active Users (last 7 days) (card)
   - Flagged Users (card)
6. "View Details" button navigates to user detail page
7. Loading, error, and empty states handled
8. Uses OperatorDataTable component (from UX spec)
9. Responsive design

**Prerequisites:** Stories 1.1, 6.1 (frontend and API endpoint exist)

**Technical Notes:**
- Use React Query for data fetching
- Use shadcn/ui Table component
- Implement debounced search
- Use Recharts for persona bar chart

---

### Story 6.3: Create Operator User Detail API Endpoint

As an operator,
I want to view detailed information about a specific user,
so that I can audit their recommendations and understand their financial behavior.

**Acceptance Criteria:**
1. Backend endpoint created: `GET /api/v1/operator/users/{user_id}`
2. Response includes:
   - User Overview:
     - Name, email, member since
     - Consent status + timestamp
     - Connected accounts (count + types)
     - Persona assignments (30d, 90d, 180d)
   - Behavioral Signals:
     - Credit signals (utilization, payments, interest, status)
     - Subscription signals (count, monthly total, top subscriptions)
     - Savings signals (balance, growth rate, coverage)
     - Income signals (frequency, paycheck amount, buffer)
   - Recommendations:
     - All education items + offers shown to user
     - Type, title, shown_at, clicked status
     - Decision trace IDs for each recommendation
3. Response format matches PRD specifications
4. Only accessible to operators
5. Efficient query (minimize database calls)

**Prerequisites:** Stories 1.4, 2.4 (database and RBAC exist)

**Technical Notes:**
- Use `require_operator()` dependency
- Join multiple tables efficiently
- Aggregate signals by time window
- Include decision trace references

---

### Story 6.4: Create Decision Trace Viewer Component

As an operator,
I want to view the complete decision trace for a recommendation,
so that I can understand how and why it was generated.

**Acceptance Criteria:**
1. DecisionTraceViewer component created (`DecisionTraceViewer.tsx`)
2. Component displays JSON decision trace with:
   - Syntax highlighting (monospace font, color-coded)
   - Collapsible sections
   - Copy-to-clipboard button
3. Trace format matches PRD:
   ```json
   {
     "recommendation_id": "rec_123",
     "persona_match": "high_utilization",
     "signals_used": [...],
     "template_id": "...",
     "guardrails_passed": {...},
     "timestamp": "..."
   }
   ```
4. Component opens in modal (from "Decision Trace" button)
5. Component is accessible (keyboard navigation)
6. Component uses monospace font (JetBrains Mono or similar)
7. Component styled per UX specification

**Prerequisites:** Story 1.1 (frontend project initialized)

**Technical Notes:**
- Use syntax highlighting library (react-syntax-highlighter or similar)
- Use shadcn/ui Dialog for modal
- Implement JSON collapsing/expanding
- Add copy-to-clipboard functionality

---

### Story 6.5: Create Operator User Detail Page

As an operator,
I want to view comprehensive user information including signals, recommendations, and traces,
so that I can audit recommendations and take action if needed.

**Acceptance Criteria:**
1. UserDetailPage component created (`UserDetailPage.tsx`)
2. Page displays 4 sections:
   - Section 1: User Overview
     - Name, email, member since
     - Consent status + timestamp
     - Connected accounts
     - Persona assignments (30d, 90d, 180d)
   - Section 2: Behavioral Signals
     - Credit signals with details
     - Subscription signals with breakdown
     - Savings signals with metrics
     - Income signals with patterns
   - Section 3: Recommendations Review
     - Table of all recommendations
     - Columns: Type, Title, Shown At, Clicked?, Decision Trace
     - "Decision Trace" button opens DecisionTraceViewer modal
   - Section 4: Operator Actions
     - "Override Recommendation" button
     - "Flag for Review" button
     - Audit log of past actions
3. Loading, error states handled
4. Navigation back to user list
5. Responsive design
6. Uses shadcn/ui components

**Prerequisites:** Stories 1.1, 6.3, 6.4 (frontend, API, and DecisionTraceViewer exist)

**Technical Notes:**
- Use React Query for data fetching
- Use React Router for navigation
- Integrate DecisionTraceViewer component
- Handle operator actions (to be implemented in next story)

---

### Story 6.6: Implement Operator Actions API

As an operator,
I want to override recommendations or flag users for review,
so that I can take corrective action when needed.

**Acceptance Criteria:**
1. Backend endpoint created: `POST /api/v1/operator/users/{user_id}/override`
2. Request body: `{recommendation_id: string, reason: string}`
3. Endpoint:
   - Marks recommendation as overridden
   - Stores action in `operator_actions` table:
     - `operator_id` (from JWT)
     - `user_id` (from path)
     - `action_type` ("override")
     - `reason` (from request)
     - `created_at` (timestamp)
4. Backend endpoint created: `POST /api/v1/operator/users/{user_id}/flag`
5. Request body: `{reason: string}`
6. Endpoint:
   - Flags user for review
   - Stores action in `operator_actions` table
7. Endpoint: `GET /api/v1/operator/users/{user_id}/actions`
   - Returns audit log of past operator actions
8. All endpoints require operator role
9. Actions are logged for audit trail

**Prerequisites:** Stories 1.4, 2.4 (database and RBAC exist)

**Technical Notes:**
- Use `require_operator()` dependency
- Insert into operator_actions table
- Return audit log for display
- Consider adding recommendation override flag to recommendations table

---

## Epic 7: Behavioral Signal Detection

**Goal:** Compute behavioral signals from transaction data to enable personalization and persona assignment.

**Value Proposition:** Automatically analyzes user transaction patterns to identify key financial behaviors, enabling personalized recommendations.

**Epic Scope:**
- Signal detection algorithms (subscriptions, credit, savings, income) - Already implemented
- Computed features storage (dual database: SQLite/Firestore)
- Batch processing scripts for all users
- API endpoints for on-demand computation (gap)

### Story 7.1: Create Subscription Detection Logic

**Status:** ✅ Already Implemented

As the system,
I want to automatically detect recurring subscriptions from transaction data,
so that users can see their subscription spending patterns.

**Acceptance Criteria:**
1. ✅ Subscription detection function created (`src/features/signal_detection.py` - `detect_subscriptions()`)
2. ✅ Logic identifies recurring merchants:
   - ≥3 occurrences in window
   - Monthly cadence (±3 days tolerance)
   - Weekly cadence (±1 day tolerance)
3. ✅ Function outputs:
   - List of recurring merchants
   - Monthly recurring spend total
   - Subscription share of total spend (%)
4. ✅ Function stores results in `computed_features` table:
   - `signal_type` = "subscriptions"
   - `signal_data` = JSON with merchant list and totals
   - `time_window` = "30d" or "180d"
5. ✅ Function handles edge cases:
   - No transactions
   - No recurring patterns
   - Multiple subscriptions same merchant
6. ✅ Function is testable (unit tests)

**Implementation:** `src/features/signal_detection.py::detect_subscriptions()`

**Technical Notes:**
- Supports dual database (SQLite/Firestore) via `USE_FIRESTORE` flag
- Stores results as JSON in `signal_data` column
- Time windows: "30d" and "180d"

---

### Story 7.2: Create Credit Utilization Detection Logic

**Status:** ✅ Already Implemented

As the system,
I want to automatically compute credit utilization metrics,
so that users can understand their credit card usage.

**Acceptance Criteria:**
1. ✅ Credit utilization detection function created
2. ✅ Logic computes for each credit card account:
   - Utilization % = balance / limit
   - Flag: High (≥50%), Medium (30-50%), Low (<30%)
3. ✅ Logic detects:
   - Minimum payment only (compare last_payment_amount to minimum_payment_amount, flag if equal within $5)
   - Interest charges (check transaction categories for interest)
   - Overdue status (from account data if available)
4. ✅ Function stores results in `computed_features` table:
   - `signal_type` = "credit_utilization"
   - `signal_data` = JSON with utilization %, flags, interest, payment info, and account-level details
5. ✅ Function handles:
   - Multiple credit cards per user (aggregated in single signal)
   - No credit accounts (skip)
   - Missing balance/limit data
6. ✅ Function is testable

**Implementation:** `src/features/signal_detection.py::detect_credit_utilization()`

**Technical Notes:**
- Supports dual database (SQLite/Firestore) via `USE_FIRESTORE` flag
- Stores all account data in single JSON signal (not per-account signals)
- Query accounts table for credit accounts
- Detect payment patterns from transactions

---

### Story 7.3: Create Savings Behavior Detection Logic

**Status:** ✅ Already Implemented

As the system,
I want to automatically compute savings behavior metrics,
so that users can see their savings patterns and growth.

**Acceptance Criteria:**
1. ✅ Savings behavior detection function created
2. ✅ Logic computes:
   - Net inflow = deposits to savings-like accounts - withdrawals
   - Growth rate = (current_balance - balance_180d_ago) / balance_180d_ago
   - Emergency fund coverage:
     - Average monthly expenses from transactions
     - Coverage = savings_balance / avg_monthly_expenses
     - Flag: Excellent (≥6mo), Good (3-6mo), Building (1-3mo), Low (<1mo)
3. ✅ Function identifies savings-like accounts (subtype = "savings", "money market", "hsa")
4. ✅ Function stores results in `computed_features` table:
   - `signal_type` = "savings_behavior"
   - `signal_data` = JSON with metrics and flags
5. ✅ Function handles:
   - No savings accounts (skip)
   - Negative growth (handle gracefully)
   - Missing historical data
6. ✅ Function is testable

**Implementation:** `src/features/signal_detection.py::detect_savings_behavior()`

**Technical Notes:**
- Supports dual database (SQLite/Firestore) via `USE_FIRESTORE` flag
- Query accounts table for savings accounts
- Aggregate transactions for savings accounts
- Calculate monthly expense average from transaction history
- Uses 180-day window for growth calculation

---

### Story 7.4: Create Income Stability Detection Logic

**Status:** ✅ Already Implemented

As the system,
I want to automatically detect income patterns and stability,
so that users can understand their cash flow situation.

**Acceptance Criteria:**
1. ✅ Income stability detection function created
2. ✅ Logic detects payroll deposits:
   - Look for ACH deposits with "PAYROLL" or employer names
   - Identify recurring pattern
3. ✅ Logic computes:
   - Frequency: Weekly, biweekly, semi-monthly, monthly
   - Variability: Coefficient of variation of paycheck amounts
   - Cash-flow buffer = checking_balance / avg_monthly_expenses
4. ✅ Function stores results in `computed_features` table:
   - `signal_type` = "income_stability"
   - `signal_data` = JSON with frequency, variability, buffer
5. ✅ Function handles:
   - No payroll detected (skip)
   - Irregular income patterns
   - Missing account data
6. ✅ Function is testable

**Implementation:** `src/features/signal_detection.py::detect_income_stability()`

**Technical Notes:**
- Supports dual database (SQLite/Firestore) via `USE_FIRESTORE` flag
- Query transactions for deposit patterns
- Use pattern matching for payroll detection
- Calculate coefficient of variation for variability
- Store frequency as string (weekly, biweekly, etc.)

---

### Story 7.5: Create Compute Features API Endpoint

**Status:** ❌ Gap - API endpoint missing (batch script exists)

As the system,
I want to automatically compute all behavioral signals when user data updates,
so that recommendations stay current with user behavior.

**Acceptance Criteria:**
1. ✅ Batch script exists: `src/features/compute_all.py` (computes for all users)
2. ❌ API endpoint missing: `POST /api/users/{user_id}/compute-features`
3. API endpoint should:
   - Accept `user_id` as path parameter
   - Optionally accept `time_window` query parameter (default: "30d")
   - Call `compute_all_features()` from `src/features/signal_detection.py`
   - Store computed features in `computed_features` table
   - Return status with computed signal types
4. Endpoint handles errors gracefully (returns appropriate HTTP status codes)
5. Endpoint can be triggered manually or via webhook
6. Endpoint is testable

**Existing Implementation:**
- Batch script: `src/features/compute_all.py` (computes for all users)
- Core function: `src/features/signal_detection.py::compute_all_features()`

**Prerequisites:** Stories 1.4, 7.1-7.4 (database schema and signal detection functions exist)

**Technical Notes:**
- Use existing `compute_all_features()` function
- Supports dual database (SQLite/Firestore) via `USE_FIRESTORE` flag
- Add endpoint to `src/api/main.py`
- Time windows: "30d" and "180d" (not "90d")
- Store results efficiently (uses existing `store_feature()` function)

---

## Epic 8: Persona Assignment & Recommendation Engine

**Goal:** Assign personas to users and generate personalized recommendations with explainable rationales.

**Value Proposition:** Automatically categorizes users and provides personalized financial education and offers based on their behavior, with full transparency about why recommendations are shown.

**Epic Scope:**
- Persona assignment logic - Already implemented
- Recommendation generation - Already implemented
- Content catalog management - Already implemented
- Rationale generation - Already implemented
- Tone guardrails - Already implemented
- Decision trace creation - Already implemented
- API endpoints for on-demand triggers (gap)

### Story 8.1: Create Persona Assignment Logic

**Status:** ✅ Already Implemented

As the system,
I want to automatically assign personas to users based on their behavioral signals,
so that recommendations can be personalized to their financial situation.

**Acceptance Criteria:**
1. ✅ Persona assignment function created (`src/personas/assignment.py` - `assign_persona()`)
2. ✅ Logic implements hierarchical assignment (priority order):
   - Persona 1: High Utilization (priority 1)
     - Criteria: ANY card utilization ≥50% OR interest charges > $0 OR minimum payment only OR overdue
   - Persona 2: Variable Income (priority 2)
     - Criteria: Median pay gap >45 days OR irregular frequency AND cash-flow buffer <1 month
   - Persona 3: Subscription-Heavy (priority 3)
     - Criteria: ≥3 recurring merchants AND (monthly recurring ≥$50 OR subscription share ≥10%)
   - Persona 4: Savings Builder (priority 4)
     - Criteria: Savings growth ≥2% OR net savings ≥$200/month AND all utilizations <30%
   - Default: "general_wellness" (if no criteria met)
3. ✅ Function assigns persona per time window (30d, 180d)
4. ✅ Function stores in `persona_assignments` table:
   - `user_id`, `time_window`, `persona`, `criteria_met` (JSON array), `assigned_at`
5. ✅ Function handles:
   - Multiple criteria met (highest priority wins)
   - No signals available (default persona)
   - Different personas across time windows
6. ✅ Function is testable

**Implementation:** `src/personas/assignment.py::assign_persona()`

**Technical Notes:**
- Supports dual database (SQLite/Firestore) via `USE_FIRESTORE` flag
- Query computed_features table for user signals
- Implement priority-based logic
- Store persona assignments with timestamps
- Time windows: "30d" and "180d" (not "90d")

---

### Story 8.2: Create Assign Persona API Endpoint

**Status:** ❌ Gap - API endpoint missing (batch script exists)

As the system,
I want to automatically assign personas after features are computed,
so that users have current persona assignments for recommendations.

**Acceptance Criteria:**
1. ✅ Batch script exists: `src/personas/assign_all.py` (assigns for all users)
2. ❌ API endpoint missing: `POST /api/users/{user_id}/assign-persona`
3. API endpoint should:
   - Accept `user_id` as path parameter
   - Optionally accept `time_window` query parameter (default: "30d")
   - Call `assign_persona()` from `src/personas/assignment.py`
   - Store persona assignments in database
   - Return assigned persona and criteria met
4. Endpoint handles errors gracefully (returns appropriate HTTP status codes)
5. Endpoint can be triggered manually or via webhook
6. Endpoint is testable

**Existing Implementation:**
- Batch script: `src/personas/assign_all.py` (assigns for all users)
- Core function: `src/personas/assignment.py::assign_persona()`

**Prerequisites:** Stories 1.4, 8.1 (database and persona logic exist)

**Technical Notes:**
- Use existing `assign_persona()` function
- Supports dual database (SQLite/Firestore) via `USE_FIRESTORE` flag
- Add endpoint to `src/api/main.py`
- Time windows: "30d" and "180d" (not "90d")
- Store results via existing `store_persona_assignment()` function

---

### Story 8.3: Create Content Catalog Management

**Status:** ✅ Already Implemented

As the system,
I want to store education content and partner offers in a structured format,
so that recommendations can be matched to user personas.

**Acceptance Criteria:**
1. ✅ Content catalog structure defined (Python module with constants)
2. ✅ Education items stored with:
   - ID, title, description, category
   - Personas (array of matching personas)
   - Trigger signals (array of signal types)
   - Full content text
   - Rationale template (with variables)
   - Tags
3. ✅ Partner offers stored with:
   - ID, title, description
   - Eligibility criteria (functions)
   - Partner logo URL
   - External link URL
4. ✅ Content catalog seeded with PRD items:
   - 15+ education items (3-5 per persona)
   - 8+ partner offers
5. ✅ Content can be queried by persona and signals
6. ✅ Content catalog stored in Python module (not database table)

**Implementation:** `src/recommend/content_catalog.py`

**Technical Notes:**
- Content stored as Python constants in module
- Rationale templates with variable placeholders
- Includes all content from PRD data requirements
- Queryable by persona via `get_content_by_persona()`
- Functions for eligibility checking (`check_offer_eligibility()`)

---

### Story 8.4: Create Recommendation Generation Logic

**Status:** ✅ Already Implemented

As the system,
I want to generate personalized recommendations based on user persona and signals,
so that users receive relevant financial education and offers.

**Acceptance Criteria:**
1. ✅ Recommendation generation function created (`src/recommend/engine.py` - `generate_recommendations()`)
2. ✅ Function:
   - Retrieves user's persona (30-day window)
   - Retrieves user's behavioral signals
   - Selects 3-5 education items from catalog (matching persona and signals)
   - Selects 2-3 partner offers (matching eligibility criteria)
   - Generates rationales for each recommendation
   - Applies tone guardrails
   - Stores recommendations in database
   - Creates decision traces
3. ✅ Education selection:
   - Filter by persona match
   - Filter by trigger signals
   - Sort by priority/relevance
   - Limit to 3-5 items
4. ✅ Offer selection:
   - Filter by eligibility criteria
   - Check user doesn't already have product
   - Check minimum requirements met
   - Exclude predatory products
   - Limit to 2-3 items
5. ✅ Function stores in `recommendations` table
6. ✅ Function is testable

**Implementation:** `src/recommend/engine.py::generate_recommendations()`

**Technical Notes:**
- Supports dual database (SQLite/Firestore) via `USE_FIRESTORE` flag
- Query persona_assignments and computed_features
- Filter content catalog by persona and signals
- Implement eligibility checking logic
- Store recommendations with rationale and decision trace

---

### Story 8.5: Create Rationale Generation with Template System

**Status:** ✅ Already Implemented

As the system,
I want to generate clear rationales explaining why recommendations are shown,
so that users understand the data-driven reasoning.

**Acceptance Criteria:**
1. ✅ Rationale generation function created
2. ✅ Function uses template-based approach:
   - Rationale templates stored in content catalog
   - Variables substituted with actual data (e.g., `{card_name}`, `{utilization}%`, `{balance}`)
3. ✅ Function generates rationales:
   - Always cite specific data (account numbers, amounts, dates)
   - Use plain language, no jargon
   - Format: "We're showing you this because [concrete observation]"
4. ✅ Examples:
   - "Your Visa ending in 4523 is at 65% utilization ($3,400 of $5,000 limit)"
   - "You have 8 active subscriptions totaling $203/month"
5. ✅ Rationale stored with recommendation
6. ✅ Function handles missing data gracefully

**Implementation:** `src/recommend/rationale_generator.py::generate_rationale()`

**Technical Notes:**
- Use Python string formatting with template substitution
- Extract data from computed_features using dot notation paths
- Substitute variables in templates
- Format currency and percentages appropriately
- Validate rationale completeness

---

### Story 8.6: Implement Tone Guardrails and Validation

**Status:** ✅ Already Implemented

As the system,
I want to ensure recommendations use empowering, non-shaming language,
so that users feel supported rather than judged.

**Acceptance Criteria:**
1. ✅ Tone guardrail function created
2. ✅ Function checks generated text against prohibited phrase list:
   - "you're overspending"
   - "bad habits"
   - "poor choices"
   - Other shaming language
3. ✅ Function validates:
   - No shaming language present
   - Empowering language used ("opportunity to", "you might consider")
   - Neutral observations ("We noticed", "your data shows")
4. ✅ If validation fails:
   - Recommendation skipped (not stored)
   - Tone validation status stored in decision trace
5. ✅ Guardrails status stored in decision trace
6. ✅ Prohibited phrase list is configurable
7. ✅ Function is testable

**Implementation:** `src/guardrails/tone_validator.py::validate_tone()`

**Technical Notes:**
- Maintain prohibited phrase list as Python constant
- Use string matching for detection
- Implement validation before storing recommendations
- Log violations for monitoring
- Integrated into recommendation generation flow

---

### Story 8.7: Create Decision Trace Generation

**Status:** ✅ Already Implemented

As the system,
I want to store complete decision traces for all recommendations,
so that operators can audit recommendation logic.

**Acceptance Criteria:**
1. ✅ Decision trace generation function created
2. ✅ Function creates decision trace JSON:
   ```json
   {
     "recommendation_id": "rec_abc123",
     "user_id": "user_xyz",
     "type": "education",
     "title": "Understanding Credit Utilization",
     "selected_reason": "Persona match: high_utilization",
     "signals_used": [
       {"signal": "credit_utilization", "value": 0.65, "threshold": 0.50}
     ],
     "template_id": "edu_credit_util_101",
     "rationale_generated": "Your Visa ending in 4523 is at 65% utilization...",
     "guardrails_passed": {
       "tone_check": true,
       "eligibility_check": true,
       "no_shaming": true
     },
     "timestamp": "2025-11-03T10:30:00Z"
   }
   ```
3. ✅ Function stores trace in `recommendations` table:
   - `decision_trace` column (JSON string)
   - Linked to recommendation via recommendation_id
4. ✅ Function links trace to recommendation (one-to-one)
5. ✅ Trace format matches PRD specification
6. ✅ Function is called for every recommendation generated

**Implementation:** `src/recommend/engine.py::create_decision_trace()`

**Technical Notes:**
- Store trace as JSON string in `decision_trace` column of `recommendations` table
- Link trace to recommendation via recommendation_id
- Include all decision logic details
- Ensure trace completeness
- Integrated into recommendation generation flow

---

### Story 8.8: Create Generate Recommendations API Endpoint

**Status:** ❌ Gap - API endpoint missing (batch script exists)

As the system,
I want to automatically generate recommendations after persona assignment,
so that users have current personalized content.

**Acceptance Criteria:**
1. ✅ Batch script exists: `src/recommend/generate_all.py` (generates for all users)
2. ❌ API endpoint missing: `POST /api/users/{user_id}/generate-recommendations`
3. API endpoint should:
   - Accept `user_id` as path parameter
   - Optionally accept `time_window` query parameter (default: "30d")
   - Call `generate_recommendations()` from `src/recommend/engine.py`
   - Generates rationales
   - Applies tone guardrails
   - Stores recommendations and decision traces
   - Returns list of generated recommendations
4. Endpoint handles errors gracefully (returns appropriate HTTP status codes)
5. Endpoint can be triggered manually or via webhook
6. Endpoint respects consent (could check consent status if implemented)
7. Endpoint is testable

**Existing Implementation:**
- Batch script: `src/recommend/generate_all.py` (generates for all users)
- Core function: `src/recommend/engine.py::generate_recommendations()`

**Prerequisites:** Stories 1.4, 8.4-8.7 (database and recommendation logic exist)

**Technical Notes:**
- Use existing `generate_recommendations()` function
- Supports dual database (SQLite/Firestore) via `USE_FIRESTORE` flag
- Add endpoint to `src/api/main.py`
- Time windows: "30d" and "180d" (not "90d")
- Store recommendations and traces via existing engine functions
- Handle API timeouts if rationale generation becomes async

---

## Implementation Sequence

### Phase 1: Foundation (Week 1-2)

**Parallel Stories (can run simultaneously):**
- Story 1.1: Initialize Frontend Project
- Story 1.2: Initialize Backend Project
- Story 1.3: Create AWS RDS PostgreSQL Database
- Story 1.5: Create AWS Cognito User Pool

**Sequential Stories:**
- Story 1.4: Create Database Schema (depends on 1.3)
- Story 1.6: Create AWS Lambda Functions and API Gateway (depends on 1.3, 1.5)
- Story 1.7: Create S3 Buckets and CloudFront Distribution (can run parallel with 1.6)
- Story 1.8: Set Up EventBridge Rules (depends on 1.6)
- Story 1.9: Set Up CI/CD Pipeline (can run parallel)
- Story 1.10: Configure Development Environment Variables (depends on 1.1, 1.2, 1.3, 1.5)

**Gate:** Infrastructure must be complete before Phase 2

---

### Phase 2: Authentication & Core Data (Week 3-4)

**Sequential Stories:**
- Story 2.1: Create Login Form Component (depends on 1.1)
- Story 2.2: Integrate AWS Cognito Authentication (depends on 1.1, 1.5)
- Story 2.3: Implement JWT Token Validation (depends on 1.2, 1.5)
- Story 2.4: Implement Role-Based Access Control (depends on 2.3)
- Story 2.5: Create Consent Modal Component (depends on 1.1, 2.2)
- Story 2.6: Implement Consent Management API (depends on 1.4, 2.3)
- Story 2.7: Implement Session Management (depends on 2.2)

**Parallel with Authentication:**
- Story 3.1: Create Database Seeding Script (depends on 1.4, 1.5)

**Gate:** Authentication working, demo data seeded

---

### Phase 3: Consumer Dashboard Core (Week 5-6)

**Sequential Stories:**
- Story 3.2: Create Transactions API Endpoint (depends on 1.4, 2.3, 3.1)
- Story 3.3: Create Transactions Tab Component (depends on 1.1, 3.2)
- Story 3.4: Create Insights API Endpoint (depends on 1.4, 2.3, 3.1)
- Story 3.5: Create Insights Tab with Charts (depends on 1.1, 3.4)

**Gate:** Consumers can view transactions and insights

---

### Phase 4: Education & Offers (Week 7)

**Sequential Stories:**
- Story 4.1: Create Rationale Box Component (depends on 1.1)
- Story 4.2: Create Education Card Component (depends on 1.1, 4.1)
- Story 4.3: Create Recommendations API Endpoint (depends on 1.4, 2.3)
- Story 4.4: Create Education Tab Component (depends on 1.1, 4.2, 4.3)
- Story 4.5: Create Offers Tab Component (depends on 1.1, 4.1, 4.3)

**Note:** Recommendations may be empty initially until background jobs are implemented

---

### Phase 5: Chat Widget (Week 8)

**Sequential Stories:**
- Story 5.1: Create Chat Widget Component (depends on 1.1)
- Story 5.2: Create Chat API Endpoint (depends on 1.4, 2.3)
- Story 5.3: Implement Chat Guardrails (depends on 5.2)
- Story 5.4: Integrate Chat Widget with Dashboard (depends on 1.1, 5.1)

---

### Phase 6: Operator Dashboard (Week 9)

**Sequential Stories:**
- Story 6.1: Create Operator User List API Endpoint (depends on 1.4, 2.4)
- Story 6.2: Create Operator User List Page (depends on 1.1, 6.1)
- Story 6.3: Create Operator User Detail API Endpoint (depends on 1.4, 2.4)
- Story 6.4: Create Decision Trace Viewer Component (depends on 1.1)
- Story 6.5: Create Operator User Detail Page (depends on 1.1, 6.3, 6.4)
- Story 6.6: Implement Operator Actions API (depends on 1.4, 2.4)

---

### Phase 7: Background Processing (Week 10-11)

**Sequential Stories:**
- Story 7.1: Create Subscription Detection Logic (depends on 1.4, 3.1)
- Story 7.2: Create Credit Utilization Detection Logic (depends on 1.4, 3.1)
- Story 7.3: Create Savings Behavior Detection Logic (depends on 1.4, 3.1)
- Story 7.4: Create Income Stability Detection Logic (depends on 1.4, 3.1)
- Story 7.5: Create Compute Features Lambda Function (depends on 1.6, 7.1-7.4)

**Parallel with Signal Detection:**
- Story 8.1: Create Persona Assignment Logic (depends on 1.4, 7.5)
- Story 8.3: Create Content Catalog Management (depends on 1.4)

**Sequential after Persona Assignment:**
- Story 8.2: Create Assign Persona Lambda Function (depends on 1.6, 8.1)
- Story 8.4: Create Recommendation Generation Logic (depends on 1.4, 8.1, 8.3)
- Story 8.5: Create Rationale Generation (depends on 8.4)
- Story 8.6: Implement Tone Guardrails (depends on 8.5)
- Story 8.7: Create Decision Trace Generation (depends on 1.4, 8.4)
- Story 8.8: Create Generate Recommendations Lambda Function (depends on 1.6, 8.4-8.7)

**Gate:** Background jobs working, recommendations generated

---

## Dependency Graph

```
Epic 1 (Foundation):
  1.1 (Frontend) ──┐
  1.2 (Backend) ───┼──> 1.10 (Env Vars)
  1.3 (RDS) ───────┼──> 1.4 (Schema) ──> 1.6 (Lambda)
  1.5 (Cognito) ───┘                      │
  1.7 (S3/CloudFront) ────────────────────┼──> 1.8 (EventBridge)
  1.9 (CI/CD) ────────────────────────────┘

Epic 2 (Auth):
  2.1 ──> 2.2 ──> 2.5
  2.3 ──> 2.4 ──> 2.6
  2.2 ──> 2.7

Epic 3 (Consumer Dashboard Core):
  3.1 (depends on 1.4, 1.5)
  3.2 (depends on 1.4, 2.3, 3.1) ──> 3.3
  3.4 (depends on 1.4, 2.3, 3.1) ──> 3.5

Epic 4 (Education & Offers):
  4.1 ──> 4.2 ──> 4.4
  4.1 ──> 4.5
  4.3 (depends on 1.4, 2.3) ──> 4.4, 4.5

Epic 5 (Chat):
  5.1 ──> 5.4
  5.2 ──> 5.3 ──> 5.4

Epic 6 (Operator):
  6.1 ──> 6.2
  6.3 ──> 6.5
  6.4 ──> 6.5
  6.6 (parallel with 6.5)

Epic 7 (Signal Detection):
  7.1 ──┐
  7.2 ──┼──> 7.5
  7.3 ──┤
  7.4 ──┘

Epic 8 (Persona & Recommendations):
  8.1 (depends on 7.5) ──> 8.2
  8.3 ────────────────────┐
  8.4 (depends on 8.1, 8.3) ──> 8.5 ──> 8.6 ──> 8.8
  8.7 (depends on 8.4) ────────────────────────┘
```

---

## Development Phases Summary

**Phase 1: Foundation (Stories 1.1-1.10)**
- Duration: 2 weeks
- Deliverable: Working infrastructure, development environment, CI/CD
- Parallel opportunities: Frontend/backend setup, multiple AWS services

**Phase 2: Authentication & Core Data (Stories 2.1-2.7, 3.1)**
- Duration: 2 weeks
- Deliverable: Users can log in, consent managed, demo data available
- Parallel opportunities: Frontend auth UI + backend auth API

**Phase 3: Consumer Dashboard Core (Stories 3.2-3.5)**
- Duration: 2 weeks
- Deliverable: Consumers can view transactions and insights
- Parallel opportunities: API endpoints + frontend components

**Phase 4: Education & Offers (Stories 4.1-4.5)**
- Duration: 1 week
- Deliverable: Education and offers tabs functional (may need background jobs for recommendations)

**Phase 5: Chat Widget (Stories 5.1-5.4)**
- Duration: 1 week
- Deliverable: Chat widget functional with AI responses

**Phase 6: Operator Dashboard (Stories 6.1-6.6)**
- Duration: 1 week
- Deliverable: Operators can view users and audit recommendations

**Phase 7: Background Processing (Stories 7.1-7.5, 8.1-8.8)**
- Duration: 2 weeks
- Deliverable: Automatic signal detection, persona assignment, recommendation generation
- Parallel opportunities: Signal detection functions can be developed in parallel

**Total Estimated Timeline: 11 weeks**

---

## Story Validation Summary

**Total Stories:** 47 stories across 8 epics

**Size Check:**
- ✅ All stories are < 500 words in description
- ✅ Clear inputs and outputs defined
- ✅ Single responsibility principle followed
- ✅ No hidden complexity

**Clarity Check:**
- ✅ Acceptance criteria explicit and testable
- ✅ Technical approach clear
- ✅ No ambiguous requirements
- ✅ Success measurable

**Dependency Check:**
- ✅ Dependencies documented for each story
- ✅ Stories can start with clear inputs
- ✅ Outputs well-defined
- ✅ Parallel opportunities noted

**Coverage:**
- ✅ All PRD requirements have story coverage
- ✅ Infrastructure setup stories included
- ✅ Background jobs have implementation stories
- ✅ Novel patterns (Rationale Box, Decision Trace) have implementation stories

---

## Implementation Guidance

### Getting Started

Start with Phase 1 stories - multiple can run in parallel:
- Story 1.1 (Frontend) and 1.2 (Backend) can be done simultaneously
- Story 1.3 (RDS) and 1.5 (Cognito) can be done simultaneously
- Story 1.7 (S3/CloudFront) can be done in parallel with others

**Key Files to Create First:**
- Frontend: `package.json`, `vite.config.ts`, `tailwind.config.js`
- Backend: `requirements.txt`, `app/main.py`, `app/config.py`
- Infrastructure: CDK/CloudFormation templates or SAM templates

**Recommended Agent Allocation:**
- Frontend developer: Stories 1.1, 2.1-2.2, 2.5, 2.7, 3.3, 3.5, 4.1-4.5, 5.1, 5.4, 6.2, 6.4-6.5
- Backend developer: Stories 1.2, 1.4, 2.3-2.4, 2.6, 3.1-3.2, 3.4, 4.3, 5.2-5.3, 6.1, 6.3, 6.6, 7.1-7.5, 8.1-8.8
- DevOps/Infrastructure: Stories 1.3, 1.5-1.9, 1.10

### Technical Notes

**Architecture Decisions Needed:**
- Database migration strategy (Alembic vs raw SQL) - affects Story 1.4
- Lambda deployment method (SAM vs CDK) - affects Story 1.6
- Content catalog storage (database table vs JSON file) - affects Story 8.3

**Consider These Patterns:**
- React Query for all API data fetching (frontend)
- FastAPI dependencies for authentication/authorization (backend)
- EventBridge events for background job triggers
- Structured logging for all Lambda functions

### Risk Mitigation

**Watch Out For:**
- RDS connection limits in Lambda (use connection pooling) - Story 1.6
- Lambda cold starts (consider provisioned concurrency) - Story 1.6
- OpenAI/Claude API rate limits - Story 5.2, 8.4
- Large transaction datasets (pagination, efficient queries) - Story 3.2
- Complex signal detection algorithms (performance testing) - Stories 7.1-7.4

### Success Metrics

**You'll know Phase 1 is complete when:**
- Frontend builds and runs locally
- Backend API runs locally
- RDS database is accessible
- Cognito authentication works
- Lambda functions can be deployed

**You'll know Phase 2 is complete when:**
- Users can log in with demo accounts
- Consent modal appears and works
- JWT tokens are validated on backend
- Role-based access works (consumer vs operator)

**You'll know Phase 7 is complete when:**
- Background jobs compute features automatically
- Personas are assigned to users
- Recommendations are generated with rationales
- Decision traces are created for all recommendations

---

**For implementation:** Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown.


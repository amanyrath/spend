# SpendSense (crEDit) UX Design Specification

_Created on 2025-11-03 by Alexis_
_Generated using BMad Method - Create UX Design Workflow v1.0_

---

## Executive Summary

SpendSense is a web-based financial education platform that analyzes user transaction data to deliver personalized, explainable financial guidance. The platform serves two distinct user types: **Consumers** (banking customers seeking financial education) and **Operators** (bank employees auditing recommendations).

**Core Value Proposition:**
- Consumers receive personalized financial education with clear rationales explaining why content is shown
- Operators gain full auditability and oversight of all recommendations through decision traces
- Every recommendation includes specific data citations and maintains ethical guardrails

**Design Philosophy:**
- **For Consumers:** Safe and Empowered - Clear, non-judgmental guidance that helps users understand their finances
- **For Operators:** Comfortable, Secure, Confident - Full transparency and traceability builds trust in recommendations

---

## 1. Design System Foundation

### 1.1 Design System Choice

**Selected:** shadcn/ui

**Rationale:**
- Built specifically for Tailwind CSS (matches tech stack)
- Provides accessible defaults (WCAG AA compliance via Radix UI primitives)
- Fully customizable (components live in codebase, not dependency)
- Comprehensive component library (~50 components)
- Active community and excellent documentation
- Works seamlessly with Recharts for data visualization

**Provides:**
- Core components: Button, Card, Form, Dialog, Table, Badge, Tabs, Input, Select, etc.
- Accessibility built-in: Keyboard navigation, ARIA labels, focus management
- Theming capabilities: CSS variables for easy brand customization
- Responsive patterns: Mobile-first responsive design

**Custom Components Needed:**
- Rationale Box component (unique to SpendSense)
- Decision Trace Viewer (JSON display with syntax highlighting)
- Education Card component (with rationale box)
- Operator Data Table (with inline filters and actions)
- Chat Widget (Messenger-style)

---

## 2. Core User Experience

### 2.1 Defining Experience

**For Consumers:**
"It's the app that shows you one clear thing you can do to improve your finances" - with a rationale explaining why it's relevant to them.

**For Operators:**
"It's the tool that helps operators trust AI recommendations through full decision traceability."

**Core Interaction:**
- **Consumers:** Seeing a clear, actionable insight with a rationale box explaining why they're seeing this content
- **Operators:** Reviewing recommendations with full decision trace visibility and AI chat assistant for data queries

**Most Critical Action:**
Presenting the most relevant, actionable insight that moves users toward their financial goals - making it effortless to understand.

### 2.2 Novel UX Patterns

**Rationale Box Pattern:**
- Every education card and offer includes a highlighted rationale box
- Format: "We're showing you this because [specific data point]"
- Example: "Your Visa ending in 4523 is at 65% utilization ($3,400 of $5,000 limit)"
- Visual treatment: Subtle background color, left border accent, clear label

**Decision Trace Transparency:**
- Operators can view complete JSON of recommendation logic
- Shows: Persona match, signals used, template ID, guardrails passed, timestamp
- Displayed in modal with syntax highlighting for readability

**AI Chat Integration:**
- **Consumers:** Messenger-style floating chat widget (bottom-right, slide-up)
- **Operators:** Compact sidebar chat helper (Option 6 style) for data queries
- Both cite specific data points and maintain educational tone

---

## 3. Visual Foundation

### 3.1 Color System

**Selected Theme:** Trust Professional

**Color Palette:**
- **Primary:** `#1e40af` (Deep Blue) - Main actions, key elements, trust
- **Secondary:** `#3b82f6` (Bright Blue) - Supporting actions, links
- **Success:** `#10b981` (Green) - Positive actions, success states
- **Error:** `#ef4444` (Red) - Errors, warnings, destructive actions
- **Warning:** `#f59e0b` (Amber) - Warnings, caution states
- **Neutral:** `#64748b` (Slate Gray) - Text, borders, secondary elements

**Semantic Color Usage:**
- Primary buttons: Deep blue (#1e40af)
- Rationale boxes: Light blue background (#eff6ff) with blue border
- Success indicators: Green (#10b981)
- Risk flags: Red badges/indicators
- Data points in chat: Highlighted with blue accent

**Typography:**
- **Font Family:** System font stack (San Francisco on Mac, Segoe UI on Windows)
- **Headings:** Inter (if available) or system sans-serif, weights 600-700
- **Body:** System font, weight 400
- **Monospace:** JetBrains Mono for code/data (decision traces)

**Spacing System:**
- Base unit: 4px
- Scale: 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px
- Layout grid: 12-column grid for dashboards
- Container max-width: 1280px (desktop)

**Interactive Visualizations:**
- Color Theme Explorer: [ux-color-themes.html](./ux-color-themes.html)

---

## 4. Design Direction

### 4.1 Chosen Design Approach

**Consumer Dashboard:** Direction #1 - Spacious Dashboard
- Top navigation with tabs
- Spacious layout with breathing room
- Clear information hierarchy
- Professional and efficient
- Rationale boxes prominently displayed

**Operator Dashboard:** Direction #6 - Operator Dashboard Style
- Sidebar navigation + main content area
- Data-first approach with tables and metrics
- Professional and structured
- Clear hierarchy for audit workflows
- Compact AI chat helper in sidebar (Option 6 style)

**Layout Decisions:**
- **Navigation:** Top tabs for consumers, sidebar for operators
- **Content Structure:** Single column for consumers, multi-column for operators
- **Visual Density:** Spacious for consumers (breathing room), balanced for operators (information-rich)
- **Interaction Style:** Progressive disclosure for consumers, all-at-once for operators

**Rationale:**
- Consumer experience prioritizes clarity and reduced overwhelm
- Operator experience prioritizes efficiency and information access
- Both maintain professional, trustworthy appearance

**Interactive Mockups:**
- Design Direction Showcase: [ux-design-directions.html](./ux-design-directions.html)
- Chat Widget Options: [ux-chat-widget-options.html](./ux-chat-widget-options.html)

---

## 5. User Journey Flows

### 5.1 Critical User Paths

#### Consumer Journey: First-Time Login to Education

**Flow: Progressive Onboarding → Education First**

1. **Signup Flow:**
   - User enters email/password
   - **Consent during signup** (not after login)
   - Consent modal explains data usage
   - User checks "I consent" → submits

2. **First Login:**
   - User logs in with credentials
   - **Progressive onboarding** (3-4 screens):
     - Welcome screen explaining platform value
     - Overview of dashboard tabs
     - Quick tour of key features
     - Highlight on Education tab value

3. **Dashboard Loads:**
   - **Default to Education tab** (not Transactions)
   - Most relevant education card shown first
   - Rationale box prominently displayed
   - User sees immediate value

4. **Explore Education:**
   - User reads rationale: "Your Visa ending in 4523 is at 65% utilization..."
   - Clicks "Learn More" → expands full content
   - Can browse other education cards
   - Clear, actionable insights throughout

5. **Additional Interactions:**
   - User can switch to Insights tab (charts, data visualization)
   - User can view Transactions tab (spending history)
   - User can check Offers tab (partner products)
   - Chat widget always accessible (bottom-right, Messenger style)

**Key Decisions:**
- Consent during signup (not after login) - reduces friction
- Progressive onboarding - helps first-time users understand platform
- Default to Education tab - delivers immediate value
- Education-first approach - aligns with core value proposition

#### Consumer Journey: Chat Interaction

1. **Trigger:** User clicks Messenger-style chat button (bottom-right)
2. **Chat Opens:** Slide-up animation, 380px wide, 600px tall
3. **Initial State:** Bot greeting with suggested question chips
4. **User Types:** "What's my credit utilization?"
5. **System Responds:** Cites specific data (Visa 4523, 65%, $3,400/$5,000)
6. **User Asks:** "Why am I seeing this education content?"
7. **System Responds:** Explains persona match and signals
8. **Always Includes:** Disclaimer at bottom of chat window

**Key Features:**
- Suggested question chips for quick interactions
- Typing indicators during processing
- Data points highlighted in responses
- Links back to relevant tabs when appropriate

#### Operator Journey: Auditing a Recommendation

**Flow: Data-First with AI Chat Helper**

1. **Login:**
   - Operator logs in
   - Redirects to User List page

2. **User List View:**
   - Main area: Table of users with columns:
     - Name, Email, Primary Persona, Risk Flags, Last Active, Actions
   - Quick filters: By persona, risk flags, date range
   - Search: Name or email
   - **Sidebar: Compact AI Chat Helper** (Option 6 style)
     - Can ask: "Show me all users with high utilization"
     - Can ask: "Find users who haven't logged in this week"
     - Assists with data queries and information location

3. **Select User:**
   - Click "View Details" for Hannah Martinez
   - Main area switches to User Detail view

4. **User Detail View:**
   - **Section 1:** User Overview
     - Name, email, member since
     - Consent status + timestamp
     - Connected accounts
     - Persona assignments (30d, 90d, 180d)
   
   - **Section 2:** Behavioral Signals
     - Credit signals: Utilization %, payments, interest
     - Subscription signals: Count, monthly total, top subscriptions
     - Savings signals: Balance, growth rate, coverage
     - Income signals: Frequency, paycheck amount, buffer
   
   - **Section 3:** Recommendations Review
     - Table of all education items + offers
     - Columns: Type, Title, Shown At, Clicked?, Decision Trace
     - Click "Decision Trace" → Modal with JSON view
   
   - **Section 4:** Operator Actions
     - "Override Recommendation" button
     - "Flag for Review" button
     - Audit log of past actions

5. **AI Chat Helper (Sidebar):**
   - Can ask: "Explain why this recommendation was shown"
   - Can ask: "What signals triggered this persona?"
   - Can ask: "Show me similar users"
   - Provides quick data access without navigating away

6. **Decision Trace Review:**
   - Click "Decision Trace" → Modal opens
   - JSON view shows:
     - Persona match: high_utilization
     - Signals used: credit_utilization_visa_4523 = 0.68
     - Template ID: edu_credit_util_101
     - Guardrails passed: tone_check = true
     - Timestamp: 2025-11-03T10:30:00Z

7. **Override Action:**
   - Click "Override Recommendation"
   - Enter reason: "User already completed this module"
   - Confirm override
   - Action logged in operator_actions table

**Key Decisions:**
- Data-first layout for operators (tables, metrics prominent)
- Compact sidebar AI helper for quick data queries
- Decision traces in modal (doesn't interrupt main workflow)
- All actions auditable and traceable

---

## 6. Component Library

### 6.1 Component Strategy

**From shadcn/ui (Standard Components):**
- Button (primary, secondary, outline, destructive variants)
- Card (for education cards, offer cards)
- Table (for transactions, user lists, recommendations)
- Tabs (for dashboard navigation)
- Dialog/Modal (for decision traces, overrides)
- Input, Select, Textarea (for forms)
- Badge (for personas, risk flags, status)
- Alert (for success, error, warning messages)

**Custom Components Needed:**

1. **Rationale Box Component**
   - Purpose: Explain why content is shown to user
   - Anatomy: Label ("Why we're showing this"), content area, optional icon
   - States: Default, expanded (for longer rationales)
   - Visual: Light blue background (#eff6ff), left border (#1e40af), subtle shadow
   - Accessibility: ARIA label, keyboard accessible

2. **Education Card Component**
   - Purpose: Display personalized financial education content
   - Anatomy: Icon, title, description, rationale box, "Learn More" button
   - States: Default, expanded (full content), loading
   - Variants: By category (credit, savings, budgeting, etc.)
   - Behavior: Click "Learn More" → expands inline or opens modal

3. **Decision Trace Viewer**
   - Purpose: Display JSON recommendation logic for operators
   - Anatomy: Syntax-highlighted JSON, collapsible sections, copy button
   - States: Default, expanded sections
   - Visual: Code block style, monospace font, color-coded syntax

4. **Operator Data Table**
   - Purpose: Display user list with filtering and actions
   - Anatomy: Sortable columns, inline filters, row actions, pagination
   - States: Loading, empty, filtered, selected
   - Features: Search, multi-select, export, bulk actions

5. **Chat Widget (Consumer)**
   - Style: Messenger-style (Option 5 from chat widget options)
   - Position: Fixed bottom-right
   - Behavior: Slide-up animation, 380px × 600px
   - Features: Suggested chips, typing indicator, data point highlighting

6. **AI Chat Helper (Operator)**
   - Style: Compact sidebar (Option 6 style from chat widget)
   - Position: Fixed right sidebar
   - Behavior: Collapsible, persistent
   - Features: Data query assistance, quick filters, user search

7. **Consent Modal**
   - Purpose: Collect user consent during signup
   - Anatomy: Title, explanation text, checkbox, Accept/Decline buttons
   - States: Default, checked, error (if declined)
   - Visual: Centered modal, clear explanation, prominent checkbox

---

## 7. UX Pattern Decisions

### 7.1 Consistency Rules

**Button Hierarchy:**
- **Primary:** Deep blue (#1e40af) - Main actions (Learn More, Send, View Details)
- **Secondary:** Bright blue (#3b82f6) - Supporting actions (Cancel, Back)
- **Outline:** Transparent with blue border - Tertiary actions (View All, Filter)
- **Destructive:** Red (#ef4444) - Delete, override, dangerous actions

**Feedback Patterns:**
- **Success:** Green toast notification (top-right, auto-dismiss after 3s)
- **Error:** Red inline message below input OR toast for system errors
- **Warning:** Amber badge or inline message
- **Info:** Blue badge or inline message
- **Loading:** Skeleton screens for content, spinner for actions

**Form Patterns:**
- **Label Position:** Above input (for clarity)
- **Required Field Indicator:** Red asterisk (*) + "Required" text
- **Validation Timing:** On blur (after user leaves field)
- **Error Display:** Inline below input, clear message, red border on input
- **Help Text:** Below input, gray text, 0.875rem

**Modal Patterns:**
- **Size Variants:** 
  - Small (400px): Simple confirmations
  - Medium (600px): Decision traces, overrides
  - Large (800px): Full content views
- **Dismiss Behavior:** Click outside to close (except for critical actions)
- **Focus Management:** Auto-focus first interactive element, trap focus
- **Stacking:** Multiple modals supported (stacked with backdrop)

**Navigation Patterns:**
- **Active State:** Underline (consumers), background highlight (operators)
- **Breadcrumbs:** Not used (flat navigation structure)
- **Back Button:** Browser back for consumers, explicit "Back" button for operators
- **Deep Linking:** Supported for all tabs and views

**Empty State Patterns:**
- **First Use:** Guidance message + CTA button (e.g., "Connect your account to get started")
- **No Results:** Helpful message + suggestions (e.g., "No transactions found. Try adjusting your filters.")
- **Cleared Content:** "No items" message + undo option if applicable

**Confirmation Patterns:**
- **Delete:** Always confirm with modal (cannot undo)
- **Leave Unsaved:** Warn with modal if user tries to navigate away
- **Override Recommendation:** Require reason input, confirm button

**Notification Patterns:**
- **Placement:** Top-right corner (toast notifications)
- **Duration:** Auto-dismiss after 3s (success), 5s (error/warning)
- **Stacking:** New notifications appear above previous, max 3 visible
- **Priority:** Critical (stays until dismissed), Normal (auto-dismiss)

**Search Patterns:**
- **Trigger:** Manual (click search icon or use keyboard shortcut)
- **Results Display:** Instant (as user types, with debounce)
- **Filters:** Located below search bar, chips for active filters
- **No Results:** Suggest alternative searches or clear filters

**Date/Time Patterns:**
- **Format:** Relative for recent (e.g., "2 hours ago"), absolute for older (e.g., "Nov 3, 2025")
- **Timezone:** User's local timezone (display in their timezone)
- **Pickers:** Calendar dropdown for date selection

---

## 8. Responsive Design & Accessibility

### 8.1 Responsive Strategy

**Breakpoints:**
- **Mobile:** < 640px (single column, bottom navigation)
- **Tablet:** 640px - 1024px (2-column layouts, touch-optimized)
- **Desktop:** > 1024px (full layouts, hover states)

**Adaptation Patterns:**

**Consumer Dashboard:**
- **Mobile:** 
  - Bottom tab navigation (instead of top)
  - Single column layout
  - Cards stack vertically
  - Chat widget full-width slide-up
- **Tablet:**
  - Top navigation maintained
  - 2-column grid for education cards
  - Chat widget 380px width
- **Desktop:**
  - Full 3-4 column layouts
  - Spacious spacing
  - Hover states on interactive elements

**Operator Dashboard:**
- **Mobile:**
  - Sidebar collapses to hamburger menu
  - Table becomes card view
  - AI chat helper becomes floating button
- **Tablet:**
  - Sidebar can be collapsed
  - Table maintains columns with horizontal scroll
  - AI chat helper in sidebar
- **Desktop:**
  - Full sidebar + main content
  - All columns visible
  - AI chat helper always visible

**Navigation Adaptation:**
- Consumers: Top tabs → Bottom tabs (mobile)
- Operators: Sidebar → Hamburger menu (mobile)

**Form Adaptation:**
- Single column on mobile
- Multi-column on desktop (where appropriate)

### 8.2 Accessibility Strategy

**WCAG Compliance Target:** Level AA

**Key Requirements:**

1. **Color Contrast:**
   - Text: 4.5:1 ratio minimum (WCAG AA)
   - Large text: 3:1 ratio minimum
   - Interactive elements: 3:1 ratio minimum

2. **Keyboard Navigation:**
   - All interactive elements accessible via keyboard
   - Tab order follows visual hierarchy
   - Focus indicators visible (2px blue outline)
   - Skip links for main content

3. **Screen Reader Support:**
   - ARIA labels on all interactive elements
   - Semantic HTML (headers, nav, main, aside)
   - Alt text for all meaningful images
   - Live regions for dynamic content (chat, notifications)

4. **Form Accessibility:**
   - Labels associated with inputs (for/id)
   - Error messages associated with inputs (aria-describedby)
   - Required fields announced to screen readers

5. **Touch Target Size:**
   - Minimum 44px × 44px for mobile
   - Adequate spacing between touch targets

**Testing Strategy:**
- **Automated:** Lighthouse, axe DevTools (browser extension)
- **Manual:** Keyboard-only navigation testing
- **Screen Reader:** NVDA (Windows) or VoiceOver (Mac) testing
- **Color Contrast:** WebAIM Contrast Checker

---

## 9. Implementation Guidance

### 9.1 Completion Summary

**What We Created Together:**

- **Design System:** shadcn/ui with 6 custom components (Rationale Box, Education Card, Decision Trace Viewer, Operator Data Table, Chat Widgets)
- **Visual Foundation:** Trust Professional color theme (#1e40af blue) with comprehensive spacing and typography system
- **Design Direction:** Spacious Dashboard (#1) for consumers, Operator Dashboard (#6) for operators
- **User Journeys:** 3 critical flows designed (Consumer onboarding, Chat interaction, Operator auditing)
- **UX Patterns:** 10 consistency rule categories established for cohesive experience
- **Responsive Strategy:** 3 breakpoints with adaptation patterns for all device sizes
- **Accessibility:** WCAG 2.1 Level AA compliance requirements defined

**Your Deliverables:**

- ✅ UX Design Document: `docs/ux-design-specification.md`
- ✅ Interactive Color Themes: `docs/ux-color-themes.html`
- ✅ Design Direction Mockups: `docs/ux-design-directions.html`
- ✅ Chat Widget Options: `docs/ux-chat-widget-options.html`

**What Happens Next:**

- Designers can create high-fidelity mockups from this foundation
- Developers can implement with clear UX guidance and rationale
- All design decisions are documented with reasoning for future reference

You've made thoughtful choices through visual collaboration that will create a great user experience. Ready for design refinement and implementation!

---

## Appendix

### Related Documents

- Product Requirements: `doc/spendsense_prd.md`

### Core Interactive Deliverables

This UX Design Specification was created through visual collaboration:

- **Color Theme Visualizer**: `docs/ux-color-themes.html`
  - Interactive HTML showing 4 color theme options explored
  - Live UI component examples in each theme
  - Side-by-side comparison and semantic color usage

- **Design Direction Mockups**: `docs/ux-design-directions.html`
  - Interactive HTML with 6 complete design approaches
  - Full-screen mockups of key screens
  - Design philosophy and rationale for each direction

- **Chat Widget Options**: `docs/ux-chat-widget-options.html`
  - Interactive HTML with 5 chat widget designs
  - Messenger-style option selected (Option 5)
  - Compact sidebar option for operators (Option 6)

### Next Steps & Follow-Up Workflows

This UX Design Specification can serve as input to:

- **Solution Architecture Workflow** - Define technical architecture with UX context
- **Component Implementation** - Build shadcn/ui components and custom components
- **Frontend Development** - Use this spec to implement React components
- **Design System Documentation** - Create component library documentation

### Version History

| Date       | Version | Changes                         | Author  |
| ---------- | ------- | ------------------------------- | ------- |
| 2025-11-03 | 1.0     | Initial UX Design Specification | Alexis  |

---

_This UX Design Specification was created through collaborative design facilitation, not template generation. All decisions were made with user input and are documented with rationale._





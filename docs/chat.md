## Epic 5: Consumer Chat Widget

**Goal:** Enable consumers to ask questions about their financial data through an AI-powered chat interface.

**Value Proposition:** Provides instant answers to financial questions with specific data citations, maintaining educational tone and ethical guardrails.

**Epic Scope:**
- Chat widget component (Messenger-style) ✅ COMPLETE
- OpenAI/Claude API integration ⏳ TODO
- Response generation with data citations ⏳ TODO
- Guardrails and validation ⚠️ PARTIAL (tone_validator exists, needs integration)
- Rate limiting ⏳ TODO

### Story 5.1: Create Chat Widget Component ✅ COMPLETE

**Status:** ✅ COMPLETE - ChatWidget component exists at `consumer_ui/src/components/chat-widget.tsx`

As a consumer,
I want to ask questions about my financial data through a chat interface,
so that I can quickly get answers without navigating through multiple tabs.

**Acceptance Criteria:**
1. ✅ ChatWidget component created (`chat-widget.tsx`)
2. ✅ Widget displays as fixed position: bottom-right corner
3. ✅ Widget is expandable/collapsible (button toggles visibility)
4. ✅ When expanded, shows chat interface:
   - Chat history (session-based)
   - Message input field
   - Send button
   - Typing indicator when processing
5. ✅ Messages displayed in conversation format (user messages right-aligned, bot messages left-aligned)
6. ✅ Widget uses Messenger-style design (from UX spec)
7. ✅ Widget is accessible (keyboard navigation, screen reader support)
8. ✅ Widget styled with Tailwind CSS
9. ✅ Widget persists chat history during session (cleared on page refresh)
10. ✅ Suggested questions chips implemented
11. ✅ Data citation highlighting in messages (basic pattern matching)

**Implementation Details:**
- Location: `consumer_ui/src/components/chat-widget.tsx`
- Integrated into `App.tsx` via `ChatWidgetWrapper` component
- Uses React hooks for state management
- Currently has placeholder bot responses (TODO on line 76: "Connect to chat API endpoint")

**Remaining Work:**
- Connect to actual chat API endpoint (Story 5.2)
- Integrate real API responses instead of simulated responses

---

### Story 5.2: Create Chat API Endpoint ⏳ TODO

**Status:** ⏳ NOT STARTED - No chat endpoint exists in `src/api/main.py`

As a consumer,
I want my chat questions to be answered with relevant information,
so that I understand my financial data better.

**Acceptance Criteria:**
1. Backend endpoint created: `POST /api/chat` (note: API uses `/api/` prefix, not `/api/v1/`)
2. Request body: `{message: string, user_id: string}` (user_id extracted from frontend context)
3. Endpoint retrieves:
   - User's computed features (from `computed_features` table via `get_user_features()`)
   - Recent transactions (last 30 transactions via existing transactions endpoint logic)
   - User's persona (from `persona_assignments` table via `get_persona_assignment()`)
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
     "meta": {
       "user_id": "user_001",
       "timestamp": "2025-01-15T10:30:00Z"
     }
   }
   ```
6. Response includes disclaimer at end
7. Rate limiting: 10 messages per minute per user (implement using in-memory dict or Redis)
8. Chat log stored in `chat_logs` table with guardrails status (needs schema migration)

**Prerequisites:** Stories 1.4, 2.3 (database and auth exist)

**Technical Notes:**
- Add endpoint to `src/api/main.py`
- Use OpenAI or Anthropic API (add to `requirements.txt`)
- Construct system prompt with guardrails
- Include user data in prompt context (use existing `get_user_features()` function)
- Validate response before returning (check for prohibited phrases using `tone_validator.py`)
- Store chat log with `guardrails_passed` boolean
- Support both SQLite and Firestore (match existing pattern in `main.py`)
- Database schema: Need to create `chat_logs` table:
  ```sql
  CREATE TABLE IF NOT EXISTS chat_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT,
      message TEXT,
      response TEXT,
      citations TEXT,  -- JSON
      guardrails_passed INTEGER,  -- 0 or 1
      created_at TEXT,
      FOREIGN KEY (user_id) REFERENCES users(user_id)
  );
  ```

**Files to Create/Modify:**
- `src/api/main.py` - Add `/api/chat` endpoint
- `src/database/schema.sql` - Add `chat_logs` table
- `src/database/firestore.py` - Add Firestore chat_logs collection handlers
- `requirements.txt` - Add OpenAI or Anthropic SDK
- `src/chat/` (new directory) - Chat logic module
  - `__init__.py`
  - `service.py` - Chat service with LLM integration
  - `prompts.py` - System prompt templates

---

### Story 5.3: Implement Chat Guardrails and Validation ⚠️ PARTIAL

**Status:** ⚠️ PARTIAL - `tone_validator.py` exists but needs integration with chat endpoint

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
   - No prohibited phrases in response (use `tone_validator.validate_tone()`)
   - Educational tone maintained
   - Data citations present
   - Disclaimer included
3. If validation fails, response is regenerated or filtered
4. Guardrails status stored in `chat_logs` table
5. Prohibited phrase list maintained (configurable - exists in `src/guardrails/tone_validator.py`)
6. Logging of guardrail violations (for monitoring)

**Current Implementation:**
- ✅ `src/guardrails/tone_validator.py` exists with:
  - `PROHIBITED_PHRASES` list
  - `validate_tone(text: str) -> bool` function
  - `check_prohibited_phrases(text: str) -> list[str]` function

**Remaining Work:**
- Integrate `tone_validator` into chat endpoint (Story 5.2)
- Add system prompt template with guardrails
- Implement response regeneration logic if validation fails
- Add violation logging for operator review
- Consider OpenAI moderation API for additional safety

**Technical Notes:**
- Import and use `src.guardrails.tone_validator` in chat service
- Define system prompt in `src/chat/prompts.py`
- Log violations to `chat_logs` table with `guardrails_passed=False`

---

### Story 5.4: Integrate Chat Widget with Dashboard ✅ COMPLETE

**Status:** ✅ COMPLETE - ChatWidget integrated into App.tsx

As a consumer,
I want the chat widget to be accessible from all dashboard tabs,
so that I can ask questions while viewing different sections.

**Acceptance Criteria:**
1. ✅ ChatWidget component added to DashboardLayout (`App.tsx` via `ChatWidgetWrapper`)
2. ✅ Widget persists across tab navigation
3. ✅ Widget accessible from all consumer dashboard tabs
4. ⏳ Chat can reference current tab context (e.g., "See Insights tab for more") - Future enhancement
5. ✅ Widget does not interfere with dashboard functionality
6. ✅ Widget maintains chat history during navigation
7. ✅ Widget z-index ensures it's always visible (z-50 in Tailwind)
8. ✅ Widget responsive (adjusts position on mobile - max-md classes)

**Implementation Details:**
- Location: `consumer_ui/src/App.tsx`
- `ChatWidgetWrapper` component extracts `userId` from route params
- Widget renders outside main content area, persists across route changes
- Uses React Router `useLocation` hook to extract user context

**Optional Future Enhancements:**
- Add tab context awareness (pass current tab to chat API)
- Add chat history persistence (localStorage or backend)

---

## Epic 6: Operator Dashboard

**Goal:** Enable operators to audit recommendations and monitor users with full decision traceability.

**Value Proposition:** Provides operators with complete visibility into recommendation logic and user behavior, enabling oversight and audit capabilities.

**Epic Scope:**
- User list page (table with filters and search)
- User detail page (overview, signals, recommendations, traces)
- Decision trace viewer (JSON display)
- Operator actions (override, flag for review)
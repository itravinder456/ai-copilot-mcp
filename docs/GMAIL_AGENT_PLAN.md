# Gmail Personal Agent — Planning Document

## 1. Goal

Build a personal AI agent that:

- Connects to a personal Gmail account via OAuth2
- Drafts or personalizes email bodies using an LLM
- Pauses before sending for human review, edit, and final confirmation
- Fits cleanly into the existing MCP tool-calling architecture

---

## 2. User Flow

```
User: "Email John about the meeting postponement, keep it professional but friendly"
        │
        ▼
  LLM drafts email body (personalized to user's style)
        │
        ▼
  Agent returns DRAFT to user for review
  ┌──────────────────────────────────────┐
  │  To: john@example.com                │
  │  Subject: Meeting Postponement       │
  │  Body: Hey John, ...                 │
  └──────────────────────────────────────┘
        │
  User: ┌──────────────────────────────┐
        │  "looks good, send it"       │  ──► Send via Gmail API
        │  "change the tone to formal" │  ──► Re-draft → review again
        │  "cancel"                    │  ──► Discard
        └──────────────────────────────┘
```

---

## 3. Architecture Options

### Option A — Gmail tool inside existing MCP server (recommended)

```
Backend :8000
  └─ Agent.handle_request()
       └─ MCPClient ──► MCP Server :8001
                          ├─ tools/gmail_tool.py   ← new
                          │     draft_email()
                          │     send_email()
                          │     list_emails()
                          │     read_email()
                          └─ PendingDraftStore      ← new (in-memory / Redis)
```

**Pros**

- Reuses existing MCPClient, executor, registry wiring
- No new service to deploy or Dockerize
- Single codebase change

**Cons**

- MCP server grows in responsibility (tool execution + session state)
- OAuth callback redirect URI must be hosted somewhere reachable

---

### Option B — Dedicated Gmail microservice

```
Backend :8000
  └─ Agent
       └─ GmailServiceClient ──► Gmail Service :8002
                                     ├── POST /draft
                                     ├── GET  /draft/{id}
                                     ├── PATCH /draft/{id}
                                     ├── POST /draft/{id}/send
                                     └── DELETE /draft/{id}
```

**Pros**

- Clean separation — Gmail auth/state isolated
- Can independently version, scale, or swap
- Easier to add more email providers later (Outlook, etc.)

**Cons**

- Another service to run, Dockerfile, port, and docker-compose entry
- More network hops
- Overkill for a personal tool

---

### Decision: Option A for now, with Option B upgrade path

Keep the Gmail tool in the MCP server. Structure the code so the `gmail_tool.py` module is self-contained and can be extracted to a microservice later with minimal refactoring.

---

## 4. Gmail API Authentication — Tradeoffs

| Method                                  | Best For                  | Token Storage             | Tradeoffs                                                                                 |
| --------------------------------------- | ------------------------- | ------------------------- | ----------------------------------------------------------------------------------------- |
| **OAuth2 — Desktop/Installed App flow** | Personal use, single user | Local file (`token.json`) | Simple, no server needed for callback. Token file must be protected.                      |
| **OAuth2 — Web Server flow**            | Multi-user, hosted app    | DB per user               | Needs a public callback URL. More complex but production-ready.                           |
| **Service Account**                     | G Suite/Workspace domain  | Key file                  | Cannot access personal Gmail unless domain-wide delegation is enabled. Not suitable here. |

**Recommendation: OAuth2 Desktop/Installed App flow**

- Use `google-auth-oauthlib` with `InstalledAppFlow`
- First run opens browser → user grants consent → token saved to `token.json`
- Subsequent runs refresh silently via stored refresh token
- Store `token.json` in a path excluded from git (already in `.gitignore` via `.env.*`)

### Required Gmail OAuth Scopes (minimal)

```
https://www.googleapis.com/auth/gmail.send          # send emails
https://www.googleapis.com/auth/gmail.compose       # create drafts
https://www.googleapis.com/auth/gmail.readonly      # read emails (for context/reply)
```

Do NOT request `gmail.modify` or `mail.google.com` (full access) unless needed.

---

## 5. Email Personalization Strategy — Tradeoffs

| Strategy                                         | Quality   | Effort    | Privacy                               |
| ------------------------------------------------ | --------- | --------- | ------------------------------------- |
| **Generic LLM prompt with tone/style params**    | Medium    | Low       | High — no personal data sent          |
| **System prompt with writing style description** | Good      | Low       | Medium — you describe your style once |
| **Few-shot examples of your past emails**        | High      | Medium    | Low — past emails sent to LLM         |
| **Fine-tuned model on your emails**              | Very High | Very High | Low — requires data pipeline          |

**Recommendation: System prompt with style description + optional tone override**

```python
PERSONAL_STYLE = """
You are writing on behalf of the user. Their writing style:
- Friendly but professional
- Uses short paragraphs
- Avoids corporate jargon
- Signs off with "Best, [Name]"
"""
```

User can override per request: "make it more formal", "keep it brief", etc.

---

## 6. Confirmation / Human-in-the-Loop Flow — Tradeoffs

The core challenge: the agent must **pause** after drafting and wait for user input before sending. Three approaches:

### 6a. Stateless Request-Response (simplest)

```
POST /chat  →  agent drafts  →  returns draft JSON to client
POST /chat  →  user confirms  →  agent sends
```

- Client stores draft state (e.g., in UI memory)
- Second request includes `{ "action": "send", "draft_id": "xyz" }`
- **Pros**: No server-side state, works with existing `/chat` endpoint
- **Cons**: Relies on client to track draft ID; fragile if client resets

### 6b. Server-Side Draft Store (recommended)

```
POST /chat  →  draft created  →  stored server-side with draft_id  →  draft returned
POST /chat  →  "send it" + draft_id  →  agent retrieves draft  →  sends
```

- Store drafts in memory dict (simple) or Redis (persistent)
- Draft expires after N minutes if not confirmed
- **Pros**: Robust, works across sessions if using Redis
- **Cons**: Requires state management in backend

### 6c. Streaming with Interrupt (advanced)

- Use WebSocket or SSE to stream draft token-by-token
- User can interrupt mid-generation to redirect
- **Pros**: Best UX for long emails
- **Cons**: Significant backend complexity; overkill for v1

**Recommendation: 6b (server-side draft store) with in-memory dict for v1, Redis upgrade for v2**

---

## 7. New Components Needed

### In `mcp-server/tools/gmail_tool.py`

```
draft_email(to, subject, body_instruction, style_override) → draft_id + body
send_email(draft_id)                                        → message_id
modify_email(draft_id, new_instruction)                     → updated body
cancel_email(draft_id)                                      → void
list_recent_emails(max_results, label)                      → list of email summaries
read_email(message_id)                                      → full email content
```

### In `mcp-server/`

```
draft_store.py        — in-memory DraftStore with expiry
gmail_auth.py         — OAuth2 flow, token refresh, gmail service builder
```

### In `backend/`

```
.env additions:
  GMAIL_CREDENTIALS_PATH=./credentials.json
  GMAIL_TOKEN_PATH=./token.json
  DRAFT_TTL_SECONDS=600
```

### New files (OAuth credentials — never committed)

```
backend/credentials.json    # downloaded from Google Cloud Console — in .gitignore
backend/token.json          # generated on first auth — in .gitignore
```

---

## 8. MCP Tool Registry Additions

```python
# registry.py additions
"draft_email": {
    "description": "Draft a personalized email using AI. Returns a draft for review.",
    "schema": DraftEmailRequestSchema,
},
"send_email": {
    "description": "Send a previously drafted email after user confirmation.",
    "schema": SendEmailRequestSchema,
},
"modify_email": {
    "description": "Modify a pending email draft based on user feedback.",
    "schema": ModifyEmailRequestSchema,
},
"cancel_email": {
    "description": "Cancel and discard a pending email draft.",
    "schema": CancelEmailRequestSchema,
},
"list_emails": {
    "description": "List recent emails from Gmail inbox.",
    "schema": ListEmailsRequestSchema,
},
"read_email": {
    "description": "Read the full content of a specific email.",
    "schema": ReadEmailRequestSchema,
},
```

---

## 9. Security Considerations

| Risk                                                 | Mitigation                                                                                        |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `credentials.json` and `token.json` committed to git | Add to `.gitignore`; never commit                                                                 |
| OAuth token stored in plaintext                      | Use `keyring` library or OS secret store for production                                           |
| LLM generates email to wrong recipient               | Always show `To:` field in confirmation; never auto-send without confirmation                     |
| Draft store grows unbounded                          | Add TTL-based expiry (10 min default)                                                             |
| MCP server open to anyone on network                 | Add API key middleware on `/execute/*` routes in MCP server                                       |
| Email content sent to external LLM                   | Use Groq/local model; document data handling; avoid including sensitive email body in LLM context |
| Phishing via AI-drafted emails                       | Rate-limit `send_email` calls; log all sent emails                                                |

---

## 10. Implementation Phases

### Phase 1 — Gmail Read + Auth (foundation)

- [ ] Create Google Cloud project, enable Gmail API, download `credentials.json`
- [ ] Implement `gmail_auth.py` — OAuth2 desktop flow with token refresh
- [ ] Implement `read_email` and `list_emails` tools
- [ ] Register in MCP registry and test via `/tools` endpoint

### Phase 2 — Draft + Confirm + Send loop

- [ ] Implement `DraftStore` with TTL expiry
- [ ] Implement `draft_email` tool — calls LLM with personalization system prompt
- [ ] Implement `send_email`, `cancel_email`, `modify_email` tools
- [ ] Register all new tools in MCP registry
- [ ] Update `.gitignore` for credential files

### Phase 3 — Personalization tuning

- [ ] Add `PERSONAL_STYLE` config to backend `.env`
- [ ] Allow per-request tone/style overrides
- [ ] Test with sample email scenarios (formal, casual, follow-up)

### Phase 4 — Hardening

- [ ] Replace in-memory `DraftStore` with Redis (add to docker-compose)
- [ ] Add API key middleware to MCP server `/execute/*`
- [ ] Replace plaintext token storage with OS keyring
- [ ] Add email send logging

---

## 11. Dependencies to Add

### mcp-server/requirements.txt

```
google-auth==2.x
google-auth-oauthlib==1.x
google-auth-httplib2==0.2.x
google-api-python-client==2.x
```

### backend/requirements.txt

```
# no new deps needed for v1
# redis (Phase 4)
```

---

## 12. Open Questions Before Starting

1. **Single user or multi-user?** — If only you, desktop OAuth flow is fine. If others will use it, need web server OAuth flow with per-user token storage.
2. **Reply to existing threads or only new emails?** — Replies require fetching thread ID from Gmail API, slightly more complex.
3. **Draft in Gmail itself or only in-memory?** — Creating a Gmail Draft (visible in Gmail UI) vs purely in-memory agent draft. Gmail draft approach is safer (recoverable), in-memory is simpler.
4. **Which LLM for personalization?** — Same Groq model, or a different one? Groq `llama-3.1-8b-instant` is fast but `llama-3.3-70b` will produce much better personalized prose.
5. **Offline token storage path** — Where should `credentials.json` and `token.json` live relative to Docker container mounts?

# 🧠 AgenticMem — Agentic Shared Memory

A full-stack collaborative memory system for AI agents and developer teams. Store architectural rules, decisions, and constraints in a shared vector database. Query them semantically using AI. Sync them live across teammates in real time.

Built for the **MongoDB AI Hackathon** — demonstrating persistent, workspace-isolated, role-controlled agentic memory using **MongoDB Atlas Vector Search**, **Change Streams**, **TTL Indexes**, **Google Gemini**, **FastAPI**, and **React**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **JWT Authentication** | Signup, login, bcrypt-hashed passwords, 24-hour tokens |
| 🏢 **Workspaces** | Create isolated team workspaces, invite members by email |
| 👥 **Roles** | Owner (full control) · Editor (add memories) · Viewer (read & ask only) |
| 🧠 **Semantic Memory** | Store rules as 768-dim Gemini embeddings in MongoDB Atlas |
| 🔍 **Vector RAG Search** | Ask questions; AI retrieves relevant rules via `$vectorSearch` |
| ⚡ **Live Sync** | MongoDB Change Streams + WebSockets push new memories instantly |
| ⏱️ **TTL Expiry** | Memories auto-delete when their expiry date is reached |
| 💻 **CLI** | Legacy CLI (`remember`, `ask`, `sync`) fully preserved and working |
| 🎨 **React Frontend** | Dark, minimal, responsive UI — Login · Dashboard · Workspace · Members |

---

## 🗂️ Folder Structure

```
agentic-mem/
├── server/                     # FastAPI backend
│   ├── main.py                 # App entrypoint, CORS, legacy CLI routes, WebSocket
│   ├── database.py             # MongoDB Atlas client, all CRUD helpers
│   ├── llm.py                  # Google Gemini — embeddings + rule extraction + RAG
│   ├── auth.py                 # JWT creation/verification, bcrypt, get_current_user
│   └── routers/
│       ├── auth_router.py      # POST /auth/signup  POST /auth/login  GET /auth/me
│       ├── workspace_router.py # CRUD /workspaces + member management
│       └── memory_router.py    # POST /memories/remember  GET /memories  POST /memories/ask
│
├── cli/                        # Legacy Typer CLI (unchanged, still fully works)
│   ├── main.py                 # remember · ask · sync commands
│   ├── connection.py           # HTTP + WebSocket client
│   └── file_manager.py        # Writes rules to .agent_rules.md
│
├── frontend/                   # React + Vite + Tailwind CSS
│   └── src/
│       ├── App.jsx             # Router with protected routes
│       ├── lib/api.js          # Centralized fetch-based API client
│       ├── context/
│       │   └── AuthContext.jsx # User state, login/signup/logout, token persistence
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── MemoryCard.jsx
│       │   ├── AIChatPanel.jsx
│       │   ├── MemberList.jsx
│       │   ├── InviteModal.jsx
│       │   └── ProtectedRoute.jsx
│       └── pages/
│           ├── Login.jsx
│           ├── Signup.jsx
│           ├── Dashboard.jsx
│           ├── WorkspacePage.jsx
│           └── MembersPage.jsx
│
├── requirements.txt
├── .env                        # All secrets (never commit this)
└── README.md
```

---

## ⚙️ Prerequisites

- **Python 3.12+** (use `venv312`)
- **Node.js 18+** and `npm`
- **MongoDB Atlas** cluster (M0 Free Tier works)
  - Vector Search index named `vector_index` on `agent_db.agent_memories`
  - IP `0.0.0.0/0` allowed in Network Access
- **Google Gemini API Key**

---

## 🚀 Setup Instructions

### 1. Clone and enter project

```powershell
git clone <your-repo-url>
cd agentic-mem
```

### 2. Create Python virtual environment

```powershell
python -m venv venv312
.\venv312\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Create `.env` file

```env
# CLI networking (update IP to your server machine's LAN IP)
SERVER_URL="http://127.0.0.1:8000"
WS_URL="ws://127.0.0.1:8000/ws"
RULES_FILE=".agent_rules.md"

# MongoDB Atlas (choose Python async driver when copying connection string)
MONGODB_URI="mongodb+srv://<user>:<password>@<cluster>.mongodb.net/"

# Google Gemini
GEMINI_API_KEY="your_gemini_api_key"

# JWT — change this to a long random string in production!
JWT_SECRET="your-super-secret-jwt-key-change-this"
```

### 4. Set up MongoDB Atlas Vector Search Index

In your Atlas cluster, go to **Atlas Search → Create Index → JSON Editor**, target `agent_db.agent_memories`, name it `vector_index`:

```json
{
  "fields": [
    {
      "numDimensions": 768,
      "path": "embedding",
      "similarity": "cosine",
      "type": "vector"
    }
  ]
}
```

### 5. Install and run the frontend

```powershell
cd frontend
npm install
```

Create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

---

## ▶️ Running the Project

### Terminal 1 — Start Backend

```powershell
# From project root, with venv312 activated
.\venv312\Scripts\Activate.ps1
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2 — Start Frontend

```powershell
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

### Terminal 3 (Optional) — Legacy CLI Sync

```powershell
.\venv312\Scripts\Activate.ps1
python -m cli.main sync
```

---

## 🔌 API Endpoints

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/signup` | ❌ | Register new user |
| `POST` | `/auth/login` | ❌ | Login, get JWT token |
| `GET` | `/auth/me` | ✅ | Get current user info |

### Workspaces
| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| `POST` | `/workspaces` | ✅ | Any | Create workspace |
| `GET` | `/workspaces` | ✅ | Any | List your workspaces |
| `GET` | `/workspaces/{id}` | ✅ | Member | Get workspace details |
| `POST` | `/workspaces/{id}/members` | ✅ | Owner | Invite member by email |
| `DELETE` | `/workspaces/{id}/members/{email}` | ✅ | Owner | Remove member |
| `PATCH` | `/workspaces/{id}/members/{email}/role` | ✅ | Owner | Change member role |

### Memories (Workspace-scoped)
| Method | Endpoint | Auth | Role | Description |
|---|---|---|---|---|
| `POST` | `/memories/remember` | ✅ | Editor/Owner | Extract + embed + store rule |
| `GET` | `/memories?workspace_id=...` | ✅ | Any member | List workspace memories |
| `POST` | `/memories/ask` | ✅ | Any member | RAG Q&A using Gemini |
| `DELETE` | `/memories/{id}?workspace_id=...` | ✅ | Owner | Delete a memory |

### Legacy CLI (Unauthenticated, preserved)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/remember` | Save a rule anonymously |
| `POST` | `/ask` | Ask across all memories |
| `WS` | `/ws` | Anonymous live sync |
| `WS` | `/ws?token=...&workspace_id=...` | Authenticated workspace sync |

---

## 💻 CLI Usage (Legacy)

```powershell
# Activate venv
.\venv312\Scripts\Activate.ps1

# Save a rule to shared memory
python -m cli.main remember "All React components must use functional style with hooks"

# Ask a question via RAG
python -m cli.main ask "Can I use class components?"

# Listen for live updates from teammates (in a separate terminal)
python -m cli.main sync
```

---

## 🎨 Frontend Pages

| Page | Route | Description |
|---|---|---|
| **Login** | `/` | Sign into your account |
| **Signup** | `/signup` | Create a new account |
| **Dashboard** | `/dashboard` | View and create workspaces |
| **Workspace** | `/workspace/:id` | Shared memories + AI chat panel |
| **Members** | `/workspace/:id/members` | Invite, remove, and update roles |

---

## 🗃️ MongoDB Collections

### `users`
```json
{ "email": "...", "name": "...", "hashed_password": "...", "created_at": "..." }
```

### `workspaces`
```json
{
  "name": "Team Alpha",
  "owner_id": "...",
  "members": [
    { "user_id": "...", "email": "...", "name": "...", "role": "owner|editor|viewer" }
  ]
}
```

### `agent_memories` (extended, backward-compatible)
```json
{
  "content": "All API endpoints must return JSON...",
  "embedding": [0.02, -0.11, ...],
  "expiresAt": "2036-01-01T00:00:00Z",
  "workspace_id": "...",
  "owner": "alice@example.com",
  "created_at": "..."
}
```

---

## 🔒 Security Notes

- **Never commit `.env`** — it contains your MongoDB URI, Gemini API key, and JWT secret.
- **JWT secret** must be a long random string in production. Generate with:
  ```python
  import secrets; print(secrets.token_hex(32))
  ```
- **MongoDB Network Access** — for hackathon, `0.0.0.0/0` is fine. For production, restrict to your server's IP.
- **Passwords** are hashed with bcrypt (cost factor 12). Never stored in plaintext.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Database | MongoDB Atlas (Vector Search, Change Streams, TTL) |
| AI / Embeddings | Google Gemini (`gemini-3.8-flash`, `gemini-embedding-2`) |
| Auth | JWT (`python-jose`), bcrypt (`passlib`) |
| Frontend | React 19, Vite, Tailwind CSS 3, React Router v7 |
| CLI | Typer, websockets, requests |

---

## 📋 Hackathon MongoDB Features Used

| Feature | Where Used |
|---|---|
| **`$vectorSearch`** | Semantic RAG in `/memories/ask` and `/ask` |
| **Change Streams** | `database.collection.watch()` → WebSocket broadcast |
| **TTL Index** | `expiresAt` field — auto-expire stale memories |
| **Vector Index (cosine, 768d)** | `gemini-embedding-2` embeddings |
| **Metadata Filtering** | `workspace_id` filter in `$vectorSearch` pre-filter |
| **Document Model** | Embedded members array in workspaces collection |

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `SSL handshake failed` on startup | Add `0.0.0.0/0` to MongoDB Atlas → Network Access |
| `ImportError: cannot import 'genai'` | Run `pip install google-genai` in your active venv |
| `WebSocket timed out` | Update `.env` `WS_URL` to server machine's current LAN IP |
| `401 Unauthorized` on API | Token expired — log out and log back in |
| `404 vector_index not found` | Create the Atlas Search index (see Setup Step 4) |
| Frontend shows blank page | Check `VITE_API_URL` in `frontend/.env`, ensure backend is running |
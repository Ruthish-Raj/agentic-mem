import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import Navbar from "../components/Navbar";
import MemoryCard from "../components/MemoryCard";
import AIChatPanel from "../components/AIChatPanel";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function WorkspacePage() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState(null);
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newRule, setNewRule] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState("");
  const wsRef = useRef(null);

  const userRole = workspace?.members?.find((m) => m.email === user?.email)?.role;
  const isOwner = userRole === "owner";
  const canEdit = userRole === "owner" || userRole === "editor";

  const fetchData = async () => {
    try {
      const [ws, mem] = await Promise.all([api.getWorkspace(id), api.listMemories(id)]);
      setWorkspace(ws);
      setMemories(mem.memories || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  // Authenticated WebSocket for live sync
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    const ws = new WebSocket(`${API_URL.replace("http", "ws")}/ws?token=${token}&workspace_id=${id}`);
    wsRef.current = ws;
    ws.onmessage = (e) => {
      if (e.data.startsWith("NEW_RULE:")) {
        fetchData(); // refresh memory list
      }
    };
    return () => ws.close();
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleRemember = async (e) => {
    e.preventDefault();
    if (!newRule.trim()) return;
    setSaving(true);
    setSaveMsg("");
    try {
      const res = await api.remember(id, newRule.trim());
      setSaveMsg(res.status === "No rule detected" ? "⚠️ No rule detected in input." : "✅ " + res.content);
      setNewRule("");
      await fetchData();
    } catch (err) {
      setSaveMsg("❌ " + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (memId) => {
    if (!confirm("Delete this memory?")) return;
    try {
      await api.deleteMemory(memId, id);
      setMemories((m) => m.filter((x) => x._id !== memId));
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <div className="flex items-center justify-center h-64 text-gray-400">Loading workspace...</div>
    </div>
  );

  if (!workspace) return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <div className="flex flex-col items-center justify-center h-64 text-gray-400">
        <p>Workspace not found.</p>
        <button onClick={() => navigate("/dashboard")} className="mt-3 text-indigo-400 text-sm">← Back</button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate("/dashboard")} className="text-gray-500 hover:text-gray-300 transition text-sm">
              ← Dashboard
            </button>
            <span className="text-gray-700">/</span>
            <h1 className="text-lg font-bold text-white">{workspace.name}</h1>
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              userRole === "owner" ? "bg-yellow-900 text-yellow-300" :
              userRole === "editor" ? "bg-blue-900 text-blue-300" : "bg-gray-700 text-gray-300"
            }`}>{userRole}</span>
          </div>
          <Link
            to={`/workspace/${id}/members`}
            className="text-sm text-gray-400 hover:text-white transition flex items-center gap-1"
          >
            👥 {workspace.members?.length} member{workspace.members?.length !== 1 ? "s" : ""}
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left: Memories */}
          <div className="lg:col-span-3 flex flex-col gap-4">
            {/* Add memory (editor/owner only) */}
            {canEdit && (
              <form onSubmit={handleRemember} className="bg-gray-900 border border-gray-700 rounded-xl p-4">
                <label className="text-xs text-gray-400 mb-2 block">Add a project rule or constraint</label>
                <textarea
                  value={newRule}
                  onChange={(e) => setNewRule(e.target.value)}
                  rows={3}
                  placeholder="e.g. All API endpoints must return JSON with snake_case keys..."
                  className="w-full bg-gray-800 text-gray-100 placeholder-gray-500 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 transition resize-none"
                />
                <div className="flex items-center justify-between mt-3">
                  <span className="text-xs text-gray-500">{saveMsg}</span>
                  <button
                    type="submit"
                    disabled={saving}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition"
                  >
                    {saving ? "Saving..." : "Remember"}
                  </button>
                </div>
              </form>
            )}

            {/* Memory list */}
            <div className="space-y-3">
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                Shared Memories · {memories.length}
              </h2>
              {memories.length === 0 ? (
                <div className="text-center py-10 text-gray-600">
                  <p className="text-3xl mb-2">📭</p>
                  <p>No memories yet. Add a project rule above!</p>
                </div>
              ) : (
                memories.map((m) => (
                  <MemoryCard
                    key={m._id}
                    memory={m}
                    isOwner={isOwner}
                    onDelete={handleDelete}
                  />
                ))
              )}
            </div>
          </div>

          {/* Right: AI Chat */}
          <div className="lg:col-span-2 h-[600px]">
            <AIChatPanel workspaceId={id} />
          </div>
        </div>
      </main>
    </div>
  );
}

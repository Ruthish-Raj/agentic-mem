import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import Navbar from "../components/Navbar";

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const fetchWorkspaces = async () => {
    try {
      const data = await api.listWorkspaces();
      setWorkspaces(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const ws = await api.createWorkspace(newName.trim());
      setWorkspaces((prev) => [ws, ...prev]);
      setNewName("");
      setShowForm(false);
    } catch (e) {
      console.error(e);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-white">
              Welcome, {user?.name || user?.email} 👋
            </h1>
            <p className="text-gray-400 text-sm mt-0.5">Your workspaces</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 py-2 rounded-lg font-medium transition"
          >
            + New Workspace
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleCreate} className="bg-gray-900 border border-gray-700 rounded-xl p-4 mb-6 flex gap-3">
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Workspace name..."
              className="flex-1 bg-gray-800 text-gray-100 placeholder-gray-500 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 transition"
              autoFocus
            />
            <button
              type="submit"
              disabled={creating}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
            >
              {creating ? "Creating..." : "Create"}
            </button>
          </form>
        )}

        {loading ? (
          <div className="text-center text-gray-500 py-16">Loading workspaces...</div>
        ) : workspaces.length === 0 ? (
          <div className="text-center py-16 text-gray-500">
            <p className="text-4xl mb-3">🏗️</p>
            <p>No workspaces yet. Create one to get started!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {workspaces.map((ws) => {
              const role = ws.members?.find((m) => m.email === user?.email)?.role;
              return (
                <div
                  key={ws._id}
                  onClick={() => navigate(`/workspace/${ws._id}`)}
                  className="bg-gray-900 border border-gray-700 hover:border-indigo-500 rounded-xl p-5 cursor-pointer transition group"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-white font-semibold text-base group-hover:text-indigo-300 transition">{ws.name}</h3>
                      <p className="text-gray-500 text-xs mt-1">
                        {ws.members?.length || 0} member{ws.members?.length !== 1 ? "s" : ""}
                      </p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      role === "owner" ? "bg-yellow-900 text-yellow-300" :
                      role === "editor" ? "bg-blue-900 text-blue-300" :
                      "bg-gray-700 text-gray-300"
                    }`}>
                      {role}
                    </span>
                  </div>
                  <div className="mt-3 text-indigo-400 text-xs font-medium opacity-0 group-hover:opacity-100 transition">
                    Open workspace →
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import Navbar from "../components/Navbar";
import MemberList from "../components/MemberList";
import InviteModal from "../components/InviteModal";

export default function MembersPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showInvite, setShowInvite] = useState(false);

  const userRole = workspace?.members?.find((m) => m.email === user?.email)?.role;
  const isOwner = userRole === "owner";

  const fetchWorkspace = async () => {
    try {
      const ws = await api.getWorkspace(id);
      setWorkspace(ws);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspace();
  }, [id]);

  const handleRemove = async (email) => {
    if (!confirm(`Remove ${email} from workspace?`)) return;
    try {
      await api.removeMember(id, email);
      fetchWorkspace();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleChangeRole = async (email, role) => {
    try {
      await api.updateRole(id, email, role);
      fetchWorkspace();
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <div className="flex items-center justify-center h-64 text-gray-400">Loading...</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      <main className="max-w-2xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate(`/workspace/${id}`)}
              className="text-gray-500 hover:text-gray-300 transition text-sm"
            >
              ← Back
            </button>
            <span className="text-gray-700">/</span>
            <h1 className="text-lg font-bold text-white">
              {workspace?.name} · Members
            </h1>
          </div>
          {isOwner && (
            <button
              onClick={() => setShowInvite(true)}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 py-2 rounded-lg font-medium transition"
            >
              + Invite
            </button>
          )}
        </div>

        <MemberList
          members={workspace?.members || []}
          currentUserEmail={user?.email}
          isOwner={isOwner}
          onRemove={handleRemove}
          onChangeRole={handleChangeRole}
        />
      </main>

      {showInvite && (
        <InviteModal
          workspaceId={id}
          onClose={() => setShowInvite(false)}
          onInvited={fetchWorkspace}
        />
      )}
    </div>
  );
}

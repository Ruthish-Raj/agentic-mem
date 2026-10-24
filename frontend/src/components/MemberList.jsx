const ROLE_COLORS = {
  owner: "bg-yellow-900 text-yellow-300",
  editor: "bg-blue-900 text-blue-300",
  viewer: "bg-gray-700 text-gray-300",
};

export default function MemberList({ members, currentUserEmail, isOwner, onRemove, onChangeRole }) {
  return (
    <div className="space-y-2">
      {members.map((member) => (
        <div
          key={member.email}
          className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-indigo-700 flex items-center justify-center text-white font-bold text-sm">
              {(member.name || member.email)[0].toUpperCase()}
            </div>
            <div>
              <p className="text-gray-100 text-sm font-medium">{member.name || member.email}</p>
              <p className="text-gray-500 text-xs">{member.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${ROLE_COLORS[member.role]}`}>
              {member.role}
            </span>

            {isOwner && member.email !== currentUserEmail && (
              <>
                <select
                  defaultValue={member.role}
                  onChange={(e) => onChangeRole(member.email, e.target.value)}
                  className="text-xs bg-gray-700 text-gray-300 border border-gray-600 rounded-lg px-2 py-1 focus:outline-none focus:border-indigo-500"
                >
                  <option value="editor">Editor</option>
                  <option value="viewer">Viewer</option>
                </select>
                <button
                  onClick={() => onRemove(member.email)}
                  className="text-xs text-red-400 hover:text-red-300 transition"
                >
                  Remove
                </button>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

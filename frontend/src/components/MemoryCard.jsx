export default function MemoryCard({ memory, onDelete, isOwner }) {
  const date = memory.created_at
    ? new Date(memory.created_at).toLocaleDateString("en-IN", {
        day: "numeric", month: "short", year: "numeric",
      })
    : "";

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 flex flex-col gap-2 hover:border-indigo-500 transition group">
      <p className="text-gray-100 text-sm leading-relaxed">{memory.content}</p>
      <div className="flex items-center justify-between mt-1">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          {memory.owner && (
            <span className="bg-gray-700 px-2 py-0.5 rounded-full">
              👤 {memory.owner}
            </span>
          )}
          {date && <span>{date}</span>}
        </div>
        {isOwner && (
          <button
            onClick={() => onDelete(memory._id)}
            className="text-xs text-red-400 hover:text-red-300 opacity-0 group-hover:opacity-100 transition"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}

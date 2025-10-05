export default function TaskRow({ t }) {
  return (
    <div className="p-2 border rounded-xl text-sm">
      <div className="font-medium truncate">{t.title}</div>
      <div className="text-xs text-neutral-500">
        assignee: {t.assignee} {t.due_iso && `• due: ${t.due_iso}`}
      </div>
    </div>
  );
}

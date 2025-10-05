import Button from "./Button";

export default function DateRange({ start, end, setStart, setEnd, onRun }) {
  return (
    <div className="flex items-end gap-3">
      <div>
        <label className="text-xs block mb-1">Start</label>
        <input type="date" value={start} onChange={e => setStart(e.target.value)} className="input" />
      </div>
      <div>
        <label className="text-xs block mb-1">End</label>
        <input type="date" value={end} onChange={e => setEnd(e.target.value)} className="input" />
      </div>
      <Button onClick={onRun}>Generate</Button>
    </div>
  );
}

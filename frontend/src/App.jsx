import { useEffect, useState } from "react";
import Header from "./components/Header";
import Card from "./components/Card";
import DateRange from "./components/DateRange";
import ListSkeleton from "./components/ListSkeleton";
import Empty from "./components/Empty";
import TaskRow from "./components/TaskRow";
import Button from "./components/Button";
import {
  emailsInRange,
  getSummary,
  extractActions,
  summarizeEmail,
  authStatus,
  authLogout,
} from "./api";

function useTodayRange(days = 7) {
  const d = new Date();
  const end = d.toISOString().slice(0, 10);
  d.setDate(d.getDate() - days);
  const start = d.toISOString().slice(0, 10);
  return { start, end };
}

export default function App() {
  const init = useTodayRange(7);
  const [start, setStart] = useState(init.start);
  const [end, setEnd] = useState(init.end);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState([]);
  const [emails, setEmails] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [connected, setConnected] = useState(false);

  // check connection on load
  useEffect(() => {
    authStatus().then((s) => setConnected(!!s.connected)).catch(() => setConnected(false));
  }, []);

  const run = async () => {
    setLoading(true);
    try {
      const [e, s] = await Promise.all([emailsInRange(start, end), getSummary(start, end)]);
      setEmails(e.messages || []);
      setSummary(s.highlights || []);
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  const onSummarize = async (body) => {
    if (!body?.trim()) {
      alert("No email body available to summarize.");
      return;
    }
    const { tldr } = await summarizeEmail(body);
    alert(tldr);
  };

  const onExtract = async (body) => {
    if (!body?.trim()) return;
    const { tasks: found } = await extractActions(body);
    if (!found?.length) {
      alert("No clear action items detected (MVP rules).");
      return;
    }
    setTasks((prev) => [...found, ...prev]);
  };

  const onLogout = async () => {
    await authLogout();
    setConnected(false);
    setEmails([]);
    setSummary([]);
    setTasks([]);
  };

  return (
    <div className="container-page">
      <Header connected={connected} onLogout={onLogout} />

      <div className="mt-5 mb-6">
        <Card title="Pick a date range" subtitle="Generate highlights and list emails for this window.">
          <div className="flex items-center justify-between gap-3">
            <DateRange start={start} end={end} setStart={setStart} setEnd={setEnd} onRun={run} />
            <div className="subtle">Tip: Start with the last 7–14 days to keep it fast.</div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Executive Summary */}
        <Card title="Summary" subtitle="Concise highlights from the selected dates.">
          {loading ? (
            <ListSkeleton />
          ) : summary.length ? (
            <ul className="space-y-2 list-disc ml-5">
              {summary.map((b, i) => (
                <li key={i} className="text-sm">{b}</li>
              ))}
            </ul>
          ) : (
            <Empty hint="Choose a date range and click Generate." />
          )}
        </Card>

        {/* Emails */}
        <Card title="Emails" subtitle="Recent messages (Summarize or Extract tasks).">
          {loading ? (
            <ListSkeleton />
          ) : emails.length ? (
            <ul className="space-y-2">
              {emails.map((m) => (
                <li key={m.id} className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-xl">
                  <div className="font-medium">{m.subject || "(no subject)"}</div>
                  <div className="subtle mt-0.5">{m.from_email}</div>
                  <div className="flex gap-3 mt-2">
                    <button className="link text-xs" onClick={() => onSummarize(m.body_text)}>Summarize</button>
                    <button className="link text-xs" onClick={() => onExtract(m.body_text)}>Extract tasks</button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <Empty hint="No emails listed yet." />
          )}
        </Card>

        {/* Tasks */}
        <Card title="Tasks" subtitle="Detected action items">
          {tasks.length ? (
            <div className="space-y-2">{tasks.map((t) => <TaskRow key={t.id} t={t} />)}</div>
          ) : (
            <Empty hint="Choose Extract tasks on any email." />
          )}
        </Card>
      </div>

      
    </div>
  );
}

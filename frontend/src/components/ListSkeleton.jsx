export default function ListSkeleton({rows=6}){
  return (
    <ul className="space-y-2 animate-pulse">
      {Array.from({length: rows}).map((_,i)=> (
        <li key={i} className="h-6 bg-neutral-200 dark:bg-neutral-800 rounded"></li>
      ))}
    </ul>
  );}

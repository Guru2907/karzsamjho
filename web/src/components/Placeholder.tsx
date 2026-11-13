// Temporary page header used until each task builds the real page.
export function Placeholder({ title, task }: { title: string; task: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{task}</p>
    </div>
  )
}

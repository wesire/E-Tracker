export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between text-center">
        <h1 className="text-4xl font-bold mb-4">Economy Tracker</h1>
        <p className="text-xl text-muted-foreground mb-8">
          Actionable macroeconomic insights across countries and regions
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <div className="border rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-2">Dashboard</h2>
            <p className="text-muted-foreground">View key macro indicators and insights</p>
          </div>
          <div className="border rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-2">Explorer</h2>
            <p className="text-muted-foreground">Explore historical economic data</p>
          </div>
          <div className="border rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-2">Compare</h2>
            <p className="text-muted-foreground">Compare countries side by side</p>
          </div>
        </div>
      </div>
    </main>
  );
}

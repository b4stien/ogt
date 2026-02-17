import { GridEditor } from "@/components/GridEditor";

function App() {
  return (
    <div className="min-h-screen p-8 pl-18">
      <div className="max-w-3xl">
        <div className="mb-10 rounded border border-yellow-400 bg-yellow-50 px-4 py-3 text-sm text-yellow-900">
          <strong>Beta:</strong> This generator is still in beta. Please verify
          its output, inspect the generated STEP/STL file, and do a small test
          print before committing to larger projects.
        </div>
        <h1 className="text-2xl font-bold mb-6">openGrid Generator</h1>
      </div>
      <GridEditor />
    </div>
  );
}

export default App;

import { Link, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import AiIntelligence from "./pages/AiIntelligence";
import Dashboard from "./pages/Dashboard";
import IncidentDetail from "./pages/IncidentDetail";
import Incidents from "./pages/Incidents";
import Landing from "./pages/Landing";

function NotFound() {
  return (
    <div className="p-10 text-slate-300">
      Page not found.{" "}
      <Link to="/" className="text-cyan-300">
        Go home
      </Link>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/incidents" element={<Incidents />} />
        <Route path="/incidents/:id" element={<IncidentDetail />} />
        <Route path="/ai" element={<AiIntelligence />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

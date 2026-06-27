import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import Landing from "./pages/Landing.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Simulator from "./pages/Simulator.jsx";
import Optimize from "./pages/Optimize.jsx";
import CostAdvisor from "./pages/CostAdvisor.jsx";
import Reports from "./pages/Reports.jsx";

export default function App() {
  return (
    <div className="min-h-full flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/simulator" element={<Simulator />} />
          <Route path="/optimize" element={<Optimize />} />
          <Route path="/cost" element={<CostAdvisor />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="*" element={<Landing />} />
        </Routes>
      </main>
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-sm text-slate-500">
        UrbanCool AI — AI-powered urban heat mitigation decision-support platform
      </footer>
    </div>
  );
}

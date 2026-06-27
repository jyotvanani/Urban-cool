import { Link } from "react-router-dom";
import {
  MapPin,
  BarChart3,
  SlidersHorizontal,
  FileText,
  ArrowRight,
  Sun,
} from "lucide-react";

const features = [
  {
    icon: MapPin,
    title: "Heat Hotspot Detection",
    desc: "Identify and map urban heat hotspots across the city using satellite-derived indicators.",
  },
  {
    icon: BarChart3,
    title: "Driver Analysis",
    desc: "Understand why a zone is hot — vegetation loss, built-up density, surface temperature and more.",
  },
  {
    icon: SlidersHorizontal,
    title: "Cooling Simulation",
    desc: "Simulate tree cover, cool roofs and other interventions to estimate temperature reduction.",
  },
  {
    icon: FileText,
    title: "Smart Reports",
    desc: "Generate clear, planner-ready reports with recommended actions and priorities.",
  },
];

const workflow = ["Detect", "Explain", "Simulate", "Recommend", "Report"];

export default function Landing() {
  return (
    <div className="mx-auto max-w-7xl px-4">
      {/* Hero */}
      <section className="py-16 text-center md:py-24">
        <span className="inline-flex items-center gap-2 rounded-full bg-teal-50 px-4 py-1.5 text-sm font-medium text-teal-700">
          <Sun size={16} /> Climate Resilience for Cities
        </span>
        <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-extrabold tracking-tight text-slate-900 md:text-5xl">
          UrbanCool <span className="text-brand">AI</span>
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
          AI-powered urban heat mitigation decision-support platform.
        </p>
        <p className="mx-auto mt-3 max-w-2xl text-sm text-slate-500">
          Cities are heating up. Dense construction, vanishing greenery and
          limited water bodies create dangerous urban heat islands. UrbanCool AI
          helps planners detect hotspots, understand their causes and choose the
          most effective cooling strategies — backed by data.
        </p>

        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 rounded-lg bg-brand px-6 py-3 font-medium text-white transition hover:bg-brand-dark"
          >
            Open Dashboard <ArrowRight size={18} />
          </Link>
          <Link
            to="/simulator"
            className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-6 py-3 font-medium text-slate-700 transition hover:bg-slate-50"
          >
            Cooling Simulator
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="grid gap-5 pb-12 sm:grid-cols-2 lg:grid-cols-4">
        {features.map((f) => (
          <div
            key={f.title}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md"
          >
            <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
              <f.icon size={22} />
            </span>
            <h3 className="mt-4 font-semibold text-slate-800">{f.title}</h3>
            <p className="mt-1 text-sm text-slate-500">{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Workflow */}
      <section className="mb-20 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <h2 className="text-center text-xl font-bold text-slate-800">
          How It Works
        </h2>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
          {workflow.map((step, i) => (
            <div key={step} className="flex items-center gap-2">
              <span className="rounded-full bg-teal-50 px-4 py-2 text-sm font-semibold text-teal-700">
                {step}
              </span>
              {i < workflow.length - 1 && (
                <ArrowRight size={18} className="text-slate-300" />
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

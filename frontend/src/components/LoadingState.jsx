import { Loader2 } from "lucide-react";

export default function LoadingState({ label = "Loading data..." }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-slate-200 bg-white p-10 text-slate-500">
      <Loader2 className="animate-spin text-brand" size={32} />
      <p className="text-sm font-medium">{label}</p>
    </div>
  );
}

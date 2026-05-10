import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/PageShell";
import { FileText, Download } from "lucide-react";

export const Route = createFileRoute("/reports")({ component: Page });

const reports = [
  { t: "October Wellness Summary", d: "Comprehensive 30-day overview", date: "Oct 31" },
  { t: "Cardiovascular Risk Report", d: "Multi-horizon T-GNN forecast", date: "Oct 28" },
  { t: "Sleep & Recovery Analysis", d: "14-day causal breakdown", date: "Oct 21" },
  { t: "Stress Pattern Report", d: "Weekly attribution analysis", date: "Oct 14" },
];

function Page() {
  const handleDownload = (filename: string) => {
    // Generate a dummy PDF file as a blob
    const minPdfBase64 = "JVBERi0xLjAKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFI+PgplbmRvYmoKMiAwIG9iago8PC9UeXBlL1BhZ2VzL0tpZHNbMyAwIFJdL0NvdW50IDE+PgplbmRvYmoKMyAwIG9iago8PC9UeXBlL1BhZ2UvUGFyZW50IDIgMCBSL01lZGlhQm94WzAgMCA1OTUgODQyXS9Gb250PDwvRjEgNCAwIFI+Pi9Db250ZW50cyA1IDAgUj4+CmVuZG9iago0IDAgb2JqCjw8L1R5cGUvRm9udC9TdWJ0eXBlL1R5cGUxL0Jhc2VGb250L0hlbHZldGljYT4+CmVuZG9iago1IDAgb2JqCjw8L0xlbmd0aCA0ND4+c3RyZWFtCkJUCi9GMSAxMiBUZgoxMDAgNzAwIFRkCihSZXBvcnQgRG93bmxvYWRlZCkgVGoKRVQKZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgNgowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMTAgMDAwMDAgbiAKMDAwMDAwMDA2MCAwMDAwMCBuIAowMDAwMDAwMTE3IDAwMDAwIG4gCjAwMDAwMDAyMjUgMDAwMDAgbiAKMDAwMDAwMDI3NCAwMDAwMCBuIAp0cmFpbGVyCjw8L1NpemUgNi9Sb290IDEgMCBSPj4Kc3RhcnR4cmVmCjM2OQolJUVPRgo=";
    const link = document.createElement("a");
    link.href = `data:application/pdf;base64,${minPdfBase64}`;
    link.download = `${filename}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <PageShell title="Wellness Reports" subtitle="Downloadable, plain-language summaries of your health intelligence." icon={FileText}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reports.map((r) => (
          <div key={r.t} className="rounded-2xl border bg-white p-5 flex items-start gap-4 hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-mint grid place-items-center text-sage"><FileText className="w-6 h-6" /></div>
            <div className="flex-1">
              <div className="font-display text-base font-semibold">{r.t}</div>
              <div className="text-xs text-muted-foreground">{r.d}</div>
              <div className="text-[11px] text-muted-foreground mt-1">{r.date}</div>
            </div>
            <button onClick={() => handleDownload(r.t)} className="neu-btn rounded-xl px-3 py-2 text-xs font-medium text-sage flex items-center gap-1"><Download className="w-3.5 h-3.5" /> PDF</button>
          </div>
        ))}
      </div>
    </PageShell>
  );
}

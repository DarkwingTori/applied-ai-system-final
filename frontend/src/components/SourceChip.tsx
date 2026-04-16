import { useState } from "react";

interface Props {
  sources: string[];
}

const SOURCE_LABELS: Record<string, string> = {
  dog_exercise: "Dog Exercise",
  cat_care: "Cat Care",
  medication_guidelines: "Medication",
  nutrition: "Nutrition",
  grooming: "Grooming",
  senior_pets: "Senior Pets",
  multi_pet: "Multi-Pet",
  enrichment: "Enrichment",
  health_warning_signs: "Health Signs",
};

export function SourceChip({ sources }: Props) {
  const [open, setOpen] = useState(false);

  if (sources.length === 0) return null;

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 text-xs text-pawpal-muted hover:text-brand-500 transition-colors"
      >
        <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
        {open ? "Hide" : "Show"} sources ({sources.length})
      </button>
      {open && (
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          {sources.map((src) => (
            <span
              key={src}
              className="inline-block rounded-full bg-brand-50 px-2.5 py-0.5 text-xs text-brand-700 border border-brand-100"
            >
              {SOURCE_LABELS[src] ?? src}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

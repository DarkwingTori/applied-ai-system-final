interface Props {
  confidence: number;
}

export function ConfidenceBadge({ confidence }: Props) {
  const pct = Math.round(confidence * 100);

  let colorClass = "bg-green-100 text-green-800";
  let label = "High confidence";
  if (confidence < 0.5) {
    colorClass = "bg-red-100 text-red-700";
    label = "Low confidence";
  } else if (confidence < 0.7) {
    colorClass = "bg-yellow-100 text-yellow-800";
    label = "Medium confidence";
  }

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClass}`}
      title={label}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current opacity-70" />
      {pct}% confidence
    </span>
  );
}

import type { ChatMessage } from "../types";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { SourceChip } from "./SourceChip";

interface Props {
  message: ChatMessage;
}

export function AdvisorMessage({ message }: Props) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-brand-500 px-4 py-3 text-sm text-white shadow-sm">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      {/* Avatar */}
      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-brand-100 flex items-center justify-center text-lg select-none">
        🐾
      </div>

      {/* Bubble */}
      <div className="max-w-[80%]">
        <div className="rounded-2xl rounded-tl-sm bg-white px-4 py-3 text-sm text-pawpal-text shadow-card border border-pawpal-border">
          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
        </div>

        {/* Meta */}
        <div className="mt-1.5 flex flex-wrap items-center gap-2 px-1">
          {message.confidence !== undefined && (
            <ConfidenceBadge confidence={message.confidence} />
          )}
          {message.sources && <SourceChip sources={message.sources} />}
        </div>

        {message.low_confidence && (
          <p className="mt-1.5 px-1 text-xs text-red-500">
            ⚠️ Low confidence — please consult your veterinarian for personalized advice.
          </p>
        )}
      </div>
    </div>
  );
}

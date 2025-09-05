import React, { useMemo, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { useUpload } from "@/context/UploadContext";
import { X } from "lucide-react";

interface PromptChipsInputProps {
  label?: string;
  placeholder?: string;
  helper?: string;
  className?: string;
  autoFocus?: boolean;
  id?: string;
}

const PromptChipsInput: React.FC<PromptChipsInputProps> = ({
  label = "Prompts",
  placeholder = "e.g., red car, person with backpack",
  helper,
  className,
  autoFocus,
  id = "prompts-input",
}) => {
const { prompts, setPrompts } = useUpload();
  const [value, setValue] = useState("");
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingValue, setEditingValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<number | null>(null);

  const onContainerClick = () => inputRef.current?.focus();

  const applyPrompts = (next: string[], immediate = false) => {
    if (immediate) return setPrompts(next);
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => setPrompts(next), 180);
  };

  const addParts = (text: string) => {
    const parts = text
      .split(",")
      .map((p) => p.trim())
      .filter(Boolean);
    if (parts.length === 0) return;
    const next = Array.from(new Set([...(prompts || []), ...parts]));
    applyPrompts(next);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      if (value.trim()) {
        addParts(value);
        setValue("");
      }
} else if (e.key === "Backspace" && value === "" && (prompts?.length ?? 0) > 0) {
      applyPrompts(prompts.slice(0, -1));
    }
  };

  const startEdit = (idx: number) => {
    setEditingIndex(idx);
    setEditingValue(prompts[idx] ?? "");
  };

const commitEdit = () => {
    if (editingIndex === null) return;
    const next = [...prompts];
    const val = editingValue.trim();
    if (val) next[editingIndex] = val;
    else next.splice(editingIndex, 1);
    applyPrompts(Array.from(new Set(next)));
    setEditingIndex(null);
    setEditingValue("");
  };

  const removeChip = (idx: number) => {
    const next = [...prompts];
    next.splice(idx, 1);
    applyPrompts(next);
  };

  const containerClasses = useMemo(
    () =>
      cn(
        "min-h-[46px] w-full rounded-[var(--radius)] border bg-background px-2 py-2 flex flex-wrap items-center gap-2",
        "focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2",
        "shadow-sm",
        className
      ),
    [className]
  );

  return (
    <div>
      <Label htmlFor={id} className="block text-sm font-medium mb-2">
        {label}
      </Label>
      <div className={containerClasses} onClick={onContainerClick}>
        {prompts?.map((p, i) => (
          <div key={`${p}-${i}`} className="flex items-center">
            {editingIndex === i ? (
              <Input
                value={editingValue}
                onChange={(e) => setEditingValue(e.target.value)}
                onBlur={commitEdit}
                onKeyDown={(e) => {
                  if (e.key === "Enter") commitEdit();
                  if (e.key === "Escape") {
                    setEditingIndex(null);
                    setEditingValue("");
                  }
                }}
                className="h-7 w-40"
                autoFocus
              />
            ) : (
              <Badge
                variant="secondary"
                className="h-7 gap-1 cursor-text select-none"
                onDoubleClick={() => startEdit(i)}
              >
                <span onClick={() => startEdit(i)}>{p}</span>
                <button
                  type="button"
                  aria-label={`Remove ${p}`}
                  className="ml-1 inline-flex items-center"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeChip(i);
                  }}
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </Badge>
            )}
          </div>
        ))}
        <Input
          id={id}
          ref={inputRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          aria-label={label}
          className="flex-1 min-w-[160px] border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
          autoFocus={autoFocus}
        />
      </div>
      {helper ? (
        <p className="text-xs text-muted-foreground mt-2">{helper}</p>
      ) : null}
    </div>
  );
};

export default PromptChipsInput;

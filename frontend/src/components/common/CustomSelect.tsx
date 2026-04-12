import { useEffect, useId, useMemo, useRef, useState } from "react";

export type SelectOption = {
  value: string;
  label: string;
  helper?: string;
  disabled?: boolean;
};

const SEARCH_THRESHOLD = 7;

type SelectVariant = "default" | "compact";

type CustomSelectProps = {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  variant?: SelectVariant;
  name?: string;
};

type CustomMultiSelectProps = {
  options: SelectOption[];
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  variant?: SelectVariant;
};

function useDismissableLayer(open: boolean, onClose: () => void, ref: React.RefObject<HTMLDivElement | null>) {
  useEffect(() => {
    if (!open) return;

    const handlePointerDown = (event: MouseEvent) => {
      if (!ref.current?.contains(event.target as Node)) {
        onClose();
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onClose, ref]);
}

export function CustomSelect({
  options,
  value,
  onChange,
  placeholder = "Select an option",
  disabled = false,
  className = "",
  variant = "default",
  name,
}: CustomSelectProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const rootRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const listId = useId();
  const selectedOption = useMemo(() => options.find((option) => option.value === value) ?? null, [options, value]);
  const searchable = options.length >= SEARCH_THRESHOLD;
  const filteredOptions = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return options;
    return options.filter((option) => option.label.toLowerCase().includes(query) || option.helper?.toLowerCase().includes(query));
  }, [options, search]);
  const enabledOptions = useMemo(() => filteredOptions.filter((option) => !option.disabled), [filteredOptions]);

  useDismissableLayer(open, () => setOpen(false), rootRef);

  useEffect(() => {
    if (!open) {
      setSearch("");
      setHighlightedIndex(-1);
      return;
    }

    const selectedIndex = filteredOptions.findIndex((option) => option.value === value && !option.disabled);
    setHighlightedIndex(selectedIndex >= 0 ? selectedIndex : filteredOptions.findIndex((option) => !option.disabled));

    if (searchable) {
      window.setTimeout(() => searchInputRef.current?.focus(), 0);
    }
  }, [filteredOptions, open, searchable, value]);

  useEffect(() => {
    if (!open || highlightedIndex < 0) return;
    optionRefs.current[highlightedIndex]?.scrollIntoView({ block: "nearest" });
  }, [highlightedIndex, open]);

  const closeMenu = () => {
    setOpen(false);
    setSearch("");
    setHighlightedIndex(-1);
  };

  const moveHighlight = (direction: 1 | -1) => {
    if (enabledOptions.length === 0) return;
    const currentIndex = enabledOptions.findIndex((option) => option.value === filteredOptions[highlightedIndex]?.value);
    const nextIndex = currentIndex < 0
      ? (direction === 1 ? 0 : enabledOptions.length - 1)
      : (currentIndex + direction + enabledOptions.length) % enabledOptions.length;
    const nextValue = enabledOptions[nextIndex]?.value;
    setHighlightedIndex(filteredOptions.findIndex((option) => option.value === nextValue));
  };

  const selectHighlighted = () => {
    const highlighted = filteredOptions[highlightedIndex];
    if (!highlighted || highlighted.disabled) return;
    onChange(highlighted.value);
    closeMenu();
  };

  const handleTriggerKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (disabled) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
    }
  };

  const handleMenuKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveHighlight(1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      moveHighlight(-1);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectHighlighted();
    }
  };

  return (
    <div
      ref={rootRef}
      className={`custom-select ${variant === "compact" ? "compact" : ""} ${open ? "open" : ""} ${className}`.trim()}
    >
      {name ? <input type="hidden" name={name} value={value} /> : null}
      <button
        type="button"
        className="custom-select-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        disabled={disabled}
        onClick={() => setOpen((current) => (disabled ? current : !current))}
        onKeyDown={handleTriggerKeyDown}
      >
        <span className={`custom-select-value ${selectedOption ? "" : "placeholder"}`.trim()}>
          {selectedOption?.label ?? placeholder}
        </span>
        <span className="custom-select-icon" aria-hidden="true" />
      </button>
      {open ? (
        <div id={listId} className="custom-select-menu" role="listbox" onKeyDown={handleMenuKeyDown}>
          {searchable ? (
            <div className="custom-select-search-wrap">
              <input
                ref={searchInputRef}
                className="custom-select-search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search..."
              />
            </div>
          ) : null}
          {filteredOptions.map((option, index) => (
            <button
              key={option.value}
              ref={(element) => {
                optionRefs.current[index] = element;
              }}
              type="button"
              role="option"
              aria-selected={option.value === value}
              className={`custom-select-option ${option.value === value ? "selected" : ""} ${index === highlightedIndex ? "highlighted" : ""}`.trim()}
              disabled={option.disabled}
              onMouseEnter={() => setHighlightedIndex(index)}
              onClick={() => {
                onChange(option.value);
                closeMenu();
              }}
            >
              <span>{option.label}</span>
              {option.helper ? <small>{option.helper}</small> : null}
            </button>
          ))}
          {filteredOptions.length === 0 ? <div className="custom-select-empty">No matching option</div> : null}
        </div>
      ) : null}
    </div>
  );
}

export function CustomMultiSelect({
  options,
  value,
  onChange,
  placeholder = "Select options",
  disabled = false,
  className = "",
  variant = "default",
}: CustomMultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const rootRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const optionRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const listId = useId();
  const searchable = options.length >= SEARCH_THRESHOLD;

  useDismissableLayer(open, () => setOpen(false), rootRef);

  const selectedLabels = useMemo(
    () => options.filter((option) => value.includes(option.value)).map((option) => option.label),
    [options, value],
  );

  const summary =
    selectedLabels.length === 0
      ? placeholder
      : selectedLabels.length <= 2
        ? selectedLabels.join(", ")
        : `${selectedLabels.length} selected`;

  const filteredOptions = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return options;
    return options.filter((option) => option.label.toLowerCase().includes(query) || option.helper?.toLowerCase().includes(query));
  }, [options, search]);

  const enabledOptions = useMemo(() => filteredOptions.filter((option) => !option.disabled), [filteredOptions]);

  useEffect(() => {
    if (!open) {
      setSearch("");
      setHighlightedIndex(-1);
      return;
    }

    setHighlightedIndex(filteredOptions.findIndex((option) => !option.disabled));
    if (searchable) {
      window.setTimeout(() => searchInputRef.current?.focus(), 0);
    }
  }, [filteredOptions, open, searchable]);

  useEffect(() => {
    if (!open || highlightedIndex < 0) return;
    optionRefs.current[highlightedIndex]?.scrollIntoView({ block: "nearest" });
  }, [highlightedIndex, open]);

  const moveHighlight = (direction: 1 | -1) => {
    if (enabledOptions.length === 0) return;
    const currentIndex = enabledOptions.findIndex((option) => option.value === filteredOptions[highlightedIndex]?.value);
    const nextIndex = currentIndex < 0
      ? (direction === 1 ? 0 : enabledOptions.length - 1)
      : (currentIndex + direction + enabledOptions.length) % enabledOptions.length;
    const nextValue = enabledOptions[nextIndex]?.value;
    setHighlightedIndex(filteredOptions.findIndex((option) => option.value === nextValue));
  };

  const toggleValue = (optionValue: string) => {
    const checked = value.includes(optionValue);
    onChange(checked ? value.filter((item) => item !== optionValue) : [...value, optionValue]);
  };

  const handleTriggerKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (disabled) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
    }
  };

  const handleMenuKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveHighlight(1);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      moveHighlight(-1);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      const highlighted = filteredOptions[highlightedIndex];
      if (!highlighted || highlighted.disabled) return;
      toggleValue(highlighted.value);
    }
  };

  return (
    <div
      ref={rootRef}
      className={`custom-select custom-multi-select ${variant === "compact" ? "compact" : ""} ${open ? "open" : ""} ${className}`.trim()}
    >
      <button
        type="button"
        className="custom-select-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        disabled={disabled}
        onClick={() => setOpen((current) => (disabled ? current : !current))}
        onKeyDown={handleTriggerKeyDown}
      >
        <span className={`custom-select-value ${selectedLabels.length > 0 ? "" : "placeholder"}`.trim()}>{summary}</span>
        <span className="custom-select-icon" aria-hidden="true" />
      </button>
      {open ? (
        <div
          id={listId}
          className="custom-select-menu custom-multi-select-menu"
          role="listbox"
          aria-multiselectable="true"
          onKeyDown={handleMenuKeyDown}
        >
          {searchable ? (
            <div className="custom-select-search-wrap">
              <input
                ref={searchInputRef}
                className="custom-select-search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search..."
              />
            </div>
          ) : null}
          {filteredOptions.map((option, index) => {
            const checked = value.includes(option.value);
            return (
              <button
                key={option.value}
                ref={(element) => {
                  optionRefs.current[index] = element;
                }}
                type="button"
                role="option"
                aria-selected={checked}
                className={`custom-select-option custom-multi-select-option ${checked ? "selected" : ""} ${index === highlightedIndex ? "highlighted" : ""}`.trim()}
                disabled={option.disabled}
                onMouseEnter={() => setHighlightedIndex(index)}
                onClick={() => toggleValue(option.value)}
              >
                <span className={`custom-checkmark ${checked ? "checked" : ""}`.trim()} aria-hidden="true" />
                <span>{option.label}</span>
              </button>
            );
          })}
          {filteredOptions.length === 0 ? <div className="custom-select-empty">No matching option</div> : null}
        </div>
      ) : null}
    </div>
  );
}

import { useEffect } from "react";

const TABLE_SELECTOR = ".table-card table, .connections-table";
const ACTIONS_FALLBACK_LABEL = "Actions";
const DETAILS_FALLBACK_LABEL = "Details";

function normalizeHeaderLabel(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

function resolveCellLabel(headers: string[], index: number): string {
  const directLabel = headers[index];
  if (directLabel) {
    return directLabel;
  }
  if (index === headers.length - 1) {
    return ACTIONS_FALLBACK_LABEL;
  }
  return DETAILS_FALLBACK_LABEL;
}

function annotateTable(table: HTMLTableElement): void {
  const headers = Array.from(table.querySelectorAll("thead th")).map((headerCell) =>
    normalizeHeaderLabel(headerCell.textContent ?? ""),
  );

  const rows = table.querySelectorAll("tbody tr");
  rows.forEach((row) => {
    const cells = Array.from(row.querySelectorAll("td"));
    cells.forEach((cell, index) => {
      if (cell.colSpan > 1) {
        cell.dataset.fullRow = "true";
        cell.removeAttribute("data-label");
        return;
      }

      const label = resolveCellLabel(headers, index);
      cell.dataset.fullRow = "false";
      if (cell.dataset.label !== label) {
        cell.dataset.label = label;
      }
    });
  });
}

function annotateAllTables(root: ParentNode): void {
  const tables = root.querySelectorAll<HTMLTableElement>(TABLE_SELECTOR);
  tables.forEach((table) => annotateTable(table));
}

export function useResponsiveTables(pathname: string): void {
  useEffect(() => {
    const scope = document.querySelector(".content") ?? document.body;
    annotateAllTables(scope);

    const observer = new MutationObserver((mutations) => {
      const shouldReprocess = mutations.some((mutation) => mutation.addedNodes.length > 0 || mutation.removedNodes.length > 0);
      if (shouldReprocess) {
        annotateAllTables(scope);
      }
    });

    observer.observe(scope, { childList: true, subtree: true });

    return () => {
      observer.disconnect();
    };
  }, [pathname]);
}


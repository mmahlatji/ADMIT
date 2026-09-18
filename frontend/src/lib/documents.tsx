// Both document endpoints answer with a short-lived signed URL rather than the
// file itself, so a document is fetched at click time and never held in a
// rendered href that would be expired by the time anyone used it.

import { Anchor } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { api } from "./api";
import type { DocumentDownload } from "../types/api";

/**
 * Claim a tab before doing any awaiting.
 *
 * A window.open() that runs after an await is no longer attributable to the
 * click that started it, and blockers stop it. Opening the tab blank up front
 * and pointing it somewhere once the URL arrives keeps it attributable.
 *
 * go() reports whether it had a tab to use. A blocker deliberately gets no
 * second attempt: sending the current tab to the file instead would take the
 * person off the page they were working on, losing an unsaved note or a
 * half-filled form, which is worse than the tab not opening.
 */
export function openTab() {
  const tab = window.open("", "_blank");
  if (tab) tab.opener = null;

  return {
    go(url: string): boolean {
      if (!tab) return false;
      tab.location.href = url;
      return true;
    },
    cancel() {
      tab?.close();
    },
  };
}

export async function signedUrlFor(path: string): Promise<string> {
  const download = await api.request<DocumentDownload>(path);
  return download.signed_url;
}

/** Hands back the link a blocked tab would have opened, while it is still valid. */
export function notifyTabBlocked(url: string, name: string) {
  notifications.show({
    color: "attention",
    title: "Your browser blocked the new tab",
    message: (
      <Anchor href={url} target="_blank" rel="noopener noreferrer" size="sm">
        Open {name}
      </Anchor>
    ),
    autoClose: false,
  });
}

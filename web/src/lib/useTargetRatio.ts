"use client";

import { useCallback, useSyncExternalStore } from "react";
import { DEFAULT_TARGET_RATIO } from "./constants";

const STORAGE_KEY = "target_ratio";
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  window.addEventListener("storage", emit);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", emit);
  };
}

function getSnapshot(): number {
  const stored = parseFloat(window.localStorage.getItem(STORAGE_KEY) ?? "");
  return Number.isFinite(stored) && stored >= 1 && stored <= 4
    ? stored
    : DEFAULT_TARGET_RATIO;
}

function getServerSnapshot(): number {
  return DEFAULT_TARGET_RATIO;
}

export function useTargetRatio(): [number, (value: number) => void] {
  const targetRatio = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const update = useCallback((value: number) => {
    const clamped = Math.min(Math.max(value, 1), 4);
    window.localStorage.setItem(STORAGE_KEY, String(clamped));
    emit();
  }, []);
  return [targetRatio, update];
}

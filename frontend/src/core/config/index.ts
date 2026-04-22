import { env } from "@/env";

function getBaseOrigin() {
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  // Fallback for SSR
  return "http://localhost:2026";
}

export function getBackendBaseURL() {
  if (env.NEXT_PUBLIC_BACKEND_BASE_URL) {
    // Check if the URL is already a full URL
    try {
      return new URL(env.NEXT_PUBLIC_BACKEND_BASE_URL).toString().replace(/\/+$/, "");
    } catch {
      // If it's not a full URL, use it as a path relative to the origin
      return new URL(
        env.NEXT_PUBLIC_BACKEND_BASE_URL,
        getBaseOrigin(),
      ).toString().replace(/\/+$/, "");
    }
  } else {
    return "";
  }
}

export function getLangGraphBaseURL(isMock?: boolean) {
  if (env.NEXT_PUBLIC_LANGGRAPH_BASE_URL) {
    // Check if the URL is already a full URL
    try {
      return new URL(env.NEXT_PUBLIC_LANGGRAPH_BASE_URL).toString();
    } catch {
      // If it's not a full URL, use it as a path relative to the origin
      return new URL(
        env.NEXT_PUBLIC_LANGGRAPH_BASE_URL,
        getBaseOrigin(),
      ).toString();
    }
  } else if (isMock) {
    if (typeof window !== "undefined") {
      return `${window.location.origin}/mock/api`;
    }
    return "http://localhost:3000/mock/api";
  } else {
    // LangGraph SDK requires a full URL, construct it from current origin
    if (typeof window !== "undefined") {
      return `${window.location.origin}/api/langgraph`;
    }
    // Fallback for SSR
    return "http://localhost:2026/api/langgraph";
  }
}

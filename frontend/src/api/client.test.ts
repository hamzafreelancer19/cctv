import { describe, expect, it } from "vitest";

describe("API base config", () => {
  it("defaults to /api/v1", async () => {
    const { API_BASE } = await import("../api/client");
    expect(API_BASE).toBe("/api/v1");
  });
});

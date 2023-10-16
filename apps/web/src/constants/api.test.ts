import { describe, expect, it } from "vitest";
import { API, API_PATHS, DEFAULT_SET_ID } from "./api";

describe("API constants", () => {
  it("defines canonical /v1 paths", () => {
    expect(API.WEAVE).toBe("/v1/weave");
    expect(API.SET_DETAIL("ex-001")).toBe("/v1/sets/ex-001");
    expect(API.INTELLIGENCE).toBe("/v1/intelligence");
    expect(API.ENTERPRISE_PROGRAM).toBe("/v1/enterprise/program");
    expect(API.ENTERPRISE_BUDGET).toBe("/v1/enterprise/budget");
    expect(API.QUEUE_JOBS).toBe("/v1/queue/jobs");
    expect(API.QUEUE_SCHEDULE).toBe("/v1/schedule");
    expect(API.PARSER_TOKENIZE).toBe("/v1/parser/tokenize");
    expect(API.PIPELINE_RUN).toBe("/v1/pipeline/run");
    expect(API.INGEST_SNAPSHOT).toBe("/v1/ingest/snapshot");
    expect(API.RULES_REPORT).toBe("/v1/rules/report");
    expect(API.SYNC_RECONCILE).toBe("/v1/sync/reconcile");
    expect(API.REBALANCE_ROUTE).toBe("/v1/rebalance/route");
    expect(API.AI_RECOMMEND).toBe("/v1/ai/recommend");
    expect(API.AI_SIMILAR).toBe("/v1/ai/similar");
  });

  it("exports static path list for coverage", () => {
    expect(API_PATHS.length).toBeGreaterThan(20);
    expect(API_PATHS).toContain("/v1/command-center");
  });

  it("has default exhibition set id", () => {
    expect(DEFAULT_SET_ID).toBe("ex-001");
  });
});

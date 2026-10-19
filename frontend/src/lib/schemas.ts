import { z } from "zod";

// TypeScript types vanish at runtime, so data from the network is validated here
// before the rest of the app is allowed to trust it.

export const riskLevelSchema = z.enum(["low", "guarded", "moderate", "high", "critical"]);
export const statusSchema = z.enum(["open", "investigating", "confirmed", "resolved", "false_positive"]);
export const originSchema = z.enum(["live", "simulated"]);

const factorSchema = z.object({
  label: z.string(),
  detail: z.string(),
  weight: z.number(),
});

const findingSchema = z.object({
  rule_id: z.string(),
  name: z.string(),
  strength: z.number(),
  confidence: z.number(),
  summary: z.string(),
  evidence: z.record(z.string(), z.union([z.number(), z.string()])),
  suggestion: z.string(),
});

const eventSchema = z.object({ at: z.string(), text: z.string() });

export const incidentSchema = z.object({
  id: z.number(),
  public_id: z.string(),
  title: z.string(),
  account: z.string(),
  risk_score: z.number(),
  level: riskLevelSchema,
  status: statusSchema,
  data_origin: originSchema,
  summary: z.string(),
  factors: z.array(factorSchema),
  findings: z.array(findingSchema),
  detected_at: z.string(),
  updated_at: z.string(),
  events: z.array(eventSchema),
  evidence: z.object({
    prepared: z.boolean(),
    hash: z.string().nullable(),
    anchored: z.boolean(),
    tx_hash: z.string().nullable(),
  }),
  allowed_next: z.array(statusSchema),
});

export const evidencePackageSchema = z.object({
  hash: z.string(),
  onchain_incident_id: z.string(),
  package: z.record(z.string(), z.unknown()),
});

export const incidentListSchema = z.array(incidentSchema);

export const syncResultSchema = z.object({
  created: z.number(),
  skipped: z.number(),
  data_origin: originSchema,
});

export type RiskLevel = z.infer<typeof riskLevelSchema>;
export type IncidentStatus = z.infer<typeof statusSchema>;
export type DataOrigin = z.infer<typeof originSchema>;
export type Incident = z.infer<typeof incidentSchema>;
export type SyncResult = z.infer<typeof syncResultSchema>;
export type EvidencePackage = z.infer<typeof evidencePackageSchema>;

export const modelStatusSchema = z.object({
  model: z.string(),
  trained: z.boolean(),
  reason: z.string().nullable(),
  training_rows: z.number(),
  accounts: z.number(),
  features: z.array(z.string()),
  trained_at: z.string().nullable(),
  rules: z.array(z.object({ rule_id: z.string(), name: z.string() })),
  data_origin: originSchema,
  note: z.string(),
});

export type ModelStatus = z.infer<typeof modelStatusSchema>;

export const networkSnapshotSchema = z.object({
  taken_at: z.string(),
  chain_name: z.string().nullable(),
  best_block: z.number(),
  finalized_block: z.number(),
  finality_lag: z.number(),
  window_blocks: z.number(),
  missed_slots: z.number(),
  authors: z.record(z.string(), z.number()),
  distinct_authors: z.number(),
  max_author_share: z.number().nullable(),
  block_age_s: z.number().nullable(),
  peers: z.number().nullable(),
  data_origin: originSchema,
});

export const networkHealthSchema = z.object({
  snapshot: networkSnapshotSchema,
  findings: z.array(findingSchema),
  risk_score: z.number(),
  level: riskLevelSchema,
  cached: z.boolean(),
  note: z.string(),
});

export const networkHistorySchema = z.array(
  z.object({
    taken_at: z.string(),
    best_block: z.number(),
    finality_lag: z.number(),
    missed_slots: z.number(),
    distinct_authors: z.number(),
    max_author_share: z.number().nullable(),
    block_age_s: z.number().nullable(),
    data_origin: originSchema,
  }),
);

export type NetworkHealth = z.infer<typeof networkHealthSchema>;
export type NetworkHistory = z.infer<typeof networkHistorySchema>;

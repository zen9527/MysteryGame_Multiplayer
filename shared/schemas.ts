import { z } from "zod";

// 客户端 → 服务器校验
export const joinSchema = z.object({
  type: z.literal("join"),
  player_name: z.string().min(1).max(50),
});

export const chatSchema = z.object({
  type: z.literal("chat"),
  content: z.string().min(1).max(1000),
});

export const privateChatSchema = z.object({
  type: z.literal("private_chat"),
  to_player_id: z.string(),
  content: z.string().min(1).max(1000),
});

export const accuseSchema = z.object({
  type: z.literal("accuse"),
  target_role_name: z.string(),
  reasoning: z.string().min(1).max(2000),
});

export const voteSchema = z.object({
  type: z.literal("vote"),
  target_role_name: z.string(),
  reasoning: z.string().min(1).max(2000),
});

export const advanceSchema = z.object({
  type: z.literal("request_advance"),
});

// 服务器 → 客户端新类型
export const roleCardSchema = z.object({
  type: z.literal("role_card"),
  layer: z.enum(["1", "2", "3"]),
  player_id: z.string(),
  data: z.record(z.string(), z.unknown()),
});

export const dmPrivateSchema = z.object({
  type: z.literal("dm_private"),
  from: z.literal("__dm__"),
  to: z.string(),
  content: z.string(),
});

export const clueUnlockSchema = z.object({
  type: z.literal("clue_unlock"),
  player_id: z.string(),
  clue: z.object({
    id: z.string(),
    title: z.string(),
    content: z.string(),
    content_hint: z.string(),
    is_red_herring: z.boolean(),
  }),
});

export const phaseUnlockSchema = z.object({
  type: z.literal("phase_unlock"),
  phase: z.string(),
  act: z.number(),
});

// 服务器 → 客户端类型
export type WSMessage =
  | { type: "system"; content: string }
  | { type: "event"; content: string }
  | { type: "clue_reveal"; clue: object; public: boolean; to_player_id?: string }
  | { type: "chat"; from: string; content: string; timestamp: string }
  | { type: "private_chat"; from: string; content: string; timestamp: string }
  | { type: "accusation"; from: string; target: string; reasoning: string }
  | { type: "trial_start"; accusations: object[] }
  | { type: "vote_result"; round: number; results: Record<string, number>; consensus: boolean }
  | { type: "reveal"; truth: object; player_evaluations: Record<string, string> }
  | { type: "game_over"; result: "correct" | "wrong" | "time_out" }
  | { type: "player_joined"; player_name: string; role_name: string }
  | { type: "player_left"; player_name: string }
  | { type: "role_assigned"; role: object; secret: object }
  | { type: "role_card"; layer: "1" | "2" | "3"; player_id: string; data: Record<string, unknown> }
  | { type: "dm_private"; from: "__dm__"; to: string; content: string }
  | { type: "clue_unlock"; player_id: string; clue: { id: string; title: string; content: string; content_hint: string; is_red_herring: boolean } }
  | { type: "phase_unlock"; phase: string; act: number };

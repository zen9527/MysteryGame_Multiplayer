import { z } from "zod";

// Chat Message Schema
export const chatMessageSchema = z.object({
  message_id: z.string(),
  content: z.string().min(1).max(2000),
  player_id: z.string(),
  role_name: z.string(),
  timestamp: z.string().datetime(),
  from_player_name: z.string()
});
export type ChatMessage = z.infer<typeof chatMessageSchema>;

// Clue Schema
export const clueSchema = z.object({
  id: z.string(),
  title: z.string(),
  content: z.string(),
  unlock_phase: z.enum(["act1", "act2"]),
  clue_type: z.enum(["public", "private"]),
  related_role_id: z.string().optional()
});
export type Clue = z.infer<typeof clueSchema>;

// Role Card Schema
export const roleCardSchema = z.object({
  role_id: z.string(),
  role_name: z.string(),
  player_id: z.string(),
  layer: z.number().int().min(1).max(3),
  content: z.string(),
  secrets: z.array(z.string()).optional()
});
export type RoleCard = z.infer<typeof roleCardSchema>;

// Player Schema
export const playerSchema = z.object({
  player_id: z.string(),
  role_id: z.string(),
  role_name: z.string(),
  is_admin: z.boolean()
});
export type Player = z.infer<typeof playerSchema>;

// Game State Schema
export const gameStateSchema = z.object({
  room_id: z.string(),
  phase: z.enum(["waiting", "playing", "ended"]),
  act: z.number().int().min(1),
  players: z.array(playerSchema),
  current_event: z.any().optional(),
  clues_unlocked: z.array(z.string())
});
export type GameState = z.infer<typeof gameStateSchema>;

// Phase Unlock Schema
export const phaseUnlockSchema = z.object({
  new_act: z.number().int().min(1),
  distributed_role_cards: z.array(roleCardSchema).optional(),
  distributed_clues: z.array(clueSchema).optional()
});
export type PhaseUnlock = z.infer<typeof phaseUnlockSchema>;

// Export all schemas for easy import
export const wsSchemas = {
  chatMessage: chatMessageSchema,
  clue: clueSchema,
  roleCard: roleCardSchema,
  player: playerSchema,
  gameState: gameStateSchema,
  phaseUnlock: phaseUnlockSchema
};

export default wsSchemas;

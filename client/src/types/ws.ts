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

export type ClientMessage =
  | { type: "join"; player_name: string }
  | { type: "role_read"; player_id: string }
  | { type: "chat"; content: string }
  | { type: "private_chat"; to_player_id: string; content: string }
  | { type: "accuse"; target_role_name: string; reasoning: string }
  | { type: "vote"; target_role_name: string; reasoning: string }
  | { type: "request_advance" };

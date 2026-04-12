export type AIAgentStatus = "draft" | "active" | "paused" | "archived";
export type PromptType = "system_instruction" | "inbox_reply" | "comment_reply" | "post_generation";
export type KnowledgeSourceStatus = "draft" | "ready" | "processing" | "archived";
export type KnowledgeSourceType = "file" | "url" | "text";

export type AIAgent = {
  id: number;
  account_id: number;
  platform_connection_id: number | null;
  name: string;
  business_type: string | null;
  status: AIAgentStatus;
  settings_json: Record<string, unknown>;
  behavior_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type AIAgentOverview = AIAgent & {
  prompt_count: number;
  knowledge_source_count: number;
  faq_count: number;
};

export type AIPrompt = {
  id: number;
  account_id: number;
  ai_agent_id: number | null;
  platform_connection_id: number | null;
  prompt_type: PromptType;
  title: string;
  content: string;
  version: number;
  is_active: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type PromptResolution = {
  prompt_type: PromptType;
  source_scope: string;
  prompt: AIPrompt | null;
};

export type AIKnowledgeSource = {
  id: number;
  account_id: number;
  ai_agent_id: number | null;
  title: string;
  source_type: KnowledgeSourceType;
  status: KnowledgeSourceStatus;
  description: string | null;
  content_text: string | null;
  file_name: string | null;
  file_size: number | null;
  mime_type: string | null;
  storage_key: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type FAQKnowledge = {
  id: number;
  account_id: number;
  ai_agent_id: number | null;
  question: string;
  answer: string;
  tags_json: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AIGenerationResponse = {
  content: string;
  requires_approval: boolean;
  provider: string;
  model_name: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  prompt_id: number | null;
  prompt_scope: string;
  ai_agent_id: number | null;
  platform_connection_id: number | null;
  draft_reference_type: string | null;
  draft_object_id: number | null;
};

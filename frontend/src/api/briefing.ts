import api from './client';

export interface BriefingData {
  status: string;
  date: string;
  content: string;
  article_ids: number[];
  ai_verified?: boolean;
  curated?: boolean;
}

export interface BriefingParams {
  date?: string;
  limit?: number;
  sources?: string[];
}

/**
 * Get today's briefing
 */
export const getTodayBriefing = async (): Promise<BriefingData> => {
  return api.get<BriefingData>('/briefings/today');
};

/**
 * Generate a new briefing
 */
export const generateBriefing = async (params?: BriefingParams): Promise<BriefingData> => {
  return api.post<BriefingData>('/briefings/generate', params);
};

/**
 * Get briefing by date
 */
export const getBriefingByDate = async (date: string): Promise<BriefingData> => {
  return api.get<BriefingData>(`/briefings/date/${date}`);
};

/**
 * Get recent briefings
 */
export const getRecentBriefings = async (limit = 7): Promise<BriefingData[]> => {
  return api.get<BriefingData[]>(`/briefings/recent?limit=${limit}`);
};
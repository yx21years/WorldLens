import api from './client';

export interface AIInsight {
  id: number;
  type: 'sentiment' | 'trend' | 'event' | 'alert';
  title: string;
  description: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'stable';
  confidence: number;
  metadata: {
    global_sentiment?: number;
    active_regions?: number;
    news_flow_rate?: number;
    ai_accuracy?: number;
    categories?: Array<{
      name: string;
      count: number;
      trend: 'up' | 'down' | 'stable';
    }>;
    regions?: Array<{
      name: string;
      activity: number;
      sentiment: 'positive' | 'neutral' | 'negative';
    }>;
  };
}

export interface AnalysisParams {
  timeframe?: '24h' | '7d' | '30d';
  categories?: string[];
  regions?: string[];
}

export interface AnalysisResponse {
  insights: AIInsight[];
  summary: string;
  last_updated: string;
}

/**
 * Get AI dashboard insights
 */
export const getAIInsights = async (params: AnalysisParams = {}): Promise<AnalysisResponse> => {
  const queryParams = new URLSearchParams();

  if (params.timeframe) queryParams.append('timeframe', params.timeframe);
  if (params.categories?.length) queryParams.append('categories', params.categories.join(','));
  if (params.regions?.length) queryParams.append('regions', params.regions.join(','));

  const queryString = queryParams.toString();
  const endpoint = queryString ? `/analysis/insights?${queryString}` : '/analysis/insights';

  return api.get<AnalysisResponse>(endpoint);
};

/**
 * Get global sentiment analysis
 */
export const getGlobalSentiment = async (): Promise<{
  overall: number;
  by_region: Array<{
    region: string;
    sentiment: number;
    articles_count: number;
  }>;
  by_category: Array<{
    category: string;
    sentiment: number;
    articles_count: number;
  }>;
}> => {
  return api.get('/analysis/sentiment/global');
};

/**
 * Get news flow metrics
 */
export const getNewsFlowMetrics = async (): Promise<{
  articles_per_minute: number;
  peak_hours: number[];
  sources_distribution: Array<{
    source: string;
    percentage: number;
  }>;
}> => {
  return api.get('/analysis/flow/metrics');
};

/**
 * Get trending topics
 */
export const getTrendingTopics = async (limit = 10): Promise<Array<{
  topic: string;
  mentions: number;
  sentiment: number;
  trend: 'rising' | 'stable' | 'falling';
}>> => {
  return api.get(`/analysis/trending/topics?limit=${limit}`);
};
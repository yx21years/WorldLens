import api from './client';

export interface Article {
  id: number;
  title: string;
  content: string;
  summary: string;
  url: string;
  published_at: string;
  source: string;
  author?: string;
  category: string;
  region: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  importance_score: number;
  topics: string[];
  ai_analysis?: {
    summary: string;
    sentiment: string;
    key_points: string[];
    entities: Array<{
      name: string;
      type: string;
      confidence: number;
    }>;
  };
}

export interface ArticleParams {
  limit?: number;
  offset?: number;
  category?: string;
  region?: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  date_from?: string;
  date_to?: string;
  sources?: string[];
  q?: string; // search query
}

export interface ArticlesResponse {
  articles: Article[];
  total: number;
  has_more: boolean;
  page?: number;
}

/**
 * Get articles with filtering options
 */
export const getArticles = async (params: ArticleParams = {}): Promise<ArticlesResponse> => {
  const queryParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) {
      queryParams.append(key, String(value));
    }
  });

  const queryString = queryParams.toString();
  const endpoint = queryString ? `/articles?${queryString}` : '/articles';

  return api.get<ArticlesResponse>(endpoint);
};

/**
 * Get article by ID
 */
export const getArticleById = async (id: number): Promise<Article> => {
  return api.get<Article>(`/articles/${id}`);
};

/**
 * Get trending articles
 */
export const getTrendingArticles = async (limit = 10): Promise<Article[]> => {
  return api.get<Article[]>(`/articles/trending?limit=${limit}`);
};

/**
 * Get articles by region
 */
export const getArticlesByRegion = async (region: string, limit = 20): Promise<Article[]> => {
  return api.get<Article[]>(`/articles/region/${region}?limit=${limit}`);
};

/**
 * Get articles by category
 */
export const getArticlesByCategory = async (category: string, limit = 20): Promise<Article[]> => {
  return api.get<Article[]>(`/articles/category/${category}?limit=${limit}`);
};
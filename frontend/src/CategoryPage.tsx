import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, TrendingUp, Filter, Search } from 'lucide-react';

// ============================================================
// TYPES
// ============================================================
interface Article {
  id: number;
  title: string;
  url: string;
  image_url?: string | null;
  raw_content?: string;
  published_at?: string | null;
  status?: string;
  source_id?: number;
  source_name?: string;
  source?: { id: number; name: string };
  totalScore?: number;
  analysis?: {
    summary: string;
    importance: number;
    sentiment?: 'positive' | 'negative' | 'neutral';
    category?: string;
    trend_level?: string;
  };
}

// ============================================================
// CATEGORY INFO
// ============================================================
const CATEGORY_INFO: Record<string, { nameCN: string; nameEN: string }> = {
  tech: { nameCN: '科技', nameEN: 'Technology' },
  war: { nameCN: '冲突', nameEN: 'Conflict' },
  life: { nameCN: '人文', nameEN: 'Humanity' },
  leisure: { nameCN: '生活', nameEN: 'Lifestyle' },
};

// ============================================================
// HELPERS
// ============================================================
const formatDate = (dateStr: string | null | undefined): string => {
  if (!dateStr) return '日期未知';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return '日期未知';
    return date.toISOString().slice(0, 10);
  } catch {
    return '日期未知';
  }
};

// ============================================================
// COMPONENTS
// ============================================================
const ImportanceBadge: React.FC<{ score: number }> = ({ score }) => {
  const color = score >= 9 ? '#ef4444' : score >= 7 ? '#f59e0b' : '#10b981';
  return (
    <span
      className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-semibold"
      style={{ background: `${color}20`, color, border: `1px solid ${color}40` }}
    >
      {score}/10
    </span>
  );
};

const SentimentDot: React.FC<{ sentiment?: 'positive' | 'negative' | 'neutral' }> = ({ sentiment }) => {
  const color = sentiment === 'positive' ? '#10b981' : sentiment === 'negative' ? '#ef4444' : '#64748b';
  return (
    <span
      className="inline-block w-2 h-2 rounded-full"
      style={{ background: color, boxShadow: `0 0 8px ${color}80` }}
      title={sentiment || 'neutral'}
    />
  );
};

const ArticleCard: React.FC<{ article: Article; index: number }> = ({ article, index }) => {
  const [loaded, setLoaded] = useState(false);

  const imageUrl = article.image_url || `https://picsum.photos/seed/${article.id}/400/240`;
  const summary = article.analysis?.summary
    || article.raw_content?.slice(0, 120) + (article.raw_content?.length > 120 ? '...' : '')
    || '暂无摘要';
  const sourceName = article.source_name || article.source?.name || '未知来源';
  const importance = article.analysis?.importance ?? 5;
  const sentiment = article.analysis?.sentiment || 'neutral';
  const publishedDate = formatDate(article.published_at);

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.5 }}
      whileHover={{ y: -4 }}
      className="overflow-hidden group h-full"
      style={{
        background: 'rgba(255, 255, 255, 0.15)',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.25)',
        boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
      }}
    >
      {/* Image */}
      <div className="relative h-44 overflow-hidden">
        {!loaded && (
          <div
            className="absolute inset-0 animate-pulse"
            style={{ background: 'rgba(255,255,255,0.04)' }}
          />
        )}
        <img
          src={imageUrl}
          alt={article.title}
          loading="lazy"
          onLoad={() => setLoaded(true)}
          className={`w-full h-full object-cover transition-transform duration-500 group-hover:scale-105 ${loaded ? 'opacity-100' : 'opacity-0'}`}
        />
        <div
          className="absolute inset-0"
          style={{ background: 'linear-gradient(to top, rgba(0,0,0,0.3) 0%, transparent 40%)' }}
        />
        <div className="absolute top-3 right-3">
          <ImportanceBadge score={importance} />
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Meta */}
        <div className="flex items-center gap-2 mb-2">
          <SentimentDot sentiment={sentiment} />
          <span className="text-xs" style={{ color: 'rgba(0, 0, 0, 0.6)' }}>
            {sourceName} · {publishedDate}
          </span>
        </div>

        {/* Title - clickable link */}
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold leading-snug mb-2 line-clamp-2 hover:text-blue-600 transition-colors block"
          style={{
            fontSize: '1.7rem',
            lineHeight: '1.75rem',
            color: 'rgba(0, 0, 0, 0.85)',
          }}
        >
          {article.title}
        </a>

        {/* Summary */}
        <p
          className="text-xs leading-relaxed line-clamp-2"
          style={{
            color: 'rgba(0, 0, 0, 0.6)',
          }}
        >
          {summary}
        </p>
      </div>
    </motion.div>
  );
};

// ============================================================
// PAGE
// ============================================================
const CategoryPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);

  const categoryId = id || 'tech';

  // ===== 自定义滑动条 =====
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const thumbRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [thumbHeight, setThumbHeight] = useState(0);
  const [thumbTop, setThumbTop] = useState(0);

  const updateThumb = () => {
    if (!scrollContainerRef.current || !trackRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    if (scrollHeight <= clientHeight) {
      setThumbHeight(0);
      return;
    }
    const trackHeight = trackRef.current.clientHeight;
    const thumbHeightRatio = clientHeight / scrollHeight;
    setThumbHeight(Math.max(30, thumbHeightRatio * trackHeight));
    const maxScrollTop = scrollHeight - clientHeight;
    const ratio = scrollTop / maxScrollTop;
    setThumbTop(ratio * (trackHeight - (Math.max(30, thumbHeightRatio * trackHeight))));
  };

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;
    container.addEventListener('scroll', updateThumb);
    setTimeout(updateThumb, 100);
    return () => container.removeEventListener('scroll', updateThumb);
  }, [articles, loading]);

  const handleDragStart = (e: React.MouseEvent | React.TouchEvent) => {
    setIsDragging(true);
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'grabbing';
  };

  const handleDragMove = (e: React.MouseEvent | React.TouchEvent) => {
    if (!isDragging || !scrollContainerRef.current || !trackRef.current) return;
    const clientY = 'touches' in e ? e.touches[0].clientY : (e as React.MouseEvent).clientY;
    const trackRect = trackRef.current.getBoundingClientRect();
    const relativeY = clientY - trackRect.top;
    const trackHeight = trackRef.current.clientHeight;
    const ratio = Math.max(0, Math.min(1, relativeY / trackHeight));
    const { scrollHeight, clientHeight } = scrollContainerRef.current;
    const maxScrollTop = scrollHeight - clientHeight;
    scrollContainerRef.current.scrollTop = ratio * maxScrollTop;
  };

  const handleDragEnd = () => {
    if (isDragging) {
      setIsDragging(false);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    }
  };

  useEffect(() => {
    if (isDragging) {
      const onMove = (e: MouseEvent | TouchEvent) => handleDragMove(e as any);
      const onEnd = () => handleDragEnd();
      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseup', onEnd);
      window.addEventListener('touchmove', onMove);
      window.addEventListener('touchend', onEnd);
      return () => {
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onEnd);
        window.removeEventListener('touchmove', onMove);
        window.removeEventListener('touchend', onEnd);
      };
    }
  }, [isDragging]);

  // ============================================================
  // ⭐ 核心逻辑：评分函数
  // ============================================================
  const scoreArticles = (articles: Article[]): Article[] => {
    const now = new Date();
    const keywords = ['突发', '紧急', '重大', '宣布', '发布', '推出', '首次', '创纪录', '突破', '警告', '危机', '冲突', '协议', '达成', '签署'];

    return articles.map(article => {
      let totalScore = 0;

      // 1. 来源权重
      const sourceWeightMap: Record<string, number> = {
        'BBC': 10,
        'Reuters': 9,
        'CNN': 8,
        'TechCrunch': 7,
        'The Verge': 7,
        'OpenAI Blog': 6,
        '知乎': 6,
      };
      const sourceName = article.source_name || article.source?.name || '其他';
      totalScore += sourceWeightMap[sourceName] || 5;

      // 2. 关键词加分
      const lowerTitle = article.title.toLowerCase();
      let keywordBonus = 0;
      for (const keyword of keywords) {
        if (lowerTitle.includes(keyword.toLowerCase())) {
          keywordBonus += 2;
        }
      }
      totalScore += keywordBonus;

      // 3. 新鲜度加分
      if (article.published_at || article.created_at) {
        const articleDate = new Date(article.published_at || article.created_at);
        const hoursDiff = Math.abs(now.getTime() - articleDate.getTime()) / (1000 * 60 * 60);
        if (hoursDiff <= 24) totalScore += 2;
        else if (hoursDiff <= 48) totalScore += 1;
      }

      // 4. 长度加分
      const summary = article.analysis?.summary || article.raw_content || '';
      if (summary.length >= 100 && summary.length <= 500) totalScore += 2;

      return { ...article, totalScore };
    });
  };

  // ============================================================
  // ⭐ 核心逻辑：分组筛选
  // 规则：每个源 ≤5 篇全部展示，>5 篇取前 10，每个源至少展示 1 篇
  // ============================================================
  const filterTopArticles = (articles: Article[]): Article[] => {
    // 1. 按 source_id 分组
    const grouped = articles.reduce((acc, article) => {
      const sourceId = article.source_id || 0;
      if (!acc[sourceId]) acc[sourceId] = [];
      acc[sourceId].push(article);
      return acc;
    }, {} as Record<number, Article[]>);

    // 2. 对每个源应用展示规则
    const topArticles = Object.values(grouped).map(group => {
      const sorted = group.sort((a, b) => (b.totalScore || 0) - (a.totalScore || 0));

      // 规则：
      // - 文章数 ≤ 5 篇 → 全部展示
      // - 文章数 > 5 篇 → 取前 10 篇
      if (sorted.length <= 5) {
        return sorted;
      } else {
        return sorted.slice(0, 10);
      }
    }).flat();

    // 3. 合并后按评分降序展示
    return topArticles.sort((a, b) => (b.totalScore || 0) - (a.totalScore || 0));
  };

  // ============================================================
  // ⭐ 核心逻辑：一次性拉取该分类下的所有文章
  // ============================================================
  useEffect(() => {
    const fetchAllArticles = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/v1/articles?category=${categoryId}&limit=5000`);
        const data = await res.json();
        const items = data.data || [];

        const scored = scoreArticles(items);
        const filtered = filterTopArticles(scored);
        setArticles(filtered);
      } catch (err) {
        console.error('Failed to fetch articles:', err);
        setArticles([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAllArticles();
  }, [categoryId]);

  // 搜索过滤
  const filtered = articles.filter(
    (a) =>
      a.title.toLowerCase().includes(search.toLowerCase()) ||
      (a.analysis?.summary && a.analysis.summary.toLowerCase().includes(search.toLowerCase()))
  );

  // 对过滤后的文章重新评分和分组
  const scoredForDisplay = scoreArticles(filtered);
  const finalArticles = filterTopArticles(scoredForDisplay);

  const info = CATEGORY_INFO[categoryId] || { nameCN: '', nameEN: '' };

  return (
    <>
      {/* 视频背景 */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          zIndex: -10,
          overflow: 'hidden',
          pointerEvents: 'none',
        }}
      >
        <video
          autoPlay
          muted
          loop
          playsInline
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        >
          <source src="/assets/video5.mp4" type="video/mp4" />
        </video>
      </div>

      {/* 黑色渐变遮罩 */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '60vh',
          zIndex: -5,
          pointerEvents: 'none',
          background: 'linear-gradient(180deg, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0) 100%)',
        }}
      />

      {/* 内容层 */}
      <div className="relative z-10 min-h-screen font-sans" style={{ color: '#f1f5f9' }}>
        <div className="relative z-10 w-full max-w-screen-2xl mx-auto px-6 py-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex items-center justify-between mb-6"
          >
            <button
              onClick={() => navigate(-1)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm transition-all duration-200 hover:bg-white/20"
              style={{
                color: 'rgba(0,0,0,0.8)',
                border: '1px solid rgba(255,255,255,0.5)',
                background: 'rgba(255,255,255,0.2)',
              }}
            >
              <ArrowLeft size={16} />
              <span>返回</span>
            </button>

            <div className="text-center">
              <h1
                className="text-4xl font-serif italic"
                style={{
                  color: 'rgba(0,0,0,0.9)',
                  textShadow: '0 2px 20px rgba(255,255,255,0.4)',
                }}
              >
                {info.nameCN}
              </h1>
              <p
                className="text-sm tracking-[0.2em] uppercase mt-1"
                style={{
                  color: 'rgba(0,0,0,0.7)',
                }}
              >
                {info.nameEN}
              </p>
            </div>

            <div className="w-24" />
          </motion.div>

          {/* Search & Filter Bar */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="flex items-center gap-3 mb-6 flex-wrap"
          >
            <div
              className="flex-1 min-w-[220px] flex items-center gap-3 px-4 py-2.5 rounded-full"
              style={{
                background: 'rgba(255,255,255,0.2)',
                border: '1px solid rgba(255,255,255,0.3)',
              }}
            >
              <Search size={16} style={{ color: 'rgba(0,0,0,0.6)' }} />
              <input
                type="text"
                placeholder="搜索文章..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="bg-transparent text-sm outline-none flex-1"
                style={{ color: 'rgba(0,0,0,0.9)' }}
              />
            </div>
            <button
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full text-sm transition-all"
              style={{
                background: 'rgba(255,255,255,0.2)',
                border: '1px solid rgba(255,255,255,0.3)',
                color: 'rgba(0,0,0,0.8)',
              }}
            >
              <Filter size={14} />
              筛选
            </button>
            <span className="text-xs" style={{ color: 'rgba(0,0,0,0.5)' }}>
              {finalArticles.length} 篇文章
            </span>
          </motion.div>

          {/* 文章列表 */}
          {loading ? (
            <div className="grid grid-cols-1 gap-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="rounded-2xl overflow-hidden"
                  style={{
                    background: 'rgba(255,255,255,0.1)',
                    height: 280,
                    border: '1px solid rgba(255,255,255,0.2)',
                  }}
                >
                  <div className="h-40 animate-pulse" style={{ background: 'rgba(255,255,255,0.1)' }} />
                  <div className="p-4 space-y-2">
                    <div className="h-3 rounded-full animate-pulse w-1/3" style={{ background: 'rgba(255,255,255,0.2)' }} />
                    <div className="h-4 rounded-full animate-pulse w-full" style={{ background: 'rgba(255,255,255,0.2)' }} />
                    <div className="h-4 rounded-full animate-pulse w-2/3" style={{ background: 'rgba(255,255,255,0.2)' }} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="relative w-full">
              <div
                ref={scrollContainerRef}
                className="grid grid-cols-1 gap-5 pr-6 max-h-[70vh] overflow-y-auto overflow-x-hidden scrollbar-hide"
              >
                <AnimatePresence mode="wait">
                  <motion.div
                    key={search}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="contents"
                  >
                    {finalArticles.map((article, i) => (
                      <ArticleCard key={article.id} article={article} index={i} />
                    ))}
                  </motion.div>
                </AnimatePresence>
              </div>

              {/* 自定义滚动条 */}
              <div
                ref={trackRef}
                className="absolute right-0 top-0 w-1.5 h-full bg-white/10 rounded-full cursor-pointer hover:bg-white/20 transition-colors"
                onMouseDown={handleDragStart}
                onTouchStart={handleDragStart}
              >
                {thumbHeight > 0 && (
                  <div
                    ref={thumbRef}
                    className="absolute left-1/2 -translate-x-1/2 w-3 rounded-full cursor-grab active:cursor-grabbing transition-all duration-300 hover:scale-110"
                    style={{
                      height: thumbHeight,
                      top: thumbTop,
                      background: 'linear-gradient(to bottom, #7c3aed, #3b82f6)',
                      boxShadow: '0 0 15px rgba(124, 58, 237, 0.6), inset 0 1px 0 rgba(255,255,255,0.4)',
                      backdropFilter: 'blur(4px)',
                    }}
                    onMouseDown={handleDragStart}
                    onTouchStart={handleDragStart}
                  />
                )}
              </div>
            </div>
          )}

          {/* Empty state */}
          {!loading && finalArticles.length === 0 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-20">
              <p style={{ color: 'rgba(0,0,0,0.4)' }}>未找到匹配的文章</p>
            </motion.div>
          )}
        </div>
      </div>
    </>
  );
};

export default CategoryPage;
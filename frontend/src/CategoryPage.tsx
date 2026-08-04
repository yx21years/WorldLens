import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, TrendingUp, Filter, Search } from 'lucide-react';


// ============================================================
// TYPES
// ============================================================
interface Article {
  id: number;
  title: string;
  summary: string;
  source: string;
  date: string;
  importance: number;
  category: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  imageUrl: string;
}

// ============================================================
// MOCK DATA
// ============================================================
const MOCK_ARTICLES: Record<string, Article[]> = {
  tech: Array.from({ length: 10 }, (_, i) => ({
    id: i + 1,
    title: [
      'OpenAI 发布 GPT-5，推理能力突破新纪录',
      '量子计算机实现 1000 量子比特突破',
      'Apple 推出空间计算平台 Vision Pro 2.0',
      'SpaceX 星舰完成首次商业载荷发射',
      'NVIDIA 发布下一代 AI 芯片 Blackwell Ultra',
      '欧盟通过全球首部全面 AI 监管法案',
      '特斯拉 Optimus 机器人实现自主工厂作业',
      '谷歌量子霸权实验再次刷新纪录',
      '脑机接口技术实现瘫痪患者思维控制',
      '全球首款固态电池电动车量产交付',
    ][i],
    summary: '全球科技巨头在人工智能、量子计算和航天领域持续突破，重塑人类对未来的想象边界。专家指出这些技术将在未来十年内深刻改变全球经济格局。',
    source: i % 3 === 0 ? 'Reuters' : i % 3 === 1 ? 'Bloomberg' : 'TechCrunch',
    date: '2026-08-01',
    importance: Math.floor(Math.random() * 4) + 6,
    category: '科技',
    sentiment: ['positive', 'neutral', 'negative'][i % 3] as Article['sentiment'],
    imageUrl: `https://picsum.photos/seed/tech${i}/400/240`,
  })),
  war: Array.from({ length: 10 }, (_, i) => ({
    id: i + 11,
    title: [
      '北约峰会就东欧防御计划达成新共识',
      '中东局势急剧升级，多国撤侨行动启动',
      '太平洋岛国论坛讨论安全合作新框架',
      '联合国安理会就地区冲突举行紧急会议',
      '全球军费开支创历史新高，达 2.4 万亿美元',
      '北极航道军事化引发国际关注',
      '非洲萨赫勒地区安全局势持续恶化',
      '网络安全成为现代战争新前沿阵地',
      '国际刑事法院对 war crimes 展开新调查',
      '全球核武控谈判陷入僵局',
    ][i],
    summary: '地缘政治紧张局势持续升温，多国加强军事部署与防御合作，国际社会呼吁通过外交途径缓解冲突升级风险。',
    source: i % 2 === 0 ? 'Al Jazeera' : 'BBC',
    date: '2026-07-31',
    importance: Math.floor(Math.random() * 3) + 7,
    category: '冲突',
    sentiment: 'negative' as const,
    imageUrl: `https://picsum.photos/seed/war${i}/400/240`,
  })),
  life: Array.from({ length: 10 }, (_, i) => ({
    id: i + 21,
    title: [
      '全球老龄化加速，多国出台生育激励政策',
      'WHO 发布新指南：应对气候变化健康风险',
      '远程工作重塑全球城市人口流动格局',
      '全球心理健康危机引发国际社会关注',
      '教育公平成为联合国可持续发展新焦点',
      '全球公共卫生系统面临新一轮考验',
      '数字鸿沟加剧全球不平等现象',
      '原住民权益保护获国际法新进展',
      '全球粮食安全报告警告未来挑战',
      '难民危机推动国际社会人权对话',
    ][i],
    summary: '人类社会面临人口结构转型、气候变化和公共卫生等多重挑战，国际社会正在探索新的合作模式应对这些复杂问题。',
    source: i % 2 === 0 ? 'UN News' : 'The Guardian',
    date: '2026-07-30',
    importance: Math.floor(Math.random() * 3) + 6,
    category: '人文',
    sentiment: ['positive', 'neutral', 'negative'][i % 3] as Article['sentiment'],
    imageUrl: `https://picsum.photos/seed/life${i}/400/240`,
  })),
  leisure: Array.from({ length: 10 }, (_, i) => ({
    id: i + 31,
    title: [
      '威尼斯双年展引发全球艺术界关注',
      '奥运遗产效应推动主办城市体育发展',
      'AI 生成艺术在拍卖行创下新高',
      '全球游戏产业收入首次突破 2000 亿美元',
      '时尚周展现可持续设计新趋势',
      '虚拟现实演唱会开启娱乐新纪元',
      '全球电影票房回暖，亚太市场领涨',
      '独立游戏开发者获国际大奖认可',
      '博物馆数字化转型加速推进',
      '世界音乐节吸引百万观众现场参与',
    ][i],
    summary: '文化艺术领域呈现多元化发展趋势，科技与艺术的融合为创作者和观众带来全新体验，全球创意经济持续繁荣。',
    source: i % 2 === 0 ? 'Artforum' : 'Variety',
    date: '2026-07-29',
    importance: Math.floor(Math.random() * 3) + 5,
    category: '生活',
    sentiment: ['positive', 'positive', 'neutral'][i % 3] as Article['sentiment'],
    imageUrl: `https://picsum.photos/seed/leisure${i}/400/240`,
  })),
};

const CATEGORY_INFO: Record<string, { nameCN: string; nameEN: string }> = {
  tech: { nameCN: '科技', nameEN: 'Technology' },
  war: { nameCN: '冲突', nameEN: 'Conflict' },
  life: { nameCN: '人文', nameEN: 'Humanity' },
  leisure: { nameCN: '生活', nameEN: 'Lifestyle' },
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

const SentimentDot: React.FC<{ sentiment: Article['sentiment'] }> = ({ sentiment }) => {
  const color = sentiment === 'positive' ? '#10b981' : sentiment === 'negative' ? '#ef4444' : '#64748b';
  return (
    <span
      className="inline-block w-2 h-2 rounded-full"
      style={{ background: color, boxShadow: `0 0 8px ${color}80` }}
      title={sentiment}
    />
  );
};

const ArticleCard: React.FC<{ article: Article; index: number }> = ({ article, index }) => {
  const [loaded, setLoaded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.5 }}
      whileHover={{ y: -4 }}
      className="glass-card cursor-pointer overflow-hidden group"
      style={{ transitionDelay: `${index * 30}ms` }}
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
          src={article.imageUrl}
          alt={article.title}
          loading="lazy"
          onLoad={() => setLoaded(true)}
          className={`w-full h-full object-cover transition-transform duration-500 group-hover:scale-105 ${loaded ? 'opacity-100' : 'opacity-0'}`}
        />
        {/* Overlay gradient */}
        <div
          className="absolute inset-0"
          style={{ background: 'linear-gradient(to top, rgba(10,10,15,0.9) 0%, transparent 50%)' }}
        />
        {/* Importance badge */}
        <div className="absolute top-3 right-3">
          <ImportanceBadge score={article.importance} />
        </div>
      </div>

      {/* Content */}
      <div className="p-5">
        {/* Meta */}
        <div className="flex items-center gap-2 mb-3">
          <SentimentDot sentiment={article.sentiment} />
          <span className="text-xs" style={{ color: 'rgba(255,255,255,0.40)' }}>
            {article.source} · {article.date}
          </span>
        </div>

        {/* Title */}
        <h3
          className="text-base font-semibold leading-snug mb-2 line-clamp-2"
          style={{ color: 'rgba(255,255,255,0.90)' }}
        >
          {article.title}
        </h3>

        {/* Summary */}
        <p
          className="text-sm leading-relaxed line-clamp-3"
          style={{ color: 'rgba(255,255,255,0.50)' }}
        >
          {article.summary}
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

  useEffect(() => {
    const data = MOCK_ARTICLES[id || 'tech'] || [];
    const timer = setTimeout(() => {
      setArticles(data);
      setLoading(false);
    }, 600);
    return () => clearTimeout(timer);
  }, [id]);

  const filtered = articles.filter(
    (a) =>
      a.title.toLowerCase().includes(search.toLowerCase()) ||
      a.summary.toLowerCase().includes(search.toLowerCase())
  );

  const info = CATEGORY_INFO[id || 'tech'] || { nameCN: '', nameEN: '' };

  return (
    <div
      className="min-h-screen font-sans"
      style={{ background: '#0a0a0f', color: '#f1f5f9' }}
    >
      {/* Ambient glow */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div
          className="absolute w-[600px] h-[600px] rounded-full opacity-20"
          style={{
            background: 'radial-gradient(circle, rgba(124,58,237,0.5) 0%, transparent 70%)',
            top: '10%',
            left: '-10%',
            filter: 'blur(80px)',
          }}
        />
      </div>

      {/* Noise */}
      <div
        className="fixed inset-0 pointer-events-none z-[9999] opacity-[0.025]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          backgroundSize: '512px 512px',
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex items-center justify-between mb-10"
        >
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm transition-all duration-200 hover:bg-white/5"
            style={{ color: 'rgba(255,255,255,0.60)', border: '1px solid rgba(255,255,255,0.08)' }}
          >
            <ArrowLeft size={16} />
            <span>返回</span>
          </button>

          <div className="text-center">
            <h1
              className="text-4xl font-serif italic"
              style={{ color: 'rgba(255,255,255,0.95)' }}
            >
              {info.nameCN}
            </h1>
            <p
              className="text-sm tracking-[0.2em] uppercase mt-1"
              style={{ color: 'rgba(255,255,255,0.35)' }}
            >
              {info.nameEN}
            </p>
          </div>

          <div className="w-24" /> {/* spacer for centering */}
        </motion.div>

        {/* Search & Filter Bar */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="flex items-center gap-3 mb-8 flex-wrap"
        >
          <div
            className="flex-1 min-w-[220px] flex items-center gap-3 px-4 py-2.5 rounded-full"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.08)',
              backdropFilter: 'blur(12px)',
            }}
          >
            <Search size={16} style={{ color: 'rgba(255,255,255,0.35)' }} />
            <input
              type="text"
              placeholder="搜索文章..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-transparent text-sm outline-none flex-1"
              style={{ color: '#f1f5f9' }}
            />
          </div>
          <button
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full text-sm transition-all"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.08)',
              color: 'rgba(255,255,255,0.60)',
            }}
          >
            <Filter size={14} />
            筛选
          </button>
          <span
            className="text-xs"
            style={{ color: 'rgba(255,255,255,0.30)' }}
          >
            {filtered.length} 篇文章
          </span>
        </motion.div>

        {/* Article Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="rounded-2xl overflow-hidden"
                style={{ background: 'rgba(255,255,255,0.03)', height: 320 }}
              >
                <div
                  className="h-44 animate-pulse"
                  style={{ background: 'rgba(255,255,255,0.04)' }}
                />
                <div className="p-5 space-y-3">
                  <div
                    className="h-3 rounded-full animate-pulse w-1/3"
                    style={{ background: 'rgba(255,255,255,0.06)' }}
                  />
                  <div
                    className="h-4 rounded-full animate-pulse w-full"
                    style={{ background: 'rgba(255,255,255,0.08)' }}
                  />
                  <div
                    className="h-4 rounded-full animate-pulse w-2/3"
                    style={{ background: 'rgba(255,255,255,0.06)' }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={search}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5"
            >
              {filtered.map((article, i) => (
                <ArticleCard key={article.id} article={article} index={i} />
              ))}
            </motion.div>
          </AnimatePresence>
        )}

        {/* Empty state */}
        {!loading && filtered.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20"
          >
            <p style={{ color: 'rgba(255,255,255,0.30)' }}>
              未找到匹配的文章
            </p>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default CategoryPage;

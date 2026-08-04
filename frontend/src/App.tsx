import React, { useState, useRef, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import CategoryPage from './CategoryPage';

// ============================================================
// DATA
// ============================================================
const CATEGORIES = [
  {
    id: 'tech',
    nameCN: '科技',
    nameEN: 'Technology',
    videoUrl: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260702_081127_0992a171-d3c6-4978-8213-0ec5df8b6d63.mp4',
  },
  {
    id: 'war',
    nameCN: '战争',
    nameEN: 'War',
    videoUrl: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260702_092026_dd05b805-ea0f-40b2-8c52-332b88502592.mp4',
  },
  {
    id: 'life',
    nameCN: '生活',
    nameEN: 'Life',
    videoUrl: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260702_081042_df7202bf-bd80-4b2b-bbc6-1f09ba2870e9.mp4',
  },
  {
    id: 'leisure',
    nameCN: '休闲',
    nameEN: 'Leisure',
    videoUrl: 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260702_080959_4cac5234-3573-464e-a5b7-76b94b8a7d61.mp4',
  },
];

const OVERLAY_PNG = 'https://soft-zoom-63098134.figma.site/_assets/v11/0b4a435b2df2747593c43d7a1c9b4578f7d8d90c.png';

// ============================================================
// NAVIGATION BAR
// ============================================================
const NavBar: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <motion.nav
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      className="fixed top-0 left-0 right-0 z-50"
      style={{
        background: 'rgba(10,10,15,0.55)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        boxShadow: '0 1px 0 rgba(255,255,255,0.04), 0 4px 24px rgba(0,0,0,0.40)',
        padding: '1rem 0',
      }}
    >
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
        <span
          className="text-xl font-serif italic tracking-wide text-white/95 cursor-pointer select-none"
          style={{ fontFamily: "'Instrument Serif', Georgia, serif" }}
        >
          WorldLens
        </span>

        <div className="hidden md:flex items-center gap-1">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              className="px-5 py-2 text-sm text-white/70 hover:text-white rounded-full transition-all duration-200 hover:bg-white/5"
            >
              {cat.nameCN}
            </button>
          ))}
        </div>

        <button
          className="md:hidden p-2 text-white/80 hover:text-white transition-colors"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="md:hidden"
            style={{
              background: 'rgba(10,10,15,0.95)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              borderBottom: '1px solid rgba(255,255,255,0.06)',
            }}
          >
            <div className="flex flex-col items-center gap-1 py-4">
              {CATEGORIES.map((cat, i) => (
                <motion.button
                  key={cat.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  onClick={() => setMobileOpen(false)}
                  className="w-full px-8 py-4 text-lg text-white/80 hover:text-white hover:bg-white/5 rounded-xl transition-colors text-center"
                >
                  {cat.nameCN}
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
};

// ============================================================
// HOME PAGE
// ============================================================
const HomePage: React.FC = () => {
  const [activeIndex, setActiveIndex] = useState(0);
  const navigate = useNavigate();
  const videoRefs = useRef<(HTMLVideoElement | null)[]>([]);

  const activeCategory = CATEGORIES[activeIndex];

  // Force play on the active video after mount / switch
  useEffect(() => {
    const vid = videoRefs.current[activeIndex];
    if (vid) {
      vid.play().catch(() => {});
    }
  }, [activeIndex]);

  return (
    <div
      style={{
        position: 'relative',
        width: '100vw',
        height: '100vh',
        overflow: 'hidden',
        background: '#0a0a0f',
        fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
        color: '#f1f5f9',
      }}
    >
      {/* ── Video Layer ── */}
      <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
        {CATEGORIES.map((cat, i) => (
          <video
            key={cat.id}
            ref={(el) => { videoRefs.current[i] = el; }}
            autoPlay
            muted
            loop
            playsInline
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              opacity: i === activeIndex ? 1 : 0,
              transition: 'opacity 1000ms ease-in-out',
            }}
          >
            <source src={cat.videoUrl} type="video/mp4" />
          </video>
        ))}
      </div>

      {/* ── PNG Overlay ── */}
      <img
        src={OVERLAY_PNG}
        alt=""
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '110%',
          objectFit: 'coverl',
          zIndex: 1,
          pointerEvents: 'none',
          animation: 'trainBob 6s ease-in-out infinite',
	  marginTop: '1px',
	}}
      />

      {/* ── Ambient Glows ── */}
      <div style={{ position: 'absolute', inset: 0, zIndex: 1, pointerEvents: 'none' }}>
        <div
          style={{
            position: 'absolute',
            width: 700,
            height: 700,
            borderRadius: '50%',
            opacity: 0.25,
            background: 'radial-gradient(circle, rgba(124,58,237,0.5) 0%, transparent 70%)',
            top: '-15%',
            right: '-8%',
            filter: 'blur(60px)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            width: 500,
            height: 500,
            borderRadius: '50%',
            opacity: 0.2,
            background: 'radial-gradient(circle, rgba(59,130,246,0.5) 0%, transparent 70%)',
            bottom: '-10%',
            left: '-5%',
            filter: 'blur(60px)',
          }}
        />
      </div>

      {/* ── Noise Overlay ── */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 2,
          pointerEvents: 'none',
          opacity: 0.025,
          backgroundImage:
            'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 512 512\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.85\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23n)\'/%3E%3C/svg%3E")',
          backgroundRepeat: 'repeat',
          backgroundSize: '512px 512px',
        }}
      />

      {/* ── Navigation ── */}
      <NavBar />

      {/* ── Content Overlay ── */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}
      >
        {/* Title + Subtitle */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeIndex}
            initial={{ opacity: 0, y: 32 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -24 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            style={{ textAlign: 'center', marginBottom: '3rem' }}
          >
            <h1
              style={{
                fontSize: 'clamp(5rem, 12vw, 10rem)',
                fontWeight: 700,
                letterSpacing: '0.05em',
                color: '#fff',
                textShadow: '0 4px 60px rgba(0,0,0,0.55)',
                lineHeight: 1.1,
                marginBottom: '0.4rem',
                fontFamily: "'Instrument Serif', Georgia, serif",
                fontStyle: 'italic',
              }}
            >
              {activeCategory.nameCN}
            </h1>
            <p
              style={{
                fontSize: 'clamp(1.25rem, 2.5vw, 2rem)',
                letterSpacing: '0.2em',
                color: 'rgba(255,255,255,0.75)',
                textShadow: '0 2px 20px rgba(0,0,0,0.5)',
              }}
            >
              {activeCategory.nameEN}
            </p>
          </motion.div>
        </AnimatePresence>

        {/* Explore Button */}
        <AnimatePresence mode="wait">
          <motion.div
            key={`btn-${activeIndex}`}
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.92 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            style={{ pointerEvents: 'auto' }}
          >
            <button
              onClick={() => navigate(`/category/${activeCategory.id}`)}
              className="glass-button glass-button--accent"
              style={{
                fontSize: '1.125rem',
                padding: '0.9rem 2.5rem',
                marginBottom: '3rem',
              }}
            >
              探索 →
            </button>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* ── Category Buttons ── */}
      <div
        style={{
          position: 'absolute',
          bottom: '3rem',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 10,
          display: 'flex',
          gap: '0.75rem',
        }}
      >
        {CATEGORIES.map((cat, i) => {
          const isActive = i === activeIndex;
          return (
            <button
              key={cat.id}
              onClick={() => setActiveIndex(i)}
              style={{
                padding: '0.7rem 1.6rem',
                borderRadius: '9999px',
                fontSize: '0.9375rem',
                fontWeight: 500,
                letterSpacing: '0.02em',
                background: isActive
                  ? 'rgba(255,255,255,0.16)'
                  : 'rgba(255,255,255,0.06)',
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
                border: isActive
                  ? '1px solid rgba(255,255,255,0.22)'
                  : '1px solid rgba(255,255,255,0.10)',
                color: isActive ? '#fff' : 'rgba(255,255,255,0.65)',
                boxShadow: isActive
                  ? 'inset 0 1px 0 rgba(255,255,255,0.12), 0 8px 32px rgba(0,0,0,0.40), 0 0 24px rgba(124,58,237,0.25)'
                  : 'inset 0 1px 0 rgba(255,255,255,0.05), 0 4px 16px rgba(0,0,0,0.30)',
                transition:
                  'all 400ms cubic-bezier(0.4, 0, 0.2, 1)',
                cursor: 'pointer',
                position: 'relative' as const,
                overflow: 'hidden',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.10)';
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.18)';
                  e.currentTarget.style.color = 'rgba(255,255,255,0.88)';
                  e.currentTarget.style.boxShadow =
                    'inset 0 1px 0 rgba(255,255,255,0.08), 0 8px 32px rgba(0,0,0,0.40)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.10)';
                  e.currentTarget.style.color = 'rgba(255,255,255,0.65)';
                  e.currentTarget.style.boxShadow =
                    'inset 0 1px 0 rgba(255,255,255,0.05), 0 4px 16px rgba(0,0,0,0.30)';
                }
              }}
            >
              {cat.nameCN}
            </button>
          );
        })}
      </div>

      {/* ── Train-bob keyframe injection ── */}
      <style>{`
        @keyframes trainBob {
          0%, 100% { transform: translateY(0); }
          50%      { transform: translateY(-10px); }
        }
      `}</style>
    </div>
  );
};

// ============================================================
// APP
// ============================================================
const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/category/:id" element={<CategoryPage />} />
    </Routes>
  );
};

export default App;
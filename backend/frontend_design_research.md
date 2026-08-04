# WorldLens Frontend Design Research

## 1. Design Philosophy

WorldLens should embody **cinematic intelligence** — a blend of editorial gravitas with futuristic AI insight. The aesthetic draws from Apple Vision Pro's spatial immersion: floating panels, glassmorphism depth layers, and subtle motion that guides attention without distraction. This is not a news reader; it's an intelligence dashboard that makes complex patterns feel immediate and tangible.

Key principles:
- **Glassmorphism as canvas**: Frosted-glass panels create visual hierarchy while maintaining connectivity to underlying content
- **Motion as meaning**: Transitions reveal relationships (drill-down from briefing to article) rather than decorate
- **Dark mode default**: Reduces eye strain during extended reading sessions; enhances vibrant accent colors for alerts and trends
- **Editorial typography**: Serif headlines carry authority; sans-serif body text ensures readability at small sizes

---

## 2. MotionSites Style Analysis

Reference site (stillmind) presents a cinematic, dark-mode-heavy layout with parallax scrolling, large video backgrounds, and smooth section transitions. For WorldLens, we adapt these cues into a productive dashboard interface:

| Style Element | Adaptation for WorldLens | Implementation Approach |
|---------------|------------------------|------------------------|
| Cinematic background | Subtle animated globe/network overlay instead of heavy video to avoid performance hit | Three.js background particle network |
| Glass navigation | Semi-transparent frosted navbar with blur backdrop | CSS `backdrop-filter: blur(20px)` + semi-transparent gradient |
| Floating UI | Interactive cards lift on hover, modals emerge from center | CSS transforms + Framer Motion spring physics |
| Animated typography | Headings appear with staggered fade-in on scroll | IntersectionObserver + FLIP animation |
| Smooth section transitions | Page-level fade/slide on route change | React Router + AnimatePresence |

---

## 3. Framer Components

### Hero Section

| Name | Purpose | Visual Style | How to Rebuild in React | Recommended Library |
|------|---------|--------------|------------------------|---------------------|
| **Glass Navigation Bar** | Persistent top bar with brand logo, search, user menu, and quick filters | Frosted glass with subtle border glow, centered text on right, left-aligned brand icon | Use Tailwind `backdrop-blur-lg` + `bg-white/5` with absolute-positioned div behind for border glow | Headless UI (for accessible dropdowns) |
| **Hero Banner with Video BG** | Full-width immersive header showcasing latest daily briefings or featured intelligence stories | Auto-playing muted video loop with gradient overlay, headline overlaid in large serif font, CTA button with glass effect | Use `react-spring` or `framer-motion` for hero text entrance; overlay gradient via CSS pseudo-element | Framer Motion (`<AnimatePresence>`) |
| **Animated Globe Widget** | Interactive rotating earth visualization representing global coverage area | Wireframe-style globe with pulsing dots indicating active regions, minimal controls | Three.js `SphereGeometry` with orbit controls; particles animate using `useFrame` from `@react-three/fiber` | `@react-three/drei`, `three` |
| **Floating Search Overlay** | Expandable search field that reveals advanced filters when triggered | Material-like floating pill that expands into full filter panel with date ranges, sources, sentiment sliders | Controlled component with spring-based width/height transition; backdrop overlay | Framer Motion (`motion.div` with `layout`) |
| **Daily Briefing Teaser** | Prominent card displaying today's headline summary with key trends | Large card with rounded corners, slight elevation, trending badges animating upward | Position fixed at top-right of viewport; use `useScroll` for parallax tilt on move | `framer-motion` (`useSprings`, `useTransform`) |

### Intelligence Dashboard

| Name | Purpose | Visual Style | How to Rebuild in React | Recommended Library |
|------|---------|--------------|------------------------|---------------------|
| **AI Intelligence Cards** | Clickable tiles showing article summaries with importance score, sentiment color, trend tag | Card with gradient accent border depending on sentiment (green/blue/red), importance score badge in top-right, miniature globe icon for regional focus | Grid layout with `motion.div` staggered entrance; `hover:scale-1.02` for tactile feedback | Framer Motion, CSS Grid |
| **Timeline View** | Chronological flow of analyzed articles with vertical connecting line | Vertical spine line with nodes for each article; expand node to show preview, drag to reorder | D3.js for line path + `useDrag` from `dnd-kit` for reordering | `d3` + `dnd-kit` |
| **Article List View** | Traditional table/list format for sorting/filtering/searching | Clean rows with alternating background, column headers with sortable icons, preview snippets on expand | Infinite virtualization for large datasets; sticky header | TanStack Table + `@tanstack/react-virtual` |
| **Trend Heatmap Visualization** | Grid showing trend level by region/time dimension with color intensity | Hexagonal or square grid where cells fill with color intensity based on event frequency/changing pattern over time | Canvas-based rendering for performance; cell size configurable based on viewport | `recharts` or custom Canvas + `react-spring` |
| **Sentiment Distribution Chart** | Pie/donut chart showing positive/negative/neutral proportions across collected articles | Minimalist donut with animated fill on load, percentage labels outside segments | Animated stroke-dasharray transition on mount; legend below | `recharts` |
| **Source Distribution Map** | Word cloud or geographic breakdown by news source origin | Interactive world map with clickable regions showing top sources per country | Leaflet map with GeoJSON; click handlers to filter article list | `react-leaflet` |

---

## 4. Vector Resources

### Global Intelligence / Network Visualization

| Explanatory Vector Type | Where to Use | Description |
|------------------------|--------------|-------------|
| **Animated Connection Network** | Loading state before dashboard loads; background of article detail pages | Interconnected nodes with pulsing lines between them. Represents AI making connections across articles. Should be subtle enough not to distract from content. | Use on homepage loading screen, idle state of article list |
| **Globe with Orbiting Data Points** | Hero section background; "Global Coverage" feature badge | Stylized wireframe sphere with rotating satellite-like points that leave trails when passing. Symbolizes worldwide monitoring and intelligence gathering. | Hero banner background (subtle opacity), dashboard loading placeholder |
| **Neural Pathway Lines** | Separator between sections; loading spinner conceptual art | Curved parallel lines with glowing pulses moving along them. Evokes AI processing pathways. | Horizontal divider between briefing teaser and article list |
| **Abstract Flow Charts** | Blog/docs page illustrating data pipeline (RSS → Analysis → Briefing) | Simple node-link diagrams with arrowheads showing unidirectional flow. Can animate arrows to show data movement. | Documentation pages about how WorldLens works |

### Earth & Satellite Imagery

| Vector Type | Where to Use | Description |
|-------------|--------------|-------------|
| **Low-Poly Earth** | Article map view selector; settings/location preferences | Simplified polygonal earth surface with visible triangulation. Modern tech aesthetic, lightweight for SVG export. | Region selector in filter modal |
| **Satellite Orbit Icons** | Source listing; feed status indicators | Miniature orbiting satellites around Earth or abstract circular paths. RSS feeds represented as signal waves feeding into orbit. | UI icon indicating real-time feed status |
| **Signal Wave Ripples** | New article notification toast; collection success indicator | Concentric circles emanating from central point like ripples. Subtle green/blue gradient. | Toast notification after successful collection |
| **Data Packet Streams** | Article feed visualization; live collection progress | Stream of diamond-shaped packets moving along trajectory. Color-coded by source type or urgency. | Live collector indicator in nav bar |

### Information Flow & Abstract

| Vector Type | Where to Use | Description |
|-------------|--------------|-------------|
| **Falling Data Stream** | Empty state for new database; no articles found | Vertical cascade of rectangular blocks falling like rain. Empty collection metaphor. | Article list when zero results |
| **Brain with Circuit Overlay** | About page; AI analysis explanation | Human head silhouette integrated with circuit board traces blending into neural synapses. Good for explaining AI role. | Settings page toggle for AI analysis explanations |
| **Document Stack with Scan Lines** | Export/import functionality; reports generated | Multiple layered document sheets with diagonal scan overlay suggesting digital processing. Export/download modals | Briefing export dialog |
| **Magnifying Glass Over Content** | Search highlighter; filter applied state | Lens positioned over stylized text fragments, magnifying specific words. Visual metaphor for insight discovery. | Search results highlighting active term |

---

## 5. Plugin Recommendations

### Animation Libraries

| Plugin | Purpose | React Alternative | Why |
|--------|---------|-------------------|-----|
| **Framer Motion** | Component-level transitions, gesture-based interactions, layout animations | Native (already chosen) | Industry-standard for React; supports `AnimatePresence` for route transitions, `spring` physics for natural motion, drag gestures |
| **React Spring** | Physics-based animation library, complex chained animations | Framer Motion (preferred) | Framer Spring already built in; keep single animation paradigm to reduce bundle size |
| **GSAP** | Scroll-triggered animations, complex timeline sequences | Framer IntersectionObserver | Only if need pixel-perfect scroll effects; add only for specific sections |

### Shader & Visual Effects

| Plugin | Purpose | React Alternative | Why |
|--------|---------|-------------------|-----|
| **Shadcn UI** | Accessible, customizable component system with Tailwind | Shadcn UI | Perfect fit: tailwind-based, dark mode ready, component-focused philosophy matches our glass/motion design |
| **Tailwind CSS** | Utility-first styling framework | Tailwind CSS | Already selected; enables rapid prototyping of glassmorphism classes |

### 3D Assets & Rendering

| Plugin | Purpose | React Alternative | Why |
|--------|---------|-------------------|-----|
| **React Three Fiber (R3F)** | Declarative Three.js integration for WebGL scenes | `@react-three/fiber` | Standard for 3D in React; integrates well with Framer Motion via `useFrame` |
| **Three.js** | Core 3D engine for custom visualizations | R3F + Drei | Use directly only if needing low-level control beyond R3F abstractions |
| **Drei utilities** | Common R3F helpers (OrbitControls, Text, Environment) | `@react-three/drei` | Pre-built components save significant boilerplate |

### Asset Workflow & Tooling

| Plugin | Purpose | React Alternative | Why |
|--------|---------|-------------------|-----|
| **SVGOMG** | SVGO GUI for optimizing exported SVGs | CLI tool `svgo` | Reduce vector file size for faster load times; automate via build hook |
| **Figma to Code converters** | Export designs as React/Tailwind components | Manual implementation | Most conversion tools produce bloated code; hand-crafted components ensure performance and consistency |
| **lucide-icons** | Lightweight, consistent open-source icon set | `lucide-react` | Exactly what we need: simple outlines that match clean UI aesthetic, tree-shakable, supports react integration |
| **react-query (TanStack Query)** | Server state management, caching, background refetches | `@tanstack/react-query` | Essential for fetching articles/briefings automatically, handling stale-while-revalidate, error states |

---

## 6. React Technology Stack

### Framework: **TypeScript + Vite**

| Choice | Reasoning |
|--------|-----------|
| **Next.js App Router** (or standalone Vite + React Router) | Next.js provides built-in routing, API proxy capabilities for backend communication, and server-side rendering benefits for SEO. However, since WorldLens is primarily a desktop app (Electron), a simpler **Vite + React Router** setup reduces complexity while delivering fast dev server HMR and static export capability for Electron integration. Given the project scope (solo developer portfolio, MVP-focused), Vite + React Router is lighter and aligns with the desktop-first approach. |

**Decision: Vite 5 + React 18 + TypeScript 5.x**  
Fastest startup, excellent dev experience, native ESM support, perfect for Electron integration via `vite-plugin-electron`.

### Language: **TypeScript**

Strong typing prevents runtime errors in complex UI interactions (drag-and-drop timelines, card selections). Type definitions mirror backend API contracts (`Article`, `Analysis`, `Briefing`). Essential for maintaining code quality in a growing application.

### Styling: **Tailwind CSS + Shadcn UI**

- **Tailwind CSS**: Enables rapid construction of glassmorphism (`backdrop-blur-lg`, `bg-white/10`), gradients, and responsive layouts without writing custom CSS. Custom colors defined in `tailwind.config.js` match the cinematic theme palette.
- **Shadcn UI**: Copy-paste, component-based foundation providing accessible, customizable primitives (buttons, dialogs, tables, inputs) styled with Tailwind. Each component source is editable—perfect for adapting to custom needs (e.g., modifying card hover effects, animation timings).

### Animation: **Framer Motion**

The single most important addition for the requested "cinematic" feel. Supports:

- Staggered hero entry (`motion.h1`, `motion.p` with `initial={{opacity:0, y:20}}`)
- Card hover lift with spring physics (`whileHover={{scale:1.02, transition:{type:"spring", stiffness:300}}}`)
- Modal/dialog emergence with backdrop fade
- Route-level transitions (`<AnimatePresence>` with `<motion.div key={route}>`)
- Drag-and-drop for timeline reordering via `useDrag` / `useDrop` integration

Bundle weight reasonable (~13KB gzipped); production-ready with extensive documentation.

### 3D Elements: **Three.js + React Three Fiber**

For the animated globe/network background and any spatial visualizations:

- Use `@react-three/fiber` declarative approach for cleaner integration with React state
- Leverage `@react-three/drei` for pre-built helpers (`OrbitControls`, `Environment`, `Text`)
- Keep complexity minimal: one background layer with subtle particle animation, not an interactive simulation

This approach ensures the background doesn't interfere with content readability or consume excessive CPU/GPU resources during extended use.

### State Management: **TanStack Query (react-query) + Zustand**

- **TanStack Query**: Handles all server-state fetching (articles, briefings, analysis results). Provides automatic cache management, retry logic, background refetch, and loading/error states exactly needed for our async backend API. Integrates seamlessly with TypeScript.
- **Zustand**: For client-only state (UI toggles: sidebar open/close, modal visibility, selected article ID, filter settings). Lightweight compared to Redux, no boilerplate store setup, easy to scale as needed. No provider wrapping required.

File structure keeps query hooks in `/hooks/` and stores in `/stores/`, promoting separation of concerns.

### Additional Dependencies:

| Package | Purpose |
|---------|---------|
| **lucide-react** | Icon set (lightweight, outline style matches dashboard aesthetic) |
| **clsx / cn** | Conditional class name helpers for Shadcn composition |
| **sonner** | Toast notifications (success/error messages for collection/analysis actions) | Matches "modern but friendly" design principle |
| **date-fns-tz** | Date formatting with timezone support for article timestamps |
| **zustand** | Global UI state management |
| **@tanstack/react-query** | Server state sync with FastAPI backend |
| **@react-three/fiber** | 3D background globe rendering |
| **three** + **@react-three/drei** | Three.js ecosystem helpers |
| **emmet** (VS Code extension) | Faster HTML-like JSX development |

---

## 7. Local Development Setup

### Prerequisites

```bash
# Node.js v18+ (LTS recommended)
npm install -g nvm # Optional Node version manager

# Install core dependencies
cd frontend
npm install
```

### Project Structure (Planned)

```
frontend/
├── src/
│   ├── components/           # Reusable UI (Button, Card, Navbar, GlobeBackground)
│   ├── pages/                # Route-based (HomePage, BriefingPage, ArticlesPage)
│   ├── hooks/                # Query hooks (useArticles, useBriefings)
│   ├── stores/               # Zustand UI stores (useStore)
│   ├── lib/                  # Utils, config, API client
│   ├── styles/               # Tailwind config, global CSS, theme variables
│   └── main.tsx              # Entry point
├── vite.config.ts            # Vite configuration
├── package.json
└── tsconfig.json
```

### Running Development Server

```bash
# Start Vite dev server (hot reload enabled)
npm run dev

# Typically http://localhost:5173
```

### Electron Integration (Preview)

Electron will serve the built static files from the frontend `dist/` directory. Development workflow:

1. Run Vite dev server in one terminal window
2. Run Electron in another with `--disable-gpu` flag if needed
3. Electron can either `http://localhost:5173` (dev) or serve local build files

See `package.json` scripts for combined start commands.

### Build for Production

```bash
npm run build          # Creates ./dist with optimized static assets
npm run preview        # Locally tests production build
```

---

## 8. Frontend Architecture

### Layered Structure

```
┌─────────────────────────────────────────────┐
│                 Presentation Layer          │ ← React Components (UI)
│  [Pages]            [Components]             │
│  HomePage         GlobeBackground           │
│  ArticlesPage     IntelligenceCard          │
│  BriefingPage     TimelineView              │
└──────────────────┬──────────────────────────┘
                   │ State flows down via props
                   │ Events bubble up via callbacks
┌─────────────────────────────────────────────┐
│               Application Layer             │ ← Store + Services
│  [Zustand Store]    [Query Hooks]           │
│  useThemeStore    useArticlesQuery()       │
│  useUIStore       useBriefingsQuery()      │
└──────────────────┬──────────────────────────┘
                   │ API calls
┌─────────────────────────────────────────────┐
│               Infrastructure Layer          │ ← API Client
│  [api.ts]                                      │
│  const api = createClient(BASE_URL)         │
│  articleApi = { getAll, getOne, enrich }     │
└─────────────────────────────────────────────┘
```

### Routing Strategy

Since this targets a desktop app with Electron, client-side routing is handled by **React Router DOM v6**:

```tsx
// routes.tsx
<Routes>
  <Route path="/" element={<HomeLayout />}>
    <Route index element={<HomePage />} />
    <Route path="articles" element={<ArticlesLayout />}>
      <Route path=":id" element={<ArticleDetail />} />
    </Route>
    <Route path="briefings/:date" element={<BriefingPage />} />
  </Route>
</Routes>
```

Electron's main process loads the same URL initially but subsequent navigations stay within the renderer process.

### Data Fetching Pattern

All backend communication goes through TanStack Query hooks:

```tsx
// hooks/articles.ts
export function useArticlesQuery(status?: string) {
  return useQuery({
    queryKeys: ['articles', status],
    queryFn: () => fetchArticles(status),
    staleTime: 5 * 60 * 1000, // 5 minutes auto-refresh
    retry: 1,
  });
}
```

This provides: automatic loading skeletons, cached responses, background refresh, graceful error states—all with minimal code.

### Component Composition Model

```tsx
// IntelligenceCard component (shared between list and detail views)
const IntelligenceCard = ({ article, analysis, onExpand }) => (
  <motion.article
    className="glass-card hover:shadow-xl transition-all"
    whileHover={{ y: -4 }}
    onClick={onExpand}
  >
    <div className="flex items-start justify-between">
      <h3 className="font-serif text-lg">{article.title}</h3>
      <Badge variant={importanceToVariant(article.analysis.importance)}>
        {article.analysis.importance}/10
      </Badge>
    </div>
    <p className="text-sm mt-2 text-muted-foreground">
      {article.analysis.summary}
    </p>
    {/* ... */}
  </motion.article>
);
```

Reusability achieved through compound components (variant props, controlled callbacks) ensuring consistent behavior across list/detail views.

### Theme & Accessibility

- **Tailwind theme** configured in `tailwind.config.js`:
  ```js
  theme: {
    extend: {
      colors: {
        brand: {
          100: '#A7DBA8', // soft accent for highlights
          900: '#0A4737', // primary dark for headings
        },
        background: 'rgba(10, 15, 30, 0.8)', // deep navy with alpha for glass effect
        foreground: '#E4E4E4',
      },
      fontFamily: {
        serif: ['Merriweather', 'seriatext'], // headlines for editorial feel
        sans: ['Inter', 'sans-serif'],        // body text for clarity
      },
    },
  }
  ```
- **Full keyboard navigation** ensured via Shadcn accessible components
- **Reduced motion option** honored via prefers-reduced-media media query
- **Color contrast ratios** meet WCAG AA minimums (tested with axe-core during dev)

---

## 9. Development Roadmap

### Phase 1: Foundation & Core Layout (Week 1-2)

1. Set up Vite + React + TypeScript + Tailwind project scaffold
2. Configure Shadcn UI base installation (button, card, input, select, dialog)
3. Create shared utility components: `GlassCard`, `LoadingSpinner`, `ErrorToast`
4. Implement global state store (Zustand) for UI toggles (sidebar, filters, theme)
5. Build basic route structure with React Router (home → articles → briefing)
6. Create persistent navigation bar with hamburger toggle for mobile responsiveness

**Deliverable**: Skeleton app with working navigation, empty shell pages, styled base components.

### Phase 2: Article Intelligence Views (Week 3-4)

1. Build `ArticlesPage` with integrated list/timeline toggle
2. Implement `IntelligenceCard` component with all required fields
3. Add TanStack Query hooks to fetch article + analysis data from backend
4. Connect collection trigger button to `POST /api/v1/articles/collect` endpoint
5. Connect manual analyze buttons to individual `/analyze` endpoint triggers
6. Add filtering controls (by status, category, sentiment, date range)

**Deliverable**: Functional article browsing with real data fetched from backend API.

### Phase 3: Briefing & Visualization Layer (Week 5-6)

1. Create `BriefingPage` with today's auto-generated briefing display
2. Add historical browsing (`GET /api/v1/briefings`) and manual generation trigger
3. Implement visual components: sentiment donut chart, trend heatmap (using recharts)
4. Integrate Three.js globe background component for home page hero section
5. Add "expand article from briefing" drill-down navigation

**Deliverable**: Complete briefing experience with supporting visualizations.

### Phase 4: Polish & UX Refinement (Week 7-8)

1. Add micro-interactions: toast notifications on success/error, button loading states
2. Implement smooth route transitions with `AnimatePresence`
3. Optimize perf: lazy-load heavy components (charts, 3D globe) on mount
4. Add accessibility checks (keyboard nav, screen reader labels, contrast validation)
5. Finalize responsive breakpoints (desktop → tablet → mobile portrait)
6. Prepare production build script and Electron integration

**Deliverable**: Fully polished, production-ready frontend ready for Electron packaging.

### Future Expansion (Post-MVP)

1. User accounts/profiles (if adding multi-user support)
2. Personalized recommendations engine (based on read history/saved articles)
3. Export briefings as PDF/PPT with branded templates
4. Desktop notifications for breaking high-importence alerts
5. Offline mode with local SQLite fallback for collection

---

## Summary

The WorldLens frontend combines **Tailwind CSS + Shadcn UI** for production-grade components, **Framer Motion** for cinematic interactions, **TanStack Query** for seamless server-state sync, and **Three.js/R3F** for elegant 3D visuals—all built with **TypeScript + Vite** for maximum developer velocity. This stack delivers the requested premium, AI-powered intelligence aesthetic while keeping implementation practical for a solo developer portfolio project. All components are modular, testable, and easily extendable for future phases.
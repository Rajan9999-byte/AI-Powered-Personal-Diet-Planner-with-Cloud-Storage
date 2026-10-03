import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { Link, NavLink, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { api } from './lib/api.js';
import { formatCalories, formatNumber, progressPercent, relativeDate } from './lib/formatters.js';

const AuthContext = createContext(null);

function useAuth() {
  return useContext(AuthContext);
}

function LoadingScreen() {
  return <main className="center-stage"><div className="loading-orb" /><p>Preparing your wellness workspace…</p></main>;
}

function Notice({ children, tone = 'info' }) {
  return <div className={`notice notice-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>{children}</div>;
}

function BrandMark({ compact = false }) {
  return <Link className={`brand ${compact ? 'brand-compact' : ''}`} to="/">
    <img src="/logo.svg" alt="" />
    <span><strong>Dietly</strong><small>Planner</small></span>
  </Link>;
}

function AppShell({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const links = [
    ['/dashboard', 'Overview', '◒'],
    ['/profile', 'Your profile', '◎'],
    ['/plan', 'Meal plan', '✣'],
    ['/tracker', 'Daily tracker', '⌁']
  ];
  async function handleLogout() {
    await logout();
    navigate('/login');
  }
  return <div className="app-shell">
    <aside className="sidebar">
      <BrandMark />
      <div className="sidebar-label">Workspace</div>
      <nav className="side-nav" aria-label="Main navigation">
        {links.map(([to, label, icon]) => <NavLink key={to} to={to} className={({ isActive }) => isActive ? 'active' : ''}><span className="nav-icon">{icon}</span>{label}</NavLink>)}
      </nav>
      <div className="sidebar-bottom">
        <div className="privacy-note"><span className="status-dot" /> Local demo mode<br /><small>Your data stays in this workspace.</small></div>
        <button className="user-chip" onClick={handleLogout} title="Log out">
          <span className="avatar">{user?.name?.slice(0, 1).toUpperCase() || 'D'}</span>
          <span><strong>{user?.name || 'Demo user'}</strong><small>Log out</small></span>
          <span className="logout-arrow">↗</span>
        </button>
      </div>
    </aside>
    <div className="main-column">
      <header className="mobile-header"><BrandMark compact /><button className="mobile-logout" onClick={handleLogout}>Log out</button></header>
      <main className="page-content">{children}</main>
    </div>
  </div>;
}

function AuthPage({ mode }) {
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: 'demo@dietly.local', password: 'demo12345' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const isRegister = mode === 'register';
  useEffect(() => { if (user) navigate('/dashboard', { replace: true }); }, [user, navigate]);
  function update(event) { setForm({ ...form, [event.target.name]: event.target.value }); }
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true);
    try {
      if (isRegister) await register(form); else await login({ email: form.email, password: form.password });
      navigate('/dashboard');
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return <div className="auth-layout">
    <section className="auth-story">
      <BrandMark />
      <div className="story-copy"><span className="eyebrow">Plan gently. Track clearly.</span><h1>A calmer way to make meals fit your day.</h1><p>Build an everyday food rhythm from your goals, preferences, and the progress you can actually see.</p>
        <div className="story-pill"><span>✦</span><span><strong>Wellness, not perfection.</strong><small>Plans are educational examples, never medical advice.</small></span></div>
      </div>
      <div className="story-footer">Built as a cloud computing course project · synthetic demo data only</div>
    </section>
    <section className="auth-panel"><div className="auth-card">
      <div className="auth-card-head"><span className="eyebrow">{isRegister ? 'Start your workspace' : 'Welcome back'}</span><h2>{isRegister ? 'Create your account' : 'Log in to Dietly'}</h2><p>{isRegister ? 'Your profile takes less than two minutes.' : 'Pick up where your last plan left off.'}</p></div>
      {error && <Notice tone="error">{error}</Notice>}
      <form onSubmit={submit} className="form-stack">
        {isRegister && <label>Full name<input name="name" value={form.name} onChange={update} placeholder="e.g. Priya Shah" required /></label>}
        <label>Email<input type="email" name="email" value={form.email} onChange={update} placeholder="you@example.com" required /></label>
        <label>Password<input type="password" name="password" value={form.password} onChange={update} placeholder="At least 8 characters" minLength="8" required /></label>
        <button className="button button-primary button-wide" disabled={busy}>{busy ? 'Working…' : isRegister ? 'Create account →' : 'Log in →'}</button>
      </form>
      {!isRegister && <div className="demo-callout"><span className="spark">✦</span><div><strong>Demo account prefilled</strong><small>Use demo@dietly.local / demo12345 after running the seed command.</small></div></div>}
      <p className="switch-auth">{isRegister ? 'Already have an account?' : 'New to Dietly?'} <Link to={isRegister ? '/login' : '/register'}>{isRegister ? 'Log in' : 'Create one'}</Link></p>
    </div></section>
  </div>;
}

function PageHeader({ eyebrow, title, description, action }) {
  return <div className="page-header"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</div>;
}

function StatCard({ label, value, note, accent = 'green' }) {
  return <div className={`stat-card accent-${accent}`}><span className="stat-label">{label}</span><strong>{value}</strong>{note && <small>{note}</small>}</div>;
}

function MacroBar({ label, current, target, color }) {
  return <div className="macro-row"><div className="macro-row-head"><span>{label}</span><strong>{formatNumber(current, 'g')} <small>/ {formatNumber(target, 'g')}</small></strong></div><div className="progress-track"><div className={`progress-fill ${color}`} style={{ width: `${progressPercent(current, target)}%` }} /></div></div>;
}

function MealCard({ meal, compact = false }) {
  return <article className={`meal-card ${compact ? 'meal-card-compact' : ''}`}><div className="meal-card-head"><div><span className="meal-kicker">{meal.label}</span><h3>{meal.items.map(item => item.name).join(' + ')}</h3></div><strong>{formatCalories(meal.totals.kcal)}</strong></div><ul>{meal.items.map(item => <li key={item.food_id}><span>{item.name}</span><span>{Math.round(item.grams)}g</span></li>)}</ul><div className="meal-macros"><span>P {Math.round(meal.totals.protein)}g</span><span>C {Math.round(meal.totals.carbs)}g</span><span>F {Math.round(meal.totals.fat)}g</span></div></article>;
}

function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState(null); const [error, setError] = useState('');
  useEffect(() => { api.getDashboard().then(setData).catch(err => setError(err.message)); }, []);
  if (error) return <Notice tone="error">{error}</Notice>;
  if (!data) return <LoadingScreen />;
  const { profile, targets, today, current_plan: plan } = data;
  const displayTargets = targets || { calories: 0, macros: { protein: 0, carbs: 0, fat: 0 } };
  return <>
    <PageHeader eyebrow={`Good to see you, ${profile?.name || user?.name || 'there'}`} title="Your daily rhythm" description="A small plan for today, with room to adapt." action={<Link className="button button-primary" to={profile ? '/plan' : '/profile'}>{profile ? 'Build a plan →' : 'Complete profile →'}</Link>} />
    {!profile && <Notice tone="info">Tell us about your routine first. We’ll use it to calculate an educational target and shape your meals.</Notice>}
    <section className="stat-grid"><StatCard label="Daily target" value={targets ? formatCalories(targets.calories) : '—'} note={targets ? `TDEE ${formatNumber(targets.tdee)} kcal` : 'Complete profile'} /><StatCard label="Logged today" value={formatCalories(today.intake.kcal)} note={targets ? `${progressPercent(today.intake.kcal, targets.calories)}% of target` : 'Start with a meal'} accent="apricot" /><StatCard label="Current goal" value={profile?.goal ? profile.goal.replace('maintain', 'Maintain').replace('cut', 'Weight care').replace('gain', 'Build').replace('balanced', 'Balanced') : '—'} note={profile?.dietary_preference ? `${profile.dietary_preference} preference` : 'Choose a preference'} accent="ink" /></section>
    <div className="dashboard-grid"><section className="panel macro-panel"><div className="panel-head"><div><span className="eyebrow">Today at a glance</span><h2>Fuel, not friction</h2></div><Link to="/tracker" className="text-link">Open tracker ↗</Link></div>{targets ? <div className="macro-list"><MacroBar label="Protein" current={today.intake.protein} target={targets.macros.protein} color="green" /><MacroBar label="Carbohydrates" current={today.intake.carbs} target={targets.macros.carbs} color="apricot" /><MacroBar label="Fats" current={today.intake.fat} target={targets.macros.fat} color="ink" /></div> : <div className="empty-block"><span className="empty-icon">◎</span><h3>Your targets appear here</h3><p>Save a profile to turn your goals into a simple, approximate target.</p></div>}</section><section className="panel habit-panel"><div className="panel-head"><div><span className="eyebrow">Gentle reminder</span><h2>One useful habit</h2></div><span className="habit-icon">◌</span></div><p>Keep a glass or bottle in reach during the day. Hydration is easier when it is visible.</p><div className="habit-rule" /><small>General wellness prompt · adjust to your context</small></section></div>
    <section className="section-block"><div className="section-heading"><div><span className="eyebrow">Latest plan</span><h2>{plan ? plan.title : 'A plan is one click away'}</h2></div>{plan && <Link to="/plan" className="text-link">See full plan ↗</Link>}</div>{plan ? <div className="meal-grid">{plan.meals.map(meal => <MealCard key={meal.id} meal={meal} compact />)}</div> : <div className="empty-block empty-plan"><span className="empty-icon">✣</span><h3>Make your first wellness plan</h3><p>We’ll use your saved preferences to suggest four approachable meals.</p><Link className="button button-secondary" to={profile ? '/plan' : '/profile'}>{profile ? 'Generate a plan' : 'Set up your profile'}</Link></div>}</section>
  </>;
}

function ProfilePage() {
  const { user, refresh } = useAuth();
  const [form, setForm] = useState({ name: user?.name || '', age: '', sex: 'female', height_cm: '', weight_kg: '', activity_level: 'moderate', dietary_preference: 'vegetarian', goal: 'balanced', allergies: [], cuisines: [], budget_per_day: '', timeline_weeks: '' });
  const [allergyText, setAllergyText] = useState(''); const [cuisineText, setCuisineText] = useState(''); const [status, setStatus] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [upload, setUpload] = useState(false);
  useEffect(() => { api.getProfile().then(({ profile }) => { if (profile) { setForm(profile); setAllergyText(profile.allergies.join(', ')); setCuisineText(profile.cuisines.join(', ')); } }).catch(err => setError(err.message)); }, []);
  function update(event) { setForm({ ...form, [event.target.name]: event.target.value }); setStatus(''); }
  async function save(event) { event.preventDefault(); setBusy(true); setError(''); setStatus(''); try { await api.saveProfile({ ...form, age: Number(form.age), height_cm: Number(form.height_cm), weight_kg: Number(form.weight_kg), budget_per_day: form.budget_per_day === '' ? null : Number(form.budget_per_day), timeline_weeks: form.timeline_weeks === '' ? null : Number(form.timeline_weeks), allergies: allergyText.split(',').map(item => item.trim()).filter(Boolean), cuisines: cuisineText.split(',').map(item => item.trim()).filter(Boolean) }); await refresh(); setStatus('Profile saved. Your target is ready to calculate.'); } catch (err) { setError(err.message); } finally { setBusy(false); } }
  async function handleUpload(event) { const file = event.target.files?.[0]; if (!file) return; setUpload(true); setError(''); try { await api.uploadProfilePhoto(file); setStatus('Profile image saved to local object storage.'); } catch (err) { setError(err.message); } finally { setUpload(false); } }
  return <><PageHeader eyebrow="Personal inputs" title="Your profile" description="A few details help the planner make more useful general-wellness suggestions." />{error && <Notice tone="error">{error}</Notice>}{status && <Notice tone="success">{status}</Notice>}<form className="panel form-card" onSubmit={save}><div className="form-section"><div className="form-section-title"><span className="section-number">01</span><div><h2>About you</h2><p>Keep this to demo information only.</p></div></div><div className="form-grid"><label>Name<input name="name" value={form.name} onChange={update} required /></label><label>Age<input name="age" type="number" min="13" max="100" value={form.age} onChange={update} required /></label><label>Sex<select name="sex" value={form.sex} onChange={update}><option value="female">Female</option><option value="male">Male</option><option value="other">Other / prefer not to say</option></select></label><label>Height (cm)<input name="height_cm" type="number" min="100" max="230" value={form.height_cm} onChange={update} required /></label><label>Weight (kg)<input name="weight_kg" type="number" min="30" max="250" value={form.weight_kg} onChange={update} required /></label><label>Activity<select name="activity_level" value={form.activity_level} onChange={update}><option value="sedentary">Mostly seated</option><option value="light">Lightly active</option><option value="moderate">Moderately active</option><option value="active">Very active</option></select></label></div></div><div className="form-section"><div className="form-section-title"><span className="section-number">02</span><div><h2>Your direction</h2><p>Choose a broad goal, not a prescription.</p></div></div><div className="form-grid"><label>Dietary preference<select name="dietary_preference" value={form.dietary_preference} onChange={update}><option value="vegetarian">Vegetarian</option><option value="vegan">Vegan</option><option value="nonveg">General / non-vegetarian</option></select></label><label>Goal<select name="goal" value={form.goal} onChange={update}><option value="balanced">Balanced eating</option><option value="maintain">Weight maintenance</option><option value="cut">Weight-management demo</option><option value="gain">Fitness-oriented build</option><option value="fitness">Fitness-oriented performance</option></select></label><label>Allergies <span className="label-hint">comma separated</span><input value={allergyText} onChange={event => setAllergyText(event.target.value)} placeholder="e.g. nuts, lactose" /></label><label>Favorite cuisines <span className="label-hint">comma separated</span><input value={cuisineText} onChange={event => setCuisineText(event.target.value)} placeholder="e.g. Indian, Mediterranean" /></label><label>Budget / day <span className="label-hint">optional</span><input name="budget_per_day" type="number" min="0" value={form.budget_per_day ?? ''} onChange={update} placeholder="e.g. 350" /></label><label>Timeline (weeks) <span className="label-hint">optional</span><input name="timeline_weeks" type="number" min="1" max="104" value={form.timeline_weeks ?? ''} onChange={update} placeholder="e.g. 8" /></label></div></div><div className="form-section form-section-last"><div className="form-section-title"><span className="section-number">03</span><div><h2>Optional profile image</h2><p>Stored locally in this demo as an object-storage simulation.</p></div></div><label className="upload-drop"><span className="upload-icon">↥</span><span><strong>{upload ? 'Uploading…' : 'Choose an image'}</strong><small>PNG, JPG, WEBP or GIF · 3 MB max</small></span><input type="file" accept="image/png,image/jpeg,image/webp,image/gif" onChange={handleUpload} disabled={upload} /></label></div><div className="form-actions"><span className="form-footnote">Educational demo only · no medical diagnosis</span><button className="button button-primary" disabled={busy}>{busy ? 'Saving…' : 'Save profile →'}</button></div></form></>;
}

function PlanPage() {
  const [dashboard, setDashboard] = useState(null); const [plans, setPlans] = useState([]); const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  async function load() { try { const [dash, history] = await Promise.all([api.getDashboard(), api.getPlans()]); setDashboard(dash); setPlans(history.plans); } catch (err) { setError(err.message); } }
  useEffect(() => { load(); }, []);
  async function generate() { setBusy(true); setError(''); try { await api.createPlan(dashboard.targets); await load(); } catch (err) { setError(err.message); } finally { setBusy(false); } }
  if (error) return <Notice tone="error">{error}</Notice>;
  if (!dashboard) return <LoadingScreen />;
  const plan = dashboard.current_plan;
  return <><PageHeader eyebrow="AI-assisted planning" title="Your meal plan" description="A deterministic recommendation engine turns your profile into an approachable day of meals." action={<button className="button button-primary" onClick={generate} disabled={busy || !dashboard.profile}>{busy ? 'Building…' : plan ? 'Refresh plan ↻' : 'Generate plan →'}</button>} />{!dashboard.profile && <Notice tone="info">Complete your profile before generating a plan.</Notice>}{plan && <><div className="plan-banner"><div><span className="eyebrow">Rule-based fallback engine</span><h2>{plan.title}</h2><p>{plan.hydration}</p></div><div className="plan-total"><strong>{formatCalories(plan.totals.kcal)}</strong><small>approximate daily total</small></div></div><Notice tone="info"><strong>Wellness example:</strong> {plan.disclaimer}</Notice><div className="meal-grid meal-grid-large">{plan.meals.map(meal => <MealCard key={meal.id} meal={meal} />)}</div></>}{plans.length > 0 && <section className="section-block"><div className="section-heading"><div><span className="eyebrow">Saved history</span><h2>Recent plans</h2></div><span className="history-count">{plans.length} saved</span></div><div className="history-list">{plans.map(item => <div className="history-row" key={item.id}><span className="history-date">{relativeDate(item.created_at)}</span><strong>{item.title}</strong><span>{formatCalories(item.totals.kcal)}</span><span className="history-tag">{item.source === 'rule_based_fallback' ? 'Fallback engine' : 'AI generated'}</span></div>)}</div></section>}</>;
}

function TrackerPage() {
  const today = new Date().toISOString().slice(0, 10); const [foods, setFoods] = useState([]); const [intake, setIntake] = useState(null); const [dashboard, setDashboard] = useState(null); const [form, setForm] = useState({ food_id: '', grams: 100 }); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  async function load() { try { const [foodData, intakeData, dash] = await Promise.all([api.getFoods(), api.getIntake(today), api.getDashboard()]); setFoods(foodData.foods); setIntake(intakeData); setDashboard(dash); setForm(current => ({ ...current, food_id: current.food_id || foodData.foods[0]?.id || '' })); } catch (err) { setError(err.message); } }
  useEffect(() => { load(); }, []);
  async function add(event) { event.preventDefault(); setBusy(true); setError(''); try { await api.addIntake({ ...form, grams: Number(form.grams), date: today }); await load(); } catch (err) { setError(err.message); } finally { setBusy(false); } }
  async function remove(id) { try { await api.deleteIntake(id); await load(); } catch (err) { setError(err.message); } }
  if (error) return <Notice tone="error">{error}</Notice>;
  if (!intake || !dashboard) return <LoadingScreen />;
  const targets = dashboard.targets;
  return <><PageHeader eyebrow="Daily tracker" title="Make it visible" description="Log a few items and see how your day is adding up. Approximate is enough for this demo." /><div className="tracker-layout"><section className="panel tracker-add"><div className="panel-head"><div><span className="eyebrow">Quick add</span><h2>Log a food</h2></div><span className="date-badge">{new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(new Date())}</span></div><form className="form-stack" onSubmit={add}><label>Food<select value={form.food_id} onChange={event => setForm({ ...form, food_id: event.target.value })}>{foods.map(food => <option value={food.id} key={food.id}>{food.name}</option>)}</select></label><label>Amount (grams)<input type="number" min="1" max="1000" value={form.grams} onChange={event => setForm({ ...form, grams: event.target.value })} /></label><button className="button button-primary button-wide" disabled={busy}>{busy ? 'Adding…' : 'Add to today →'}</button></form><div className="tracker-tip"><span>✦</span><p>Keep the feedback loop simple: one entry is already useful.</p></div></section><section className="panel intake-panel"><div className="panel-head"><div><span className="eyebrow">{intake.date}</span><h2>Today’s log</h2></div><strong className="intake-total">{formatCalories(intake.totals.kcal)}</strong></div>{targets && <div className="tracker-summary"><MacroBar label="Calories" current={intake.totals.kcal} target={targets.calories} color="green" /></div>}{intake.entries.length === 0 ? <div className="empty-block"><span className="empty-icon">⌁</span><h3>Nothing logged yet</h3><p>Add a food to start your daily picture.</p></div> : <ul className="intake-list">{intake.entries.map(entry => <li key={entry.id}><div><strong>{entry.food_name}</strong><small>{Math.round(entry.grams)}g · P {Math.round(entry.protein)}g · C {Math.round(entry.carbs)}g · F {Math.round(entry.fat)}g</small></div><span>{formatCalories(entry.kcal)}</span><button className="icon-button" onClick={() => remove(entry.id)} aria-label={`Remove ${entry.food_name}`}>×</button></li>)}</ul>}</section></div></>;
}

function LandingPage() {
  const { user } = useAuth();
  if (user) return <Navigate to="/dashboard" replace />;
  return <div className="landing"><BrandMark /><div className="landing-hero"><div><span className="eyebrow">Cloud-ready wellness planning</span><h1>Make room for the meals that make your day work.</h1><p>Dietly turns a few everyday inputs into a clear plan, a trackable rhythm, and a better view of your progress.</p><div className="landing-actions"><Link className="button button-primary" to="/register">Create your workspace →</Link><Link className="button button-quiet" to="/login">Use demo login</Link></div></div><div className="hero-orbit"><img src="/logo.svg" alt="Dietly plate and leaf" /><div className="orbit-card orbit-card-top"><span>Daily target</span><strong>1,840 kcal</strong><small>approximate</small></div><div className="orbit-card orbit-card-bottom"><span>Today’s rhythm</span><strong>3 / 4 meals</strong><small>looking steady</small></div></div></div><div className="landing-foot"><span>Profile</span><b>→</b><span>Plan</span><b>→</b><span>Track</span><b>→</b><span>Learn</span></div></div>;
}

function Protected({ children }) {
  const { user, loading } = useAuth(); const location = useLocation();
  if (loading) return <LoadingScreen />;
  return user ? <AppShell>{children}</AppShell> : <Navigate to="/login" state={{ from: location }} replace />;
}

export default function App() {
  const [user, setUser] = useState(null); const [loading, setLoading] = useState(true);
  useEffect(() => { api.me().then(data => setUser(data.user)).catch(() => setUser(null)).finally(() => setLoading(false)); }, []);
  const auth = useMemo(() => ({ user, loading, login: async (body) => { const data = await api.login(body); setUser(data.user); }, register: async (body) => { const data = await api.register(body); setUser(data.user); }, logout: async () => { await api.logout(); setUser(null); }, refresh: async () => { const data = await api.me(); setUser(data.user); } }), [user, loading]);
  if (loading) return <LoadingScreen />;
  return <AuthContext.Provider value={auth}><Routes><Route path="/" element={<LandingPage />} /><Route path="/login" element={<AuthPage mode="login" />} /><Route path="/register" element={<AuthPage mode="register" />} /><Route path="/dashboard" element={<Protected><DashboardPage /></Protected>} /><Route path="/profile" element={<Protected><ProfilePage /></Protected>} /><Route path="/plan" element={<Protected><PlanPage /></Protected>} /><Route path="/tracker" element={<Protected><TrackerPage /></Protected>} /><Route path="*" element={<Navigate to="/" replace />} /></Routes></AuthContext.Provider>;
}

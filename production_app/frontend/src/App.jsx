import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Plane, Train, Bus, DollarSign, Clock, Star, AlertCircle, Settings2 } from 'lucide-react';

const App = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState(null);
  const [activeTab, setActiveTab] = useState('recommended');
  const [overrideBudget, setOverrideBudget] = useState(15000);
  const [showFilters, setShowFilters] = useState(false);

  // Sync override budget with initial plan results
  useEffect(() => {
    if (plan && !loading && plan.budget) {
      setOverrideBudget(plan.budget);
    }
  }, [plan]);

  const handleSearch = async (e, customQuery = null) => {
    if (e) e.preventDefault();
    const q = customQuery || query;
    if (!q.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/plan', { query: q });
      setPlan(response.data);
    } catch (error) {
      console.error('Search error:', error);
      alert('Search failed. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleBudgetChange = (newVal) => {
    setOverrideBudget(newVal);
    // Construct a specialized query to force Gemini to use the new budget with SAME cities
    const refinedQuery = `Plan a trip from ${plan.origin} to ${plan.destination} under ₹${newVal}`;
    handleSearch(null, refinedQuery);
  };

  const getFilteredOptions = () => {
    if (!plan || !plan.transport_options) return [];
    
    let opts = [...plan.transport_options];
    if (activeTab === 'cheapest') {
      return opts.sort((a, b) => a.price - b.price);
    }
    if (activeTab === 'fastest') {
      return opts.sort((a, b) => a.time_hours - b.time_hours);
    }
    return opts.sort((a, b) => b.final_score - a.final_score);
  };

  const renderModeIcon = (mode) => {
    const m = mode.toLowerCase();
    if (m.includes('flight')) return <Plane className="w-6 h-6 text-blue-500" />;
    if (m.includes('train')) return <Train className="w-6 h-6 text-green-600" />;
    if (m.includes('bus')) return <Bus className="w-6 h-6 text-orange-500" />;
    return <Bus className="w-6 h-6 text-gray-400" />;
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center">
      {/* Header / Search Section */}
      <header className="w-full bg-brand-blue py-12 flex flex-col items-center px-4 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
          <div className="absolute top-10 left-10 w-64 h-64 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-blue-300 rounded-full blur-3xl"></div>
        </div>
        
        <h1 className="text-white text-5xl font-black mb-10 tracking-tighter drop-shadow-md">AI Travel Concierge</h1>
        
        <div className="w-full max-w-3xl flex flex-col gap-4">
          <form onSubmit={handleSearch} className="relative group">
            <input
              type="text"
              className="w-full pl-8 pr-20 py-6 rounded-3xl border-none focus:ring-4 focus:ring-blue-400 text-xl shadow-2xl text-gray-800 transition-all placeholder:text-gray-400"
              placeholder="Ex: From Delhi to Goa under ₹15000"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button
              type="submit"
              disabled={loading}
              className="absolute right-4 top-1/2 -translate-y-1/2 p-4 bg-brand-orange text-white rounded-2xl hover:bg-red-600 transition-all shadow-lg active:scale-95 disabled:bg-gray-400"
            >
              {loading ? <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-white"></div> : <Search className="w-7 h-7" />}
            </button>
          </form>

          {plan && !plan.error && (
            <div className="bg-white/10 backdrop-blur-md p-6 rounded-3xl border border-white/20 flex flex-col md:flex-row items-center justify-between gap-6 animate-in slide-in-from-top-4">
              <div className="flex items-center gap-4 text-white">
                <Settings2 className="w-6 h-6 opacity-70" />
                <span className="font-bold text-lg">Adjust Budget:</span>
              </div>
              <div className="flex-grow flex items-center gap-6 px-4">
                <span className="text-white font-black text-xl min-w-[100px]">₹{overrideBudget.toLocaleString()}</span>
                <input 
                  type="range" 
                  min="2000" 
                  max="100000" 
                  step="1000"
                  value={overrideBudget}
                  onChange={(e) => setOverrideBudget(parseInt(e.target.value))}
                  onMouseUp={() => handleBudgetChange(overrideBudget)}
                  onTouchEnd={() => handleBudgetChange(overrideBudget)}
                  className="flex-grow h-3 bg-white/20 rounded-lg appearance-none cursor-pointer accent-brand-orange"
                />
              </div>
              <div className="text-white/60 text-sm italic">Recalculating live...</div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="w-full max-w-6xl px-4 py-16 flex flex-col gap-12">
        {plan && !plan.error && (
          <>
            <section className="bg-white p-10 rounded-[40px] shadow-2xl border border-gray-100 animate-in fade-in slide-in-from-bottom-8">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-8 mb-12">
                <div>
                  <div className="text-brand-orange font-black uppercase tracking-[0.2em] text-sm mb-3">Optimal Route Found</div>
                  <h2 className="text-5xl font-black text-gray-900 leading-none">{plan.origin} <span className="text-gray-300 mx-2">→</span> {plan.destination}</h2>
                  <p className="text-gray-400 font-bold mt-4 text-lg">Geo-Distance: {plan.distance_km} km</p>
                </div>
                <div className="flex flex-col items-end gap-2 text-right">
                    <div className="text-gray-400 font-bold uppercase text-xs tracking-widest">Pricing Model</div>
                    <div className="px-8 py-4 bg-brand-blue/5 text-brand-blue rounded-3xl font-black text-2xl border border-brand-blue/10">
                    ₹{plan.budget.toLocaleString()} Cap
                    </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex gap-3 p-2 bg-gray-50 rounded-[2rem] mb-10 w-fit border border-gray-100">
                {['recommended', 'cheapest', 'fastest'].map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-10 py-4 rounded-[1.5rem] transition-all font-black text-sm uppercase tracking-widest ${activeTab === tab ? 'bg-white text-brand-blue shadow-xl scale-105 brightness-105' : 'text-gray-400 hover:text-gray-600'}`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Transport Cards Grid */}
              <div className="grid gap-8">
                {getFilteredOptions().map((opt, idx) => (
                  <div key={idx} className={`relative p-10 rounded-[2.5rem] border-4 transition-all hover:scale-[1.01] hover:shadow-2xl flex flex-col md:flex-row items-center gap-10 ${idx === 0 ? 'border-brand-blue bg-blue-50/30' : 'border-gray-50 bg-white'}`}>
                    {opt.label && (
                      <span className="absolute -top-5 left-10 px-6 py-3 bg-brand-blue text-white text-xs font-black uppercase tracking-tighter rounded-2xl shadow-2xl border-2 border-white">
                        {opt.label}
                      </span>
                    )}
                    <div className="p-8 bg-white rounded-[2rem] shadow-xl border border-gray-100 shrink-0 transform group-hover:rotate-6 transition-transform">
                      {renderModeIcon(opt.mode)}
                    </div>
                    <div className="flex-grow text-center md:text-left">
                      <h3 className="text-3xl font-black text-gray-900 mb-2">{opt.mode}</h3>
                      <div className="flex items-center justify-center md:justify-start gap-4">
                        <span className="flex items-center gap-2 text-gray-500 font-bold text-lg">
                            <Clock className="w-5 h-5 text-brand-orange" /> {opt.time_hours}h
                        </span>
                        <div className="h-4 w-1 bg-gray-200 rounded-full"></div>
                        <span className="text-brand-blue font-black tracking-tight">Optimized Path</span>
                      </div>
                    </div>
                    <div className="flex flex-col items-center md:items-end gap-4 shrink-0">
                      <div className="text-5xl font-black text-brand-blue tracking-tighter">₹{opt.price.toLocaleString()}</div>
                      <div className="flex items-center gap-2 px-6 py-2.5 bg-yellow-400 text-white rounded-2xl text-sm font-black shadow-lg">
                        <Star className="w-4 h-4 fill-white" /> {opt.final_score} <span className="opacity-70 font-bold">MATCH</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Hotels Section */}
            <section className="animate-in fade-in slide-in-from-bottom-12 delay-300">
              <div className="flex items-center justify-between mb-12 px-4">
                <h3 className="text-4xl font-black text-gray-900 flex items-center gap-5">
                    <div className="w-3 h-12 bg-brand-orange rounded-full shadow-lg shadow-brand-orange/20"></div>
                    Curated Stays
                </h3>
                <div className="h-[2px] flex-grow mx-10 bg-gray-100 rounded-full"></div>
              </div>
              
              <div className="grid lg:grid-cols-2 gap-10">
                {plan.hotels.map((h, i) => (
                  <div key={i} className="bg-white p-10 rounded-[3rem] shadow-xl hover:shadow-[0_30px_60px_-15px_rgba(0,0,0,0.15)] transition-all border border-gray-100 group flex flex-col justify-between overflow-hidden relative">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-gray-50 -mr-16 -mt-16 rounded-full group-hover:bg-blue-50 transition-colors"></div>
                    <div>
                      <div className="flex justify-between items-start mb-8 relative z-10">
                        <h4 className="text-3xl font-black text-gray-900 leading-tight group-hover:text-brand-blue transition-colors max-w-[70%]">{h.name}</h4>
                        <span className="px-5 py-2.5 bg-gray-900 text-white text-[10px] font-black rounded-2xl uppercase tracking-[0.2em] shadow-lg">{h.category}</span>
                      </div>
                      <div className="flex items-baseline gap-3 mb-4">
                        <span className="text-4xl font-black text-gray-900 tracking-tighter">₹{h.price_per_night.toLocaleString()}</span>
                        <span className="text-gray-400 font-bold text-lg uppercase text-xs tracking-widest">per night</span>
                      </div>
                    </div>
                    <button className="mt-10 w-full py-5 bg-slate-100 text-slate-800 font-black rounded-[1.5rem] hover:bg-brand-blue hover:text-white transition-all active:scale-95 text-sm uppercase tracking-widest shadow-inner">
                      Select This Stay
                    </button>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}

        {plan && plan.error && (
          <div className="bg-red-50 border-4 border-red-100 p-12 rounded-[3rem] flex items-center gap-10 text-red-800 shadow-2xl animate-bounce">
            <AlertCircle className="w-16 h-16 flex-shrink-0 text-red-500" />
            <div>
                <h3 className="text-2xl font-black mb-2 uppercase tracking-tight">Extraction Error</h3>
                <p className="text-lg font-medium opacity-80">{plan.error}</p>
            </div>
          </div>
        )}

        {!plan && !loading && (
          <div className="flex flex-col items-center py-32 opacity-20">
            <div className="relative mb-12">
              <div className="absolute inset-0 bg-blue-400 blur-[100px] opacity-30 animate-pulse"></div>
              <Plane className="w-48 h-48 text-gray-400 relative z-10 animate-bounce" />
            </div>
            <p className="text-3xl font-black text-gray-400 tracking-tighter">Where shall we take you today?</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="w-full py-20 text-center text-gray-400 text-xs font-black uppercase tracking-[0.5em] border-t border-gray-100 bg-white mt-auto">
        &copy; 2026 Antigravity Travel Engine • Production V1.0
      </footer>
    </div>
  );
};

export default App;

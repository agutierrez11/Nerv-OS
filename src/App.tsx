import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, Search, Activity, Cpu, Database, 
  ChevronRight, AlertTriangle, FileText, 
  Target, Globe, Lock, Unlock, Beaker, Zap, 
  BrainCircuit, Save, Send, Layers, Briefcase
} from 'lucide-react';
import axios from 'axios';

const COMPANIES_DATA = [
  {"sector": "Ecommerce", "empresa": "Under Armour", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "Nike", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "Adidas", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "AutoZone", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "InnovaSport", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "Grupo Martí", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "Ben&Frank", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "Pandora", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "Decathlon", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "Samsung Electronics", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "Justo", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "Luuna", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "Omnilife", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "Platanomelon", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Ecommerce", "empresa": "HoliHerb", "pitch_principal": "Orquestación de Pagos + Recurrencia"},
  {"sector": "Goods", "empresa": "Coca Cola Femsa", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "Arca Continental", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "Bepensa", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "Danone", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "Alpura", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "Grupo Lala", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "La Costeña", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "Grupo KUO", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "Kimberly Clark de Mexico", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "Nestlé", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "Grupo El Zorro", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "Productos de Consumo Z", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "Grupo Scorpion", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "Comex", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Goods", "empresa": "3M México", "pitch_principal": "Digitalización de Cobranza + BNPL"},
  {"sector": "Health", "empresa": "Salud Digna", "pitch_principal": "Discovery de Pagos"},
  {"sector": "Health", "empresa": "Hospital Angeles", "pitch_principal": "Discovery de Pagos"},
  {"sector": "Health", "empresa": "Hospital ABC", "pitch_principal": "Discovery de Pagos"},
  {"sector": "Health", "empresa": "CHOPO", "pitch_principal": "Discovery de Pagos"},
  {"sector": "Health", "empresa": "Hospital Español", "pitch_principal": "Discovery de Pagos"},
  {"sector": "Health", "empresa": "TecSalud", "pitch_principal": "Discovery de Pagos"},
  {"sector": "Otros", "empresa": "Estafeta", "pitch_principal": "Discovery de Pagos"},
  {"sector": "Otros", "empresa": "DHL Mexico", "pitch_principal": "Discovery de Pagos"},
  {"sector": "Otros", "empresa": "FedEx Mexico", "pitch_principal": "Discovery de Pagos"},
  {"sector": "Otros", "empresa": "UPS Mexico", "pitch_principal": "Discovery de Pagos"},
  {"sector": "Otros", "empresa": "Paquetexpress", "pitch_principal": "Discovery de Pagos"}
];

const App = () => {
  const [activeTab, setActiveTab] = useState('lab');
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [password, setPassword] = useState('');
  const [showPrompt, setShowPrompt] = useState(false);
  const [pendingTab, setPendingTab] = useState<string | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [intelLoading, setIntelLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [companies, setCompanies] = useState<any[]>(COMPANIES_DATA);
  
  // Form State para LAB (Agnóstico)
  const [labData, setLabData] = useState({
    vendedor_url: '',
    producto: '',
    prospecto_url: '',
    empresa: '',
    objeciones: ''
  });

  // Form State para TARGET (Toku/Protected)
  const [targetData, setTargetData] = useState({
    empresa: '',
    sector: 'Fintech',
    pitch: 'Soluciones de pago B2B'
  });

  // Form State para INTEL INJECTION
  const [intelData, setIntelData] = useState({
    company: '',
    sector: 'Fintech',
    content: '',
    type: 'objection' // objection or value_prop
  });

  const [systemStatus, setSystemStatus] = useState<any>(null);

  const checkHealth = async () => {
    try {
      const res = await axios.get('/api/health');
      setSystemStatus(res.data.keys_detected);
    } catch (e) {
      console.error("Health check failed");
    }
  };

  useEffect(() => {
    fetchCompanies();
    checkHealth();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await axios.get('/api/companies');
      if (response.data.success) {
        setCompanies(response.data.data);
      }
    } catch (error) {
      console.error("Error fetching companies:", error);
    }
  };

  const handleTabChange = (tabId: string) => {
    if (tabId === 'lab') {
      setShowPrompt(false);
      setPendingTab(null);
      setActiveTab(tabId);
    } else if (isAuthorized) {
      setActiveTab(tabId);
    } else {
      setPendingTab(tabId);
      setShowPrompt(true);
    }
  };

  const checkPassword = () => {
    if (password === 'Toku1') {
      setIsAuthorized(true);
      setShowPrompt(false);
      if (pendingTab) setActiveTab(pendingTab);
    } else {
      alert("ACCESO DENEGADO: CREDENCIALES INVÁLIDAS");
      setPassword('');
    }
  };

  const runLabAnalysis = async () => {
    setLoading(true);
    try {
      const full_pitch = `Vendedor: ${labData.vendedor_url} | Producto: ${labData.producto}`;
      const response = await axios.post('/api/analyze', {
        empresa: labData.empresa,
        sector: "General",
        pitch: full_pitch,
        context: labData.objeciones
      });
      setResult(response.data.data);
    } catch (error) {
      setResult("### ERROR: SIGNALS_LOST\nNeural link failure.");
    } finally {
      setLoading(false);
    }
  };

  const runTargetAnalysis = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/analyze', targetData);
      setResult(response.data.data);
    } catch (error) {
      setResult("### ERROR: SIGNALS_LOST\nMAGI nodes offline.");
    } finally {
      setLoading(false);
    }
  };

  const saveIntel = async () => {
    setIntelLoading(true);
    try {
      await axios.post('/api/save-intelligence', intelData);
      alert("INTELIGENCIA REGISTRADA EXITOSAMENTE");
      setIntelData({ ...intelData, content: '' });
    } catch (error) {
      alert("ERROR AL GUARDAR INTELIGENCIA");
    } finally {
      setIntelLoading(false);
    }
  };

  const selectCompany = (c: any) => {
    setTargetData({
      empresa: c.empresa,
      sector: c.sector,
      pitch: c.pitch_principal
    });
    setActiveTab('target');
  };

  return (
    <div className="min-h-screen w-full bg-[#050608] text-white p-4 md:p-6 overflow-hidden relative font-sans">
      {/* Grid Pattern Background */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none" 
           style={{ backgroundImage: 'linear-gradient(#3b82f6 1px, transparent 1px), linear-gradient(90deg, #3b82f6 1px, transparent 1px)', backgroundSize: '50px 50px' }}>
      </div>

      <header className="relative z-10 flex flex-col md:flex-row justify-between items-center border-b border-blue-900/30 pb-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-blue-600 rounded-lg shadow-[0_0_20px_rgba(59,130,246,0.3)]">
            <Cpu size={28} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-white italic uppercase">NERV.<span className="text-blue-500">IOS</span></h1>
            <p className="text-[9px] text-blue-400 font-bold uppercase tracking-[0.4em]">Intelligent Operating System</p>
          </div>
        </div>

        <nav className="flex bg-blue-950/20 p-1 border border-blue-900/20 rounded-xl mt-4 md:mt-0">
          {[
            { id: 'lab', label: 'NERV.IOS', icon: <Cpu size={14}/>, protected: false },
            { id: 'target', label: 'TARGET SCAN', icon: <Target size={14}/>, protected: true },
            { id: 'intel', label: 'INTEL HUB', icon: <Globe size={14}/>, protected: true }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`flex items-center gap-2 px-6 py-2.5 text-[10px] font-black uppercase tracking-widest transition-all rounded-lg relative
                ${activeTab === tab.id ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400 hover:text-white hover:bg-blue-900/20'}`}
            >
              {tab.icon} {tab.label}
              {tab.protected && !isAuthorized && <Lock size={10} className="ml-1 opacity-50" />}
            </button>
          ))}
        </nav>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto h-[calc(100vh-140px)]">
        <AnimatePresence mode="wait">
          {showPrompt ? (
            <motion.div 
              key="prompt" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="h-full flex items-center justify-center"
            >
              <div className="max-w-sm w-full p-10 border border-blue-900/30 bg-blue-950/5 backdrop-blur-xl rounded-3xl text-center shadow-2xl">
                <div className="w-20 h-20 bg-blue-600/20 rounded-full flex items-center justify-center mx-auto mb-8">
                  <Lock size={32} className="text-blue-500 animate-pulse" />
                </div>
                <h3 className="text-xs font-black uppercase tracking-[0.4em] mb-8 text-blue-400">Restricted Data Access</h3>
                <input 
                  type="password" autoFocus placeholder="AUTHORIZATION KEY"
                  className="w-full bg-black/50 border border-blue-900/50 p-4 rounded-xl text-center text-blue-400 font-mono focus:outline-none focus:border-blue-500 mb-6"
                  value={password} onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && checkPassword()}
                />
                <button onClick={checkPassword} className="w-full py-4 bg-blue-600 text-white rounded-xl text-[10px] font-black uppercase tracking-[0.2em] hover:bg-blue-500 transition-colors">
                  Authenticate Session
                </button>
              </div>
            </motion.div>
          ) : activeTab === 'lab' ? (
            <motion.div key="lab" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-full">
              <div className="lg:col-span-1 space-y-6 overflow-y-auto pr-2 custom-scrollbar">
                <div className="p-6 bg-blue-950/5 border border-blue-900/20 rounded-2xl">
                  <h2 className="text-[10px] font-black uppercase tracking-[0.3em] text-blue-500 mb-8 flex items-center gap-2">
                    <Cpu size={16} className="text-blue-400"/> NERV.IOS INTELLIGENT OS
                  </h2>
                  <div className="space-y-5">
                    <div>
                      <label className="block text-[8px] uppercase text-blue-400 mb-2 font-black tracking-widest">Seller URL (Competitor/Yourself)</label>
                      <input type="text" className="w-full bg-blue-900/10 border-2 border-blue-500/40 p-4 rounded-xl text-xs font-mono focus:border-blue-400 focus:ring-1 focus:ring-blue-400 outline-none transition-all placeholder:text-blue-900/40" 
                        placeholder="https://..." value={labData.vendedor_url} onChange={e => setLabData({...labData, vendedor_url: e.target.value})} />
                    </div>
                    <div>
                      <label className="block text-[8px] uppercase text-blue-400 mb-2 font-black tracking-widest">Target Product/Value Prop</label>
                      <input type="text" className="w-full bg-blue-900/10 border-2 border-blue-500/40 p-4 rounded-xl text-xs font-mono focus:border-blue-400 focus:ring-1 focus:ring-blue-400 outline-none transition-all"
                        placeholder="AI reconciliation..." value={labData.producto} onChange={e => setLabData({...labData, producto: e.target.value})} />
                    </div>
                    <div className="pt-4 border-t border-blue-900/20">
                      <label className="block text-[8px] uppercase text-blue-400 mb-2 font-black tracking-widest">Prospect Name</label>
                      <input type="text" className="w-full bg-blue-900/10 border-2 border-blue-500/40 p-4 rounded-xl text-xs font-mono focus:border-blue-400 focus:ring-1 focus:ring-blue-400 outline-none transition-all"
                        placeholder="Company name..." value={labData.empresa} onChange={e => setLabData({...labData, empresa: e.target.value})} />
                    </div>
                    <div>
                      <label className="block text-[8px] uppercase text-blue-400 mb-2 font-black tracking-widest">Objections / Context</label>
                      <textarea rows={4} className="w-full bg-blue-900/10 border-2 border-blue-500/40 p-4 rounded-xl text-xs font-mono focus:border-blue-400 focus:ring-1 focus:ring-blue-400 outline-none transition-all"
                        placeholder="Enter context..." value={labData.objeciones} onChange={e => setLabData({...labData, objeciones: e.target.value})} />
                    </div>
                    <button onClick={runLabAnalysis} className="w-full py-4 bg-blue-600 text-white rounded-xl font-black text-[10px] uppercase tracking-widest hover:bg-blue-500 transition-all shadow-xl shadow-blue-900/20">
                      {loading ? 'Initializing Neural Swarm...' : 'Generate Competitive Analysis'}
                    </button>
                  </div>
                </div>

                {/* System Health Card */}
                <div className="p-6 bg-blue-950/10 border border-blue-500/20 rounded-2xl">
                  <h3 className="text-[8px] font-black uppercase tracking-[0.2em] text-blue-400 mb-4">Neural Link Status</h3>
                  <div className="grid grid-cols-2 gap-3">
                    {systemStatus ? Object.entries(systemStatus).map(([key, ok]) => (
                      <div key={key} className="flex items-center gap-2 bg-black/40 p-2 rounded-lg border border-white/5">
                        <div className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-red-500 animate-pulse'}`} />
                        <span className="text-[9px] font-mono text-gray-400">{key}</span>
                      </div>
                    )) : (
                      <div className="col-span-2 text-[9px] text-gray-500 italic">Diagnosing system...</div>
                    )}
                  </div>
                </div>
              </div>
              <div className="lg:col-span-2 bg-black/40 border border-blue-900/20 rounded-2xl p-8 overflow-y-auto custom-scrollbar backdrop-blur-sm">
                {loading ? (
                  <div className="h-full flex flex-col items-center justify-center gap-6 text-blue-500">
                    <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }} className="w-16 h-16 border-2 border-blue-500 border-t-transparent rounded-full shadow-[0_0_30px_rgba(59,130,246,0.2)]" />
                    <p className="text-[10px] font-mono tracking-[0.5em] animate-pulse">SYNCHRONIZING MAGI NODES...</p>
                  </div>
                ) : result ? (
                  <div className="prose prose-invert max-w-none">
                    <pre className="whitespace-pre-wrap text-[12px] font-mono text-blue-50 leading-relaxed bg-blue-950/10 p-6 rounded-xl border border-blue-900/20">{result}</pre>
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-blue-900/30">
                    <BrainCircuit size={80} />
                    <p className="text-[10px] font-black uppercase mt-6 tracking-[0.3em]">System Standby</p>
                  </div>
                )}
              </div>
            </motion.div>
          ) : activeTab === 'target' ? (
            <motion.div key="target" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 lg:grid-cols-3 gap-8 h-full">
              <div className="lg:col-span-1 space-y-6">
                <div className="p-8 bg-blue-950/10 border border-blue-900/30 rounded-3xl shadow-[0_0_40px_rgba(59,130,246,0.05)]">
                  <h3 className="text-xs font-black text-blue-400 uppercase tracking-[0.4em] mb-8">Forensic Scan config</h3>
                  <div className="space-y-5">
                    <input type="text" placeholder="COMPANY NAME" className="w-full bg-blue-950/20 border-2 border-blue-500/40 p-4 rounded-xl text-xs font-mono outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 transition-all"
                      value={targetData.empresa} onChange={e => setTargetData({...targetData, empresa: e.target.value})} />
                    <input type="text" placeholder="SECTOR" className="w-full bg-blue-950/20 border-2 border-blue-500/40 p-4 rounded-xl text-xs font-mono outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 transition-all"
                      value={targetData.sector} onChange={e => setTargetData({...targetData, sector: e.target.value})} />
                    <textarea rows={6} placeholder="STRATEGIC PITCH" className="w-full bg-blue-950/20 border-2 border-blue-500/40 p-4 rounded-xl text-xs font-mono outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 transition-all"
                      value={targetData.pitch} onChange={e => setTargetData({...targetData, pitch: e.target.value})} />
                    <button onClick={runTargetAnalysis} className="w-full py-5 bg-blue-600 text-white rounded-xl font-black text-[10px] uppercase tracking-widest shadow-xl shadow-blue-900/20 hover:bg-blue-500 transition-colors">
                      {loading ? 'Scanning...' : 'Execute Target Analysis'}
                    </button>
                  </div>
                </div>
              </div>
              <div className="lg:col-span-2 bg-black/40 border border-blue-900/20 rounded-3xl p-8 overflow-y-auto custom-scrollbar">
                <pre className="whitespace-pre-wrap text-[11px] font-mono text-gray-300 leading-relaxed">{result || 'READY FOR TARGET ACQUISITION...'}</pre>
              </div>
            </motion.div>
          ) : (
            <motion.div key="intel" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 lg:grid-cols-2 gap-10 h-full overflow-hidden">
              {/* Intelligence Injection */}
              <div className="flex flex-col gap-6">
                <div className="p-8 border border-blue-900/20 bg-blue-950/5 rounded-3xl relative overflow-hidden backdrop-blur-md">
                  <div className="absolute top-0 right-0 p-6 opacity-10">
                    <Layers size={50} className="text-blue-500" />
                  </div>
                  <h3 className="text-xs font-black uppercase tracking-[0.4em] text-blue-400 mb-8 flex items-center gap-3">
                    <BrainCircuit size={18} className="text-blue-500"/> Intelligence Injection
                  </h3>
                  <div className="space-y-5">
                    <div className="grid grid-cols-2 gap-4">
                      <input type="text" placeholder="COMPANY/SECTOR" className="bg-blue-950/20 border-2 border-blue-500/40 p-3 rounded-xl text-[10px] font-mono outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 transition-all"
                        value={intelData.company} onChange={e => setIntelData({...intelData, company: e.target.value})} />
                      <select className="bg-blue-950/20 border-2 border-blue-500/40 p-3 rounded-xl text-[10px] font-mono text-blue-400 outline-none focus:border-blue-400"
                        value={intelData.type} onChange={e => setIntelData({...intelData, type: e.target.value})}>
                        <option value="objection">SALES OBJECTION</option>
                        <option value="value_prop">ATTACK ANGLE</option>
                      </select>
                    </div>
                    <textarea rows={8} placeholder="PASTE REAL-WORLD OBJECTIONS OR WINNING SALES ARGUMENTS..." 
                      className="w-full bg-blue-950/20 border-2 border-blue-500/40 p-4 rounded-xl text-[11px] font-mono focus:border-blue-400 focus:ring-1 focus:ring-blue-400 outline-none leading-relaxed transition-all"
                      value={intelData.content} onChange={e => setIntelData({...intelData, content: e.target.value})} />
                    <button 
                      onClick={saveIntel}
                      disabled={intelLoading || !intelData.content}
                      className="w-full py-4 bg-blue-600 text-white rounded-xl font-black text-[10px] uppercase tracking-[0.2em] flex items-center justify-center gap-3 shadow-lg shadow-blue-900/20 hover:bg-blue-500"
                    >
                      {intelLoading ? <Activity size={16} className="animate-spin"/> : <Save size={16}/>}
                      {intelLoading ? 'SYNCING CORE...' : 'UPDATE NEURAL CORE'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Assets List (The 41 companies) */}
              <div className="flex flex-col h-full overflow-hidden">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xs font-black uppercase tracking-[0.3em] text-blue-400 flex items-center gap-2">
                    <Database size={16}/> Pipeline Assets ({companies.length})
                  </h2>
                  <div className="flex items-center gap-2 text-green-500 text-[10px] font-bold">
                    <Unlock size={12} /> SECURE LINK
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto pr-4 custom-scrollbar space-y-3 pb-10">
                  {companies.map((c, i) => (
                    <motion.div 
                      key={i} 
                      whileHover={{ x: 5 }}
                      onClick={() => selectCompany(c)}
                      className="p-5 border border-blue-900/10 bg-blue-950/5 hover:bg-blue-900/20 hover:border-blue-500/30 transition-all cursor-pointer group rounded-2xl"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <span className="px-2 py-0.5 bg-blue-600/10 text-blue-400 text-[7px] font-black rounded border border-blue-600/20 uppercase tracking-tighter">
                          {c.sector}
                        </span>
                        <ChevronRight size={14} className="text-blue-900 group-hover:text-blue-500 transition-colors" />
                      </div>
                      <h4 className="text-sm font-black tracking-tight group-hover:text-blue-400 transition-colors">{c.empresa}</h4>
                      <p className="text-[10px] text-gray-500 font-mono mt-2 line-clamp-1 italic">{c.pitch_principal}</p>
                    </motion.div>
                  ))}
                  {companies.length === 0 && (
                    <div className="text-center p-20 text-gray-700 italic text-[10px]">No assets found in current sector.</div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer className="fixed bottom-6 left-8 hidden md:flex items-center gap-6 text-[9px] font-mono text-gray-600 uppercase tracking-[0.4em]">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isAuthorized ? 'bg-green-500 animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.5)]' : 'bg-blue-900'}`}></div>
          <span>SESSION: {isAuthorized ? "AUTHORIZED" : "GUEST"}</span>
        </div>
        <span className="opacity-20 text-blue-500 font-bold">|</span>
        <span>NERV.IOS CORE v2.5</span>
        <span className="opacity-20 text-blue-500 font-bold">|</span>
        <Activity size={12} className="text-blue-500" />
      </footer>
    </div>
  );
};

export default App;

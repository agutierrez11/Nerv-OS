import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, Search, Activity, Cpu, Database, 
  ChevronRight, AlertTriangle, FileText, 
  Target, Globe, Lock, Unlock, Beaker, Zap
} from 'lucide-react';
import axios from 'axios';

const PRELOADED_COMPANIES = [
  { empresa: "Under Armour", sector: "Ecommerce", pitch: "Orquestación de Pagos + Recurrencia" },
  { empresa: "Nike", sector: "Ecommerce", pitch: "Orquestación de Pagos + Recurrencia" },
  { empresa: "Coca Cola Femsa", sector: "Goods", pitch: "Digitalización de Cobranza + BNPL" },
  { empresa: "Salud Digna", sector: "Health", pitch: "Discovery - Exploración de necesidades" }
];

const App = () => {
  const [activeTab, setActiveTab] = useState('lab');
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [password, setPassword] = useState('');
  const [showPrompt, setShowPrompt] = useState(false);
  const [pendingTab, setPendingTab] = useState<string | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  
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

  const handleTabChange = (tabId: string) => {
    if (tabId === 'lab') {
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
      // Usamos el mismo endpoint pero con la data del lab
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

  return (
    <div className="min-h-screen w-full bg-[#0a0a0a] text-white p-4 md:p-6 overflow-hidden relative font-sans">
      <div className="absolute inset-0 opacity-5 pointer-events-none" 
           style={{ backgroundImage: 'linear-gradient(#ff0000 1px, transparent 1px), linear-gradient(90deg, #ff0000 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
      </div>

      <header className="relative z-10 flex flex-col md:flex-row justify-between items-center border-b border-red-900/40 pb-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-red-600 rounded-sm">
            <Shield size={28} className="text-black" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tighter nerv-text-glow italic">NERV OS v2.0</h1>
            <p className="text-[9px] text-red-500 font-bold uppercase tracking-[0.3em]">Agnostic Intelligence Platform</p>
          </div>
        </div>

        <nav className="flex bg-red-950/20 p-1 border border-red-900/30 rounded mt-4 md:mt-0">
          {[
            { id: 'lab', label: 'NERV LAB', icon: <Beaker size={14}/>, protected: false },
            { id: 'target', label: 'TARGET SCAN', icon: <Target size={14}/>, protected: true },
            { id: 'intel', label: 'INTEL HUB', icon: <Globe size={14}/>, protected: true }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 text-[10px] font-bold uppercase tracking-widest transition-all relative
                ${activeTab === tab.id ? 'bg-red-600 text-black' : 'text-gray-400 hover:text-white'}`}
            >
              {tab.icon} {tab.label}
              {tab.protected && !isAuthorized && <Lock size={10} className="absolute top-1 right-1 opacity-50" />}
            </button>
          ))}
        </nav>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto h-[calc(100vh-140px)]">
        <AnimatePresence mode="wait">
          {showPrompt ? (
            <motion.div 
              key="prompt" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
              className="h-full flex items-center justify-center"
            >
              <div className="max-w-sm w-full p-8 border border-red-900/40 bg-red-950/10 backdrop-blur-md text-center">
                <Lock size={48} className="text-red-600 mx-auto mb-6 animate-pulse" />
                <h3 className="text-sm font-black uppercase tracking-[0.3em] mb-6">Security Clearance Required</h3>
                <input 
                  type="password" 
                  autoFocus
                  placeholder="ENTER ACCESS KEY"
                  className="w-full bg-black border border-red-900/50 p-4 text-center text-red-500 font-mono focus:outline-none focus:border-red-500 mb-4"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && checkPassword()}
                />
                <button 
                  onClick={checkPassword}
                  className="w-full py-3 bg-red-600 text-black text-[10px] font-black uppercase tracking-[0.2em]"
                >
                  Verify Identity
                </button>
              </div>
            </motion.div>
          ) : activeTab === 'lab' ? (
            <motion.div key="lab" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
              <div className="lg:col-span-1 space-y-4 overflow-y-auto pr-2 custom-scrollbar">
                <div className="p-5 bg-red-950/5 border border-red-900/30 rounded">
                  <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-red-500 mb-6 flex items-center gap-2">
                    <Zap size={14}/> Experiment Configuration
                  </h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-[8px] uppercase text-gray-500 mb-1">Seller Identity (Your URL)</label>
                      <input type="text" className="w-full bg-black border border-red-900/30 p-2 text-xs font-mono" 
                        value={labData.vendedor_url} onChange={e => setLabData({...labData, vendedor_url: e.target.value})} />
                    </div>
                    <div>
                      <label className="block text-[8px] uppercase text-gray-500 mb-1">Value Proposition (Product)</label>
                      <input type="text" className="w-full bg-black border border-red-900/30 p-2 text-xs font-mono"
                        value={labData.producto} onChange={e => setLabData({...labData, producto: e.target.value})} />
                    </div>
                    <div className="pt-4 border-t border-red-900/20">
                      <label className="block text-[8px] uppercase text-gray-500 mb-1">Target Entity Name</label>
                      <input type="text" className="w-full bg-black border border-red-900/30 p-2 text-xs font-mono"
                        value={labData.empresa} onChange={e => setLabData({...labData, empresa: e.target.value})} />
                    </div>
                    <div>
                      <label className="block text-[8px] uppercase text-gray-500 mb-1">Target URL</label>
                      <input type="text" className="w-full bg-black border border-red-900/30 p-2 text-xs font-mono"
                        value={labData.prospecto_url} onChange={e => setLabData({...labData, prospecto_url: e.target.value})} />
                    </div>
                    <div>
                      <label className="block text-[8px] uppercase text-gray-500 mb-1">Objections / Strategic Context</label>
                      <textarea rows={3} className="w-full bg-black border border-red-900/30 p-2 text-xs font-mono"
                        value={labData.objeciones} onChange={e => setLabData({...labData, objeciones: e.target.value})} />
                    </div>
                    <button onClick={runLabAnalysis} className="w-full py-4 bg-red-600 text-black font-black text-[10px] uppercase tracking-widest hover:bg-red-500 transition-all">
                      {loading ? 'Initializing Lab...' : 'Generate Competitive Match'}
                    </button>
                  </div>
                </div>
              </div>
              <div className="lg:col-span-2 bg-black border border-red-900/30 rounded p-6 overflow-y-auto custom-scrollbar">
                {loading ? (
                  <div className="h-full flex flex-col items-center justify-center gap-4 text-red-500">
                    <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }} className="w-12 h-12 border-2 border-red-600 border-t-transparent rounded-full" />
                    <p className="text-[10px] font-mono animate-pulse">CROSS-REFERENCING NEURAL SIGNALS...</p>
                  </div>
                ) : result ? (
                  <pre className="whitespace-pre-wrap text-[11px] font-mono text-gray-300 leading-relaxed">{result}</pre>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-gray-700 opacity-30">
                    <Beaker size={64} />
                    <p className="text-[10px] font-bold uppercase mt-4">Laboratory Idle</p>
                  </div>
                )}
              </div>
            </motion.div>
          ) : activeTab === 'target' ? (
            <motion.div key="target" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
              <div className="lg:col-span-1 space-y-4">
                <div className="p-6 bg-red-950/10 border border-red-900/50 rounded">
                  <h3 className="text-xs font-black text-red-600 uppercase tracking-widest mb-6">Target Identification</h3>
                  <div className="space-y-4">
                    <input type="text" placeholder="COMPANY NAME" className="w-full bg-black border border-red-900/30 p-3 text-xs font-mono"
                      value={targetData.empresa} onChange={e => setTargetData({...targetData, empresa: e.target.value})} />
                    <input type="text" placeholder="SECTOR" className="w-full bg-black border border-red-900/30 p-3 text-xs font-mono"
                      value={targetData.sector} onChange={e => setTargetData({...targetData, sector: e.target.value})} />
                    <textarea rows={4} placeholder="PITCH STRATEGY" className="w-full bg-black border border-red-900/30 p-3 text-xs font-mono"
                      value={targetData.pitch} onChange={e => setTargetData({...targetData, pitch: e.target.value})} />
                    <button onClick={runTargetAnalysis} className="w-full py-4 bg-red-600 text-black font-black text-[10px] uppercase">
                      Execute Forensic Scan
                    </button>
                  </div>
                </div>
              </div>
              <div className="lg:col-span-2 bg-black border border-red-900/30 rounded p-6 overflow-y-auto">
                <pre className="whitespace-pre-wrap text-[11px] font-mono text-gray-300">{result || 'WAITING FOR SCAN COMMAND...'}</pre>
              </div>
            </motion.div>
          ) : (
            <motion.div key="intel" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="h-full overflow-y-auto pr-4 custom-scrollbar">
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h2 className="text-sm font-black uppercase tracking-[0.4em] text-red-600">Intel Assets: Toku GTM</h2>
                  <p className="text-[9px] text-gray-600 uppercase font-bold mt-1 tracking-widest">Level 1 Authorization Verified</p>
                </div>
                <Unlock size={16} className="text-green-500" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {PRELOADED_COMPANIES.map((c, i) => (
                  <div key={i} className="p-5 border border-red-900/30 bg-black/40 hover:bg-red-950/10 cursor-pointer transition-all group">
                    <span className="text-[8px] font-bold text-red-500 uppercase border border-red-500/30 px-2 py-0.5">{c.sector}</span>
                    <h4 className="text-lg font-black tracking-tight mt-2 mb-1 group-hover:text-red-500">{c.empresa}</h4>
                    <p className="text-[9px] text-gray-500 font-mono uppercase">{c.pitch}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer className="fixed bottom-4 left-6 hidden md:flex items-center gap-4 text-[8px] font-mono text-gray-700 uppercase tracking-widest">
        <Activity size={10} className={isAuthorized ? "text-green-500" : "text-yellow-500"} />
        <span>Status: {isAuthorized ? "Privileged Access" : "Restricted Mode"}</span>
        <span className="w-1 h-1 bg-gray-800 rounded-full"></span>
        <span>Magi-1 Online</span>
      </footer>
    </div>
  );
};

export default App;

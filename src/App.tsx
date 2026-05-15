import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, Search, Activity, Cpu, Database, 
  ChevronRight, AlertTriangle, List, FileText, 
  Settings, Zap, Target, Globe
} from 'lucide-react';
import axios from 'axios';

// --- MOCK DATA PARA EMPRESAS PRECARGADAS ---
const PRELOADED_COMPANIES = [
  { empresa: "Under Armour", sector: "Ecommerce", pitch: "Orquestación de Pagos + Recurrencia" },
  { empresa: "Nike", sector: "Ecommerce", pitch: "Orquestación de Pagos + Recurrencia" },
  { empresa: "Coca Cola Femsa", sector: "Goods", pitch: "Digitalización de Cobranza + BNPL" },
  { empresa: "Salud Digna", sector: "Health", pitch: "Discovery - Exploración de necesidades" },
  { empresa: "Bitso", sector: "Fintech", pitch: "GTM Regional Scaling" }
];

const App = () => {
  const [activeTab, setActiveTab] = useState('extraction');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    empresa: '',
    sector: 'Fintech',
    pitch: 'Soluciones de pago B2B'
  });

  const runAnalysis = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/analyze', formData);
      setResult(response.data.data);
    } catch (error) {
      console.error(error);
      setResult("### ERROR: SIGNALS_LOST\nConnection to MAGI nodes failed. Verify API configuration.");
    } finally {
      setLoading(false);
    }
  };

  const selectPreloaded = (company: any) => {
    setFormData({
      empresa: company.empresa,
      sector: company.sector,
      pitch: company.pitch
    });
    setActiveTab('extraction');
  };

  return (
    <div className="min-h-screen w-full bg-[#0a0a0a] text-white p-4 md:p-6 overflow-hidden relative font-sans">
      {/* Background Grid */}
      <div className="absolute inset-0 opacity-5 pointer-events-none" 
           style={{ backgroundImage: 'linear-gradient(#ff0000 1px, transparent 1px), linear-gradient(90deg, #ff0000 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
      </div>

      {/* Header */}
      <header className="relative z-10 flex flex-col md:flex-row justify-between items-center border-b border-red-900/40 pb-4 mb-6">
        <div className="flex items-center gap-4 mb-4 md:mb-0">
          <div className="p-2 bg-red-600 rounded-sm shadow-[0_0_15px_rgba(255,0,0,0.5)]">
            <Shield size={28} className="text-black" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tighter nerv-text-glow italic">NERV OS v2.0</h1>
            <div className="flex items-center gap-2">
              <span className="text-[9px] text-red-500 font-bold uppercase tracking-[0.3em]">Neural Intelligence Engine</span>
              <div className="h-[2px] w-8 bg-red-600/50"></div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex bg-red-950/20 p-1 border border-red-900/30 rounded">
          {[
            { id: 'extraction', label: 'TARGET', icon: <Target size={14}/> },
            { id: 'intel', label: 'INTEL HUB', icon: <Globe size={14}/> },
            { id: 'lab', label: 'AGENT LAB', icon: <Cpu size={14}/> }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 text-[10px] font-bold uppercase tracking-widest transition-all
                ${activeTab === tab.id ? 'bg-red-600 text-black' : 'text-gray-400 hover:text-white'}`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto h-[calc(100vh-140px)]">
        <AnimatePresence mode="wait">
          {activeTab === 'extraction' && (
            <motion.div 
              key="extraction"
              initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}
              className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full"
            >
              {/* Form Side */}
              <div className="lg:col-span-1 space-y-6 flex flex-col">
                <div className="flex-1 p-6 bg-red-950/5 border border-red-900/30 rounded shadow-xl">
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-red-500">Extraction Parameters</h2>
                    <Zap size={14} className="text-red-500 animate-pulse" />
                  </div>
                  
                  <div className="space-y-5">
                    <div>
                      <label className="block text-[9px] uppercase text-gray-500 font-bold mb-1.5 tracking-wider">Entity Name</label>
                      <input 
                        type="text" 
                        className="w-full bg-black border border-red-900/40 p-3 text-sm font-mono text-red-100 focus:outline-none focus:border-red-500 transition-all placeholder:text-gray-800"
                        placeholder="ENTER TARGET..."
                        value={formData.empresa}
                        onChange={(e) => setFormData({...formData, empresa: e.target.value})}
                      />
                    </div>
                    <div>
                      <label className="block text-[9px] uppercase text-gray-500 font-bold mb-1.5 tracking-wider">Market Segment</label>
                      <input 
                        type="text" 
                        className="w-full bg-black border border-red-900/40 p-3 text-sm font-mono text-red-100 focus:outline-none focus:border-red-500"
                        value={formData.sector}
                        onChange={(e) => setFormData({...formData, sector: e.target.value})}
                      />
                    </div>
                    <div>
                      <label className="block text-[9px] uppercase text-gray-500 font-bold mb-1.5 tracking-wider">Strategy / Pitch</label>
                      <textarea 
                        rows={5}
                        className="w-full bg-black border border-red-900/40 p-3 text-sm font-mono text-red-100 focus:outline-none focus:border-red-500"
                        value={formData.pitch}
                        onChange={(e) => setFormData({...formData, pitch: e.target.value})}
                      />
                    </div>
                    
                    <button 
                      onClick={runAnalysis}
                      disabled={loading || !formData.empresa}
                      className={`w-full py-4 font-black uppercase tracking-[0.3em] text-xs flex items-center justify-center gap-3 transition-all relative overflow-hidden group
                        ${loading ? 'bg-gray-800 text-gray-500 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-black shadow-[0_0_30px_rgba(255,0,0,0.4)] hover:shadow-[0_0_40px_rgba(255,0,0,0.6)] active:scale-95'}`}
                    >
                      <div className="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-500 skew-x-12"></div>
                      {loading ? 'SYNCING MAGI...' : 'RUN FORENSIC SCAN'}
                      <ChevronRight size={18} />
                    </button>
                  </div>
                </div>

                {/* Local Stats */}
                <div className="p-4 bg-black border border-red-900/20 rounded text-[9px] font-mono flex justify-between">
                  <span className="text-gray-500 uppercase">Buffer Status: <span className="text-red-500">OPTIMAL</span></span>
                  <span className="text-gray-500 uppercase">Core Load: <span className="text-red-500">12%</span></span>
                </div>
              </div>

              {/* Output Side */}
              <div className="lg:col-span-2 flex flex-col">
                <div className="flex-1 bg-black border border-red-900/30 rounded p-6 relative overflow-hidden flex flex-col">
                  {/* Decorative corner */}
                  <div className="absolute top-0 right-0 w-24 h-24 bg-red-600/5 rotate-45 translate-x-12 translate-y-[-12px] pointer-events-none"></div>
                  
                  <div className="flex justify-between items-center mb-4 border-b border-red-900/20 pb-4">
                    <div className="flex items-center gap-3">
                      <FileText size={18} className="text-red-600" />
                      <h3 className="text-xs font-bold uppercase tracking-widest italic">Signal Output: {formData.empresa || 'Idle'}</h3>
                    </div>
                    {result && <span className="text-[9px] font-bold px-2 py-1 bg-red-600 text-black">ENCRYPTED DATA</span>}
                  </div>

                  <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
                    {loading ? (
                      <div className="h-full flex flex-col items-center justify-center gap-6">
                        <div className="relative">
                          <motion.div animate={{ rotate: 360 }} transition={{ duration: 3, repeat: Infinity, ease: "linear" }} className="w-20 h-20 border-4 border-red-600/20 border-t-red-600 rounded-full" />
                          <Activity size={24} className="absolute inset-0 m-auto text-red-600 animate-pulse" />
                        </div>
                        <div className="text-center space-y-2">
                          <p className="text-[10px] font-black tracking-[0.5em] text-red-500 animate-pulse uppercase">Searching Global Data Banks</p>
                          <p className="text-[8px] font-mono text-gray-600 uppercase">Acquiring nodes in LATAM/US... [OK]</p>
                        </div>
                      </div>
                    ) : result ? (
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="prose prose-invert max-w-none">
                        <pre className="whitespace-pre-wrap text-[11px] text-red-50 font-mono leading-relaxed bg-red-950/5 p-5 rounded border border-red-900/10">
                          {result}
                        </pre>
                      </motion.div>
                    ) : (
                      <div className="h-full flex flex-col items-center justify-center text-gray-700 text-center space-y-4">
                        <div className="p-8 border-2 border-dashed border-gray-900 rounded-full">
                          <Shield size={64} className="opacity-10" />
                        </div>
                        <div>
                          <p className="text-xs font-bold uppercase tracking-widest text-gray-500">System Ready</p>
                          <p className="text-[9px] mt-2 max-w-[200px] leading-relaxed">No signals detected. Initiate target scan from the extraction panel.</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'intel' && (
            <motion.div 
              key="intel"
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
              className="h-full overflow-y-auto pr-4 custom-scrollbar"
            >
              <div className="mb-8">
                <h2 className="text-sm font-black uppercase tracking-[0.4em] text-red-600 mb-2">Preloaded Intel Assets</h2>
                <p className="text-[10px] text-gray-500 uppercase tracking-widest font-bold">Synchronized from local databases (companies.csv)</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {PRELOADED_COMPANIES.map((company, idx) => (
                  <motion.div 
                    key={idx}
                    whileHover={{ scale: 1.02, backgroundColor: 'rgba(127,0,0,0.1)' }}
                    onClick={() => selectPreloaded(company)}
                    className="p-5 border border-red-900/30 bg-black cursor-pointer group transition-all"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <span className="text-[8px] font-bold text-red-500 uppercase border border-red-500/30 px-2 py-0.5">{company.sector}</span>
                      <ChevronRight size={14} className="text-gray-700 group-hover:text-red-500 transition-colors" />
                    </div>
                    <h4 className="text-lg font-black tracking-tight mb-2 group-hover:text-red-500 transition-colors">{company.empresa}</h4>
                    <p className="text-[10px] text-gray-500 font-mono line-clamp-2 uppercase">{company.pitch}</p>
                    <div className="mt-4 pt-4 border-t border-red-900/10 flex justify-between items-center">
                      <span className="text-[8px] text-gray-600 font-bold uppercase">Ready for re-scan</span>
                      <div className="flex gap-1">
                        <div className="w-1 h-1 bg-green-500 rounded-full" />
                        <div className="w-1 h-1 bg-green-500 rounded-full" />
                        <div className="w-1 h-1 bg-green-500 rounded-full opacity-30" />
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'lab' && (
            <motion.div 
              key="lab"
              initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 1.02 }}
              className="h-full flex items-center justify-center"
            >
              <div className="max-w-xl w-full p-10 border border-red-900/20 bg-red-950/5 text-center relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-red-600 to-transparent shadow-[0_0_10px_rgba(255,0,0,1)]"></div>
                
                <AlertTriangle size={48} className="text-red-600 mx-auto mb-6 animate-pulse" />
                <h3 className="text-xl font-black uppercase tracking-[0.5em] mb-4">Agent Lab Access</h3>
                <p className="text-xs text-gray-500 leading-relaxed uppercase tracking-widest mb-8">
                  Warning: Advanced agent orchestration tools are currently restricted. Modification of MAGI-1 logic protocols may result in catastrophic neural feedback.
                </p>
                
                <div className="grid grid-cols-2 gap-4 text-left">
                  <div className="p-4 border border-red-900/30 bg-black">
                    <p className="text-[8px] font-bold text-red-500 uppercase mb-2">Swarm Mode</p>
                    <p className="text-[10px] font-bold uppercase">Sequential [LOCK]</p>
                  </div>
                  <div className="p-4 border border-red-900/30 bg-black">
                    <p className="text-[8px] font-bold text-red-500 uppercase mb-2">Memory Depth</p>
                    <p className="text-[10px] font-bold uppercase">Long-Term [ON]</p>
                  </div>
                </div>

                <div className="mt-8 pt-8 border-t border-red-900/20 flex justify-center items-center gap-6">
                  <Settings size={20} className="text-gray-700 hover:text-red-600 cursor-pointer transition-colors" />
                  <Database size={20} className="text-gray-700 hover:text-red-600 cursor-pointer transition-colors" />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer Info */}
      <footer className="fixed bottom-4 left-6 hidden md:block">
        <div className="flex items-center gap-4 text-[8px] font-mono text-gray-600 uppercase tracking-[0.2em]">
          <span>Magi-1: Active</span>
          <span className="w-1 h-1 bg-gray-800 rounded-full"></span>
          <span>Crypto: AES-256</span>
          <span className="w-1 h-1 bg-gray-800 rounded-full"></span>
          <span>Source: agutierrez11/Nerv-OS</span>
        </div>
      </footer>
    </div>
  );
};

export default App;

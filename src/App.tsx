import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Search, Activity, Cpu, Database, ChevronRight, AlertTriangle } from 'lucide-react';
import axios from 'axios';

const App = () => {
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
      setResult("ERROR: CONNECTION_FAILURE_DETECTION_FAILED");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#0a0a0a] text-white p-4 md:p-8 overflow-hidden relative">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 opacity-10 pointer-events-none" 
           style={{ backgroundImage: 'radial-gradient(#ff0000 0.5px, transparent 0.5px)', backgroundSize: '20px 20px' }}>
      </div>

      {/* Header */}
      <header className="relative z-10 flex justify-between items-center border-b border-red-900/50 pb-4 mb-8">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-600 rounded-sm">
            <Shield size={24} className="text-black" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tighter nerv-text-glow">NERV OS</h1>
            <p className="text-[10px] text-red-500 uppercase tracking-[0.2em]">Forensic GTM Engine v2.0</p>
          </div>
        </div>
        <div className="hidden md:flex gap-8 text-[10px] uppercase tracking-widest text-gray-500">
          <div className="flex items-center gap-2"><Activity size={12} className="text-green-500" /> System: Stable</div>
          <div className="flex items-center gap-2"><Cpu size={12} /> Sync: 98%</div>
          <div className="flex items-center gap-2"><Database size={12} /> Nodes: Active</div>
        </div>
      </header>

      <main className="relative z-10 max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Panel */}
        <div className="lg:col-span-1 space-y-6">
          <div className="p-6 bg-red-950/10 border border-red-900/30 rounded-lg backdrop-blur-sm">
            <h2 className="text-sm font-bold uppercase tracking-widest text-red-500 mb-6 flex items-center gap-2">
              <Search size={16} /> Target Configuration
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-[10px] uppercase text-gray-400 mb-1">Company Entity</label>
                <input 
                  type="text" 
                  placeholder="e.g. Bitso"
                  className="w-full bg-black border border-red-900/50 p-3 text-sm focus:outline-none focus:border-red-500 transition-colors"
                  value={formData.empresa}
                  onChange={(e) => setFormData({...formData, empresa: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-[10px] uppercase text-gray-400 mb-1">Market Sector</label>
                <input 
                  type="text" 
                  className="w-full bg-black border border-red-900/50 p-3 text-sm focus:outline-none focus:border-red-500 transition-colors"
                  value={formData.sector}
                  onChange={(e) => setFormData({...formData, sector: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-[10px] uppercase text-gray-400 mb-1">Strategic Pitch</label>
                <textarea 
                  rows={4}
                  className="w-full bg-black border border-red-900/50 p-3 text-sm focus:outline-none focus:border-red-500 transition-colors"
                  value={formData.pitch}
                  onChange={(e) => setFormData({...formData, pitch: e.target.value})}
                />
              </div>
              
              <button 
                onClick={runAnalysis}
                disabled={loading || !formData.empresa}
                className={`w-full py-4 font-bold uppercase tracking-widest text-sm flex items-center justify-center gap-2 transition-all
                  ${loading ? 'bg-gray-800 text-gray-500' : 'bg-red-600 hover:bg-red-500 text-black shadow-[0_0_20px_rgba(255,0,0,0.3)]'}`}
              >
                {loading ? 'Initializing Swarm...' : 'Initiate Analysis'}
                <ChevronRight size={18} />
              </button>
            </div>
          </div>

          {/* Status Display */}
          <div className="p-4 border border-red-900/20 rounded-lg bg-black/50 overflow-hidden relative">
            <div className="absolute top-0 right-0 p-2 opacity-10">
              <AlertTriangle size={40} className="text-red-500" />
            </div>
            <p className="text-[10px] text-gray-500 uppercase mb-2">Internal Diagnostics</p>
            <div className="space-y-1">
              {[1,2,3].map(i => (
                <div key={i} className="h-1 bg-red-900/20 rounded-full overflow-hidden">
                  <motion.div 
                    initial={{ x: '-100%' }}
                    animate={{ x: '100%' }}
                    transition={{ duration: 2 + i, repeat: Infinity, ease: "linear" }}
                    className="h-full w-1/3 bg-red-600"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2">
          <div className="h-full min-h-[500px] p-6 bg-black border border-red-900/30 rounded-lg relative overflow-y-auto">
            <AnimatePresence mode="wait">
              {loading ? (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center justify-center h-full gap-4"
                >
                  <motion.div 
                    animate={{ rotate: 360 }}
                    transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                    className="w-16 h-16 border-2 border-red-600 border-t-transparent rounded-full"
                  />
                  <p className="text-sm font-mono animate-pulse text-red-500 tracking-tighter">DECRYPTING TARGET SIGNALS...</p>
                </motion.div>
              ) : result ? (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="prose prose-invert max-w-none"
                >
                  <div className="flex justify-between items-start border-b border-red-900/50 pb-4 mb-6">
                    <h3 className="text-xl font-bold m-0 text-red-500">Dossier: {formData.empresa}</h3>
                    <span className="text-[10px] bg-red-600 text-black px-2 py-1 font-bold">TOP SECRET</span>
                  </div>
                  <pre className="whitespace-pre-wrap text-xs text-gray-300 font-mono leading-relaxed bg-red-950/5 p-4 rounded border border-red-900/20">
                    {result}
                  </pre>
                </motion.div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-600 text-center space-y-4">
                  <Shield size={64} className="opacity-20" />
                  <div>
                    <p className="text-sm font-bold uppercase tracking-widest">Waiting for Input</p>
                    <p className="text-[10px] mt-2">Enter target parameters to begin forensic extraction.</p>
                  </div>
                </div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>

      {/* Decorative Elements */}
      <div className="fixed bottom-4 right-4 flex gap-2">
        <div className="w-1 h-1 bg-red-600 rounded-full animate-ping" />
        <p className="text-[8px] font-mono text-red-600 uppercase">MAGI-1: ONLINE</p>
      </div>
    </div>
  );
};

export default App;

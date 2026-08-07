import React, { useState, useRef, useEffect } from 'react';
import { 
  Code, 
  Settings, 
  Terminal, 
  Play, 
  Copy, 
  Check, 
  Zap, 
  BarChart2, 
  Cpu, 
  AlertCircle,
  Bug,
  LineChart,
  RefreshCw,
  Newspaper,
  Globe
} from 'lucide-react';

const TRADING_TOOLS = [
  { id: 'sma', name: 'Simple Moving Average (SMA)', category: 'Trend' },
  { id: 'ema', name: 'Exponential Moving Average (EMA)', category: 'Trend' },
  { id: 'macd', name: 'MACD', category: 'Momentum' },
  { id: 'rsi', name: 'RSI', category: 'Momentum' },
  { id: 'bollinger', name: 'Bollinger Bands', category: 'Volatility' },
  { id: 'atr', name: 'Average True Range (ATR)', category: 'Volatility' },
  { id: 'stochastic', name: 'Stochastic Oscillator', category: 'Momentum' },
  { id: 'ichimoku', name: 'Ichimoku Cloud', category: 'Trend' },
  { id: 'volume', name: 'Volume', category: 'Volume' },
  { id: 'fibonacci', name: 'Fibonacci Retracement', category: 'Support/Resistance' },
  { id: 'news_filter', name: 'Forex Factory News Filter', category: 'Risk Management' },
  { id: 'session_filter', name: 'Trading Session (London/NY)', category: 'Time' },
];

const NEWS_TEMPLATES = [
  { id: 'custom', name: '📝 Custom / Isi Manual', title: 'Data Rilis Terbaru', currency: 'USD', forecast: '', previous: '' },
  { id: 'nfp', name: '🇺🇸 US Non-Farm Payrolls (NFP)', title: 'Non-Farm Payrolls', currency: 'USD', forecast: '185K', previous: '206K' },
  { id: 'cpi', name: '🇺🇸 US Consumer Price Index (CPI)', title: 'US Consumer Price Index (CPI) m/m', currency: 'USD', forecast: '0.2%', previous: '0.1%' },
  { id: 'fomc', name: '🇺🇸 FOMC Fed Funds Rate', title: 'FOMC Fed Funds Rate', currency: 'USD', forecast: '5.25%', previous: '5.50%' },
  { id: 'boe', name: '🇬🇧 BOE Interest Rate Decision', title: 'BOE Interest Rate Decision', currency: 'GBP', forecast: '5.00%', previous: '5.25%' },
  { id: 'boj', name: '🇯🇵 BOJ Interest Rate Decision', title: 'BOJ Interest Rate Decision', currency: 'JPY', forecast: '0.25%', previous: '0.10%' },
];

export default function AlgoTradeBuilder() {
  const [activeTab, setActiveTab] = useState('builder'); // 'builder' | 'chart' | 'news'
  
  // ================= STATE: AI BUILDER =================
  const [platform, setPlatform] = useState('pinescript');
  const [selectedTools, setSelectedTools] = useState([]);
  const [logicPrompt, setLogicPrompt] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const [error, setError] = useState('');
  const [compilerError, setCompilerError] = useState('');
  const [isFixing, setIsFixing] = useState(false);

  // ================= STATE: CHART ANALYZER =================
  const [analysisTF, setAnalysisTF] = useState('H1');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState('');
  const [signalData, setSignalData] = useState(null); 

  // ================= STATE: FUNDAMENTAL NEWS =================
  const [newsTemplate, setNewsTemplate] = useState(NEWS_TEMPLATES[1]);
  const [newsTitle, setNewsTitle] = useState(NEWS_TEMPLATES[1].title);
  const [newsCurrency, setNewsCurrency] = useState(NEWS_TEMPLATES[1].currency);
  const [newsForecast, setNewsForecast] = useState(NEWS_TEMPLATES[1].forecast);
  const [newsPrevious, setNewsPrevious] = useState(NEWS_TEMPLATES[1].previous);
  const [newsPairs, setNewsPairs] = useState('XAUUSD, USDJPY, GBPUSD, EURUSD');
  const [newsContext, setNewsContext] = useState('');
  const [isAnalyzingNews, setIsAnalyzingNews] = useState(false);
  const [newsResult, setNewsResult] = useState('');

  // Auto-fill form berita ketika dropdown diganti
  useEffect(() => {
    if (newsTemplate.id !== 'custom') {
      setNewsTitle(newsTemplate.title);
      setNewsCurrency(newsTemplate.currency);
      setNewsForecast(newsTemplate.forecast);
      setNewsPrevious(newsTemplate.previous);
    }
  }, [newsTemplate]);

  // Handle Chart TradingView Render
  useEffect(() => {
    if (activeTab !== 'chart') return;
    const container = document.getElementById('tv_chart_container');
    if (!container) return;
    let tvScript = document.getElementById('tv-script');
    
    const initWidget = () => {
      if (window.TradingView) {
        container.innerHTML = '';
        new window.TradingView.widget({
          autosize: true,
          symbol: "OANDA:XAUUSD",
          interval: getTVInterval(analysisTF),
          timezone: "Asia/Jakarta",
          theme: "dark",
          style: "1",
          locale: "id",
          enable_publishing: false,
          backgroundColor: "#1f2937",
          hide_top_toolbar: false,
          hide_legend: false,
          save_image: true,
          container_id: "tv_chart_container",
          withdateranges: true,
          allow_symbol_change: true,
          show_popup_button: true,
        });
      }
    };

    if (!tvScript) {
      tvScript = document.createElement('script');
      tvScript.id = 'tv-script';
      tvScript.src = 'https://s3.tradingview.com/tv.js';
      tvScript.async = true;
      tvScript.onload = initWidget;
      document.body.appendChild(tvScript);
    } else {
      initWidget(); 
    }
  }, [analysisTF, activeTab]); 

  const getTVInterval = (tf) => {
    const map = { 'M1': '1', 'M5': '5', 'M15': '15', 'M30': '30', 'H1': '60', 'H4': '240', 'Daily': 'D' };
    return map[tf] || '60'; 
  };

  const toggleTool = (toolId) => {
    setSelectedTools(prev => prev.includes(toolId) ? prev.filter(id => id !== toolId) : [...prev, toolId]);
  };

  const handleCopy = () => {
    if (generatedCode) {
      navigator.clipboard.writeText(generatedCode);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  // ================= AI FUNCTION: FIX CODE =================
  const fixGeneratedCode = async () => { /* ... existing fix logic ... */ };

  // ================= AI FUNCTION: GENERATE SCRIPT =================
  const generateScript = async () => { /* ... existing generate logic ... */ };

  // ================= AI FUNCTION: ANALYZE CHART =================
  const analyzeMarket = async () => { /* ... existing analyze market logic ... */ };

  // ================= AI FUNCTION: ANALYZE NEWS =================
  const analyzeNews = async () => {
    setIsAnalyzingNews(true);
    setNewsResult('');

    const systemInstruction = `Anda adalah analis pasar keuangan makro dan trader institusional senior dengan pengalaman lebih dari 20 tahun.
    Jawab dengan format teks terstruktur yang rapi (Gunakan -, *, atau kapitalisasi untuk penekanan, hindari Markdown rumit jika memungkinkan agar render di React aman).`;

    const userQuery = `Buatkan analisis skenario trading mendalam SEBELUM rilis berita berikut:
    - Nama Berita: ${newsTitle} (Mata Uang Penggerak: ${newsCurrency})
    - Data Perkiraan (Forecast): ${newsForecast}
    - Data Sebelumnya (Previous): ${newsPrevious}
    - Pair Target: ${newsPairs}
    - Sentimen Tambahan: ${newsContext || "Tidak ada, fokus pada teknikal makro ekonomi."}

    Format Output Wajib:
    1. EKSPEKTASI PASAR (PRE-MARKET SENTIMENT)
    [Jelaskan apa yang sedang ditunggu pasar]

    2. SKENARIO RILIS DATA
    - SKENARIO A (HAWKISH / Lebih kuat dari ekspektasi)
    - SKENARIO B (DOVISH / Lebih lemah dari ekspektasi)

    3. PREDIKSI BIAS PER PAIR
    [Jelaskan nasib masing-masing pair untuk skenario A dan skenario B]

    4. STRATEGI EKSEKUSI & MANAJEMEN RISIKO
    [Tips cara mengambil posisi yang aman dan area fakeout/whipsaw]`;

    try {
      const apiKey = ""; // Masukkan API Key kamu di sini
      const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${apiKey}`;
      
      const payload = {
        contents: [{ parts: [{ text: userQuery }] }],
        systemInstruction: { parts: [{ text: systemInstruction }] },
      };

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      
      if (result.candidates && result.candidates[0].content.parts[0].text) {
        setNewsResult(result.candidates[0].content.parts[0].text);
      } else {
        throw new Error("Gagal mendapatkan analisis dari AI.");
      }
    } catch (err) {
      setNewsResult('Terjadi kesalahan saat memproses data AI fundamental. Cek API Key atau koneksi internet.');
      console.error(err);
    } finally {
      setIsAnalyzingNews(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-200 font-sans p-4 md:p-8 flex flex-col items-center">
      
      {/* Header */}
      <header className="w-full max-w-7xl flex justify-between items-center mb-8 pb-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">AlgoTrade<span className="text-blue-500">.AI</span></h1>
            <p className="text-xs text-gray-400">All-in-One AI Trading Assistant</p>
          </div>
        </div>
      </header>

      {/* TABS MENU */}
      <div className="w-full max-w-7xl mb-6 flex gap-2 overflow-x-auto pb-2">
        <button 
          onClick={() => setActiveTab('builder')}
          className={`px-4 py-2 whitespace-nowrap rounded-lg text-sm font-semibold flex items-center gap-2 transition-all ${activeTab === 'builder' ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
        >
          <Code className="w-4 h-4" /> EA & Script Builder
        </button>
        <button 
          onClick={() => setActiveTab('chart')}
          className={`px-4 py-2 whitespace-nowrap rounded-lg text-sm font-semibold flex items-center gap-2 transition-all ${activeTab === 'chart' ? 'bg-yellow-600 text-white shadow-lg shadow-yellow-900/20' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
        >
          <LineChart className="w-4 h-4" /> Live AI Market
        </button>
        <button 
          onClick={() => setActiveTab('news')}
          className={`px-4 py-2 whitespace-nowrap rounded-lg text-sm font-semibold flex items-center gap-2 transition-all ${activeTab === 'news' ? 'bg-purple-600 text-white shadow-lg shadow-purple-900/20' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
        >
          <Newspaper className="w-4 h-4" /> Fundamental News Predictor
        </button>
      </div>

      {/* ================= TAB 1: EA BUILDER (Kode Lama) ================= */}
      {activeTab === 'builder' && (
        <main className="w-full max-w-7xl grid grid-cols-1 lg:grid-cols-12 gap-8">
           {/* Masukkan blok UI <div className="lg:col-span-5..."> sampai penutup </main> tab builder di sini dari kode React kamu yang lama */}
           <div className="lg:col-span-12 text-center text-gray-400">
               *(UI Builder Script AI Berada Disini)*
           </div>
        </main>
      )}

      {/* ================= TAB 2: LIVE CHART (Kode Lama) ================= */}
      {activeTab === 'chart' && (
        <main className="w-full max-w-7xl grid grid-cols-1 lg:grid-cols-12 gap-4 h-[800px]">
           {/* Masukkan blok UI chart <div id="tv_chart_container"> dari kode React kamu yang lama di sini */}
           <div className="lg:col-span-12 text-center text-gray-400">
               *(UI TradingView dan Market Analyzer Berada Disini)*
           </div>
        </main>
      )}

      {/* ================= TAB 3: FUNDAMENTAL NEWS PREDICTOR ================= */}
      {activeTab === 'news' && (
        <main className="w-full max-w-7xl flex flex-col gap-6">
          <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <Globe className="w-6 h-6 text-purple-400" />
              <div>
                <h2 className="text-xl font-bold text-white">AI Fundamental News Engine</h2>
                <p className="text-sm text-gray-400">Prediksi skenario efek domino rilis berita terhadap berbagai Pair/Crypto sebelum berita rilis.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="lg:col-span-4">
                <label className="block text-xs font-semibold text-gray-400 mb-1">Pilih Berita dari Kalender:</label>
                <select 
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2.5 text-sm text-gray-200 focus:border-purple-500 outline-none"
                  onChange={(e) => setNewsTemplate(NEWS_TEMPLATES.find(t => t.id === e.target.value))}
                  value={newsTemplate.id}
                >
                  {NEWS_TEMPLATES.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Nama Berita (Target):</label>
                <input type="text" value={newsTitle} onChange={(e) => setNewsTitle(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2.5 text-sm text-gray-200 outline-none" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Mata Uang Utama:</label>
                <input type="text" value={newsCurrency} onChange={(e) => setNewsCurrency(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2.5 text-sm text-gray-200 outline-none" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Konsensus (Forecast):</label>
                <input type="text" value={newsForecast} onChange={(e) => setNewsForecast(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2.5 text-sm text-gray-200 outline-none" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Data Previous:</label>
                <input type="text" value={newsPrevious} onChange={(e) => setNewsPrevious(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2.5 text-sm text-gray-200 outline-none" />
              </div>

              <div className="lg:col-span-2">
                <label className="block text-xs font-semibold text-gray-400 mb-1">Target Pairs (Pisahkan dengan koma):</label>
                <input type="text" value={newsPairs} onChange={(e) => setNewsPairs(e.target.value)} placeholder="Misal: XAUUSD, USDJPY, GBPUSD" className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2.5 text-sm text-gray-200 outline-none" />
              </div>
              <div className="lg:col-span-2">
                <label className="block text-xs font-semibold text-gray-400 mb-1">Sentimen Terkini (Opsional):</label>
                <input type="text" value={newsContext} onChange={(e) => setNewsContext(e.target.value)} placeholder="Contoh: Geopolitik memanas..." className="w-full bg-gray-900 border border-gray-700 rounded-lg p-2.5 text-sm text-gray-200 outline-none" />
              </div>
            </div>

            <button 
              onClick={analyzeNews}
              disabled={isAnalyzingNews}
              className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold py-3.5 px-4 rounded-lg flex items-center justify-center gap-2 transition-all shadow-lg shadow-purple-900/20 disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isAnalyzingNews ? (
                <><RefreshCw className="w-5 h-5 animate-spin" /> Sedang Menganalisis Korelasi Fundamental...</>
              ) : (
                <><Zap className="w-5 h-5 fill-current" /> Hasilkan Skenario Prediksi AI</>
              )}
            </button>
          </div>

          {/* Result Area */}
          {(newsResult || isAnalyzingNews) && (
            <div className="bg-[#1e1e24] p-6 rounded-xl border border-gray-700 shadow-2xl min-h-[300px]">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <Newspaper className="w-5 h-5 text-purple-400" /> Hasil Analisis Fundamental AI
              </h3>
              
              {isAnalyzingNews ? (
                 <div className="h-64 flex flex-col items-center justify-center text-gray-500">
                   <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                   <p className="animate-pulse">Menghubungkan titik-titik data makro ekonomi...</p>
                 </div>
              ) : (
                 <div className="text-gray-300 text-[14px] leading-relaxed whitespace-pre-wrap font-mono">
                   {newsResult}
                 </div>
              )}
            </div>
          )}
        </main>
      )}

    </div>
  );
}

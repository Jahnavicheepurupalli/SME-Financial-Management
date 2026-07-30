import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { motion, AnimatePresence } from 'framer-motion';
import * as Lucide from 'lucide-react';

// Reusable Custom SVG Line Chart Component
function SVGLineChart({ data, labels, color = '#0f766e', darkColor = '#2dd4bf' }) {
  if (!data || data.length === 0) return <div className="text-xs text-slate-400 py-6 text-center">No trend data available</div>;
  
  const maxVal = Math.max(...data, 1);
  const minVal = Math.min(...data, 0);
  const range = maxVal - minVal;
  
  const width = 500;
  const height = 150;
  const padding = 25;
  
  const points = data.map((val, idx) => {
    const x = padding + (idx * (width - 2 * padding)) / (data.length - 1 || 1);
    const y = height - padding - ((val - minVal) * (height - 2 * padding)) / range;
    return { x, y, val };
  });
  
  const polylinePoints = points.map(p => `${p.x},${p.y}`).join(' ');

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-36 overflow-visible">
        {/* Grid lines */}
        <line x1={padding} y1={padding} x2={width - padding} y2={padding} className="stroke-slate-200 dark:stroke-slate-800" strokeWidth="1" strokeDasharray="3,3" />
        <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} className="stroke-slate-200 dark:stroke-slate-800" strokeWidth="1" strokeDasharray="3,3" />
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} className="stroke-slate-300 dark:stroke-slate-700" strokeWidth="1" />
        
        {/* Line */}
        <polyline fill="none" stroke={color} strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" points={polylinePoints} />
        
        {/* Glow effect */}
        <polyline fill="none" stroke={color} strokeWidth="8" strokeLinecap="round" strokeLinejoin="round" opacity="0.15" points={polylinePoints} />
        
        {/* Points & Tooltips */}
        {points.map((p, idx) => (
          <g key={idx} className="group cursor-pointer">
            <circle cx={p.x} cy={p.y} r="5" className="fill-white stroke-teal-600 dark:stroke-teal-400" strokeWidth="2.5" />
            <circle cx={p.x} cy={p.y} r="9" className="fill-teal-500 opacity-0 group-hover:opacity-20 transition-opacity" />
            
            {/* Tooltip */}
            <g className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <rect x={p.x - 45} y={p.y - 32} width="90" height="20" rx="4" className="fill-slate-900 text-white" />
              <text x={p.x} y={p.y - 18} textAnchor="middle" className="fill-white text-[9px] font-bold">
                {p.val >= 1000 ? `INR ${(p.val/1000).toFixed(1)}k` : `INR ${p.val}`}
              </text>
            </g>
            
            {/* Label */}
            <text x={p.x} y={height - 6} textAnchor="middle" className="fill-slate-400 dark:fill-slate-500 text-[9px] font-semibold">
              {labels[idx] || `P${idx+1}`}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

// Reusable SVG Bar Chart Component
function SVGBarChart({ data, labels, color = '#6366f1' }) {
  if (!data || data.length === 0) return <div className="text-xs text-slate-400 py-6 text-center">No comparative data available</div>;
  
  const maxVal = Math.max(...data, 1);
  const width = 500;
  const height = 150;
  const padding = 25;
  const chartWidth = width - 2 * padding;
  const chartHeight = height - 2 * padding;
  const barWidth = (chartWidth / data.length) * 0.6;
  const gap = (chartWidth / data.length) * 0.4;

  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-36 overflow-visible">
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} className="stroke-slate-300 dark:stroke-slate-700" strokeWidth="1" />
        
        {data.map((val, idx) => {
          const barHeight = (val / maxVal) * chartHeight;
          const x = padding + idx * (barWidth + gap) + gap / 2;
          const y = height - padding - barHeight;
          
          return (
            <g key={idx} className="group cursor-pointer">
              {/* Rounded top bars using rect */}
              <rect x={x} y={y} width={barWidth} height={barHeight} rx="3" fill={color} className="opacity-80 group-hover:opacity-100 transition-opacity" />
              
              {/* Tooltip */}
              <g className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <rect x={x + barWidth/2 - 40} y={y - 25} width="80" height="18" rx="4" className="fill-slate-900 text-white" />
                <text x={x + barWidth/2} y={y - 13} textAnchor="middle" className="fill-white text-[8px] font-bold">
                  {val >= 1000 ? `INR ${(val/1000).toFixed(1)}k` : `INR ${val}`}
                </text>
              </g>
              
              {/* Label */}
              <text x={x + barWidth/2} y={height - 6} textAnchor="middle" className="fill-slate-400 dark:fill-slate-500 text-[9px] font-semibold">
                {labels[idx] || `P${idx+1}`}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// Custom Multi-Bar SVG Chart for Assets vs Liabilities Comparison
function AssetsVsLiabilitiesChart({ assets = [], liabilities = [], labels = [] }) {
  const maxVal = Math.max(...assets, ...liabilities, 1);
  const width = 500;
  const height = 150;
  const padding = 25;
  const chartWidth = width - 2 * padding;
  const chartHeight = height - 2 * padding;
  const groupWidth = chartWidth / (assets.length || 1);
  const barWidth = groupWidth * 0.35;
  
  return (
    <div className="w-full">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-36 overflow-visible">
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} className="stroke-slate-300 dark:stroke-slate-700" strokeWidth="1" />
        
        {assets.map((assetVal, idx) => {
          const liabVal = liabilities[idx] || 0;
          
          const assetHeight = (assetVal / maxVal) * chartHeight;
          const liabHeight = (liabVal / maxVal) * chartHeight;
          
          const xGroup = padding + idx * groupWidth;
          const xAsset = xGroup + groupWidth * 0.15;
          const xLiab = xAsset + barWidth + groupWidth * 0.05;
          
          const yAsset = height - padding - assetHeight;
          const yLiab = height - padding - liabHeight;
          
          return (
            <g key={idx} className="group">
              {/* Asset Bar */}
              <rect x={xAsset} y={yAsset} width={barWidth} height={assetHeight} rx="2" fill="#0f766e" className="opacity-80 hover:opacity-100 transition-opacity" />
              {/* Liability Bar */}
              <rect x={xLiab} y={yLiab} width={barWidth} height={liabHeight} rx="2" fill="#f43f5e" className="opacity-80 hover:opacity-100 transition-opacity" />
              
              {/* Tooltip */}
              <g className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <rect x={xGroup + groupWidth/2 - 50} y={Math.min(yAsset, yLiab) - 30} width="100" height="24" rx="4" className="fill-slate-900 text-white" />
                <text x={xGroup + groupWidth/2} y={Math.min(yAsset, yLiab) - 18} textAnchor="middle" className="fill-white text-[8px] font-bold">
                  A: INR {assetVal >= 1000 ? `${(assetVal/1000).toFixed(0)}k` : assetVal} | L: INR {liabVal >= 1000 ? `${(liabVal/1000).toFixed(0)}k` : liabVal}
                </text>
              </g>
              
              {/* Label */}
              <text x={xGroup + groupWidth/2} y={height - 6} textAnchor="middle" className="fill-slate-400 dark:fill-slate-500 text-[9px] font-semibold">
                {labels[idx] || `P${idx+1}`}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export default function Dashboard({ darkMode, toggleDarkMode }) {
  const [user, setUser] = useState(null);
  const [filesHistory, setFilesHistory] = useState([]);
  const [activeAnalysis, setActiveAnalysis] = useState(null);
  const [activeAnalysisDocName, setActiveAnalysisDocName] = useState('');
  const [activeAnalysisDocId, setActiveAnalysisDocId] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadingState, setUploadingState] = useState(''); // 'uploading', 'reasoning', 'idle', 'error'
  const [selectedFile, setSelectedFile] = useState(null);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [activeTab, setActiveTab] = useState('csa'); // 'csa', 'gaps', 'missing', 'flags', 'chat'
  
  // Chat state
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatBottomRef = useRef(null);

  const navigate = useNavigate();

  // Load User and Upload History
  useEffect(() => {
    const cachedUser = localStorage.getItem('user');
    if (cachedUser) {
      setUser(JSON.parse(cachedUser));
    }
    fetchHistory();
  }, []);

  // Scroll chat bottom
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory, activeTab]);

  const fetchHistory = async (targetDocId = null) => {
    try {
      const response = await api.get('/history');
      const history = response.data.history;
      setFilesHistory(history);
      
      if (history.length > 0) {
        const analyzedDocs = history.filter(d => d.status === 'analyzed');
        if (analyzedDocs.length > 0) {
          // Determine which document to load
          let toLoad = analyzedDocs[0]; // Default to latest analyzed
          
          if (targetDocId) {
            const match = analyzedDocs.find(d => d.id === targetDocId);
            if (match) toLoad = match;
          } else if (activeAnalysisDocId) {
            const stillExists = analyzedDocs.find(d => d.id === activeAnalysisDocId);
            if (stillExists) toLoad = stillExists;
          }
          
          loadAnalysis(toLoad.id, toLoad.filename);
        } else {
          // If no analyzed docs remain
          setActiveAnalysis(null);
          setActiveAnalysisDocName('');
          setActiveAnalysisDocId(null);
        }
      } else {
        // Empty history
        setActiveAnalysis(null);
        setActiveAnalysisDocName('');
        setActiveAnalysisDocId(null);
      }
    } catch (err) {
      console.error('Failed to fetch history', err);
    }
  };

  const loadAnalysis = async (docId, filename) => {
    try {
      const response = await api.get(`/history/${docId}`);
      setActiveAnalysis(response.data.analysis);
      setActiveAnalysisDocName(filename);
      setActiveAnalysisDocId(docId);
      setChatHistory([]); // Clear chat session when loading history item
    } catch (err) {
      console.error('Failed to load analysis details', err);
    }
  };

  const handleDeleteDoc = async (e, docId, filename) => {
    e.stopPropagation(); // Avoid loading details while clicking delete icon
    const confirmDelete = window.confirm(`Are you sure you want to delete this document?`);
    if (!confirmDelete) return;

    try {
      await api.delete(`/document/delete/${docId}`);
      alert(`Document '${filename}' deleted successfully.`);
      
      // If we deleted the active document, load the next available in fetchHistory
      const nextTargetId = activeAnalysisDocId === docId ? null : activeAnalysisDocId;
      if (activeAnalysisDocId === docId) {
        setActiveAnalysisDocId(null);
      }
      fetchHistory(nextTargetId);
    } catch (err) {
      alert(`Failed to delete document: ${err.response?.data?.message || err.message}`);
    }
  };

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (err) {
      console.error('Server logout failed', err);
    } finally {
      localStorage.clear();
      navigate('/login');
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    setUploadingState('uploading');
    setUploadProgress(20);

    let interval;
    try {
      interval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 65) {
            clearInterval(interval);
            setUploadingState('reasoning');
            return 85;
          }
          return prev + 15;
        });
      }, 250);

      const response = await api.post('/upload', formData, {
        headers: { 
          'Content-Type': 'multipart/form-data'
        }
      });

      clearInterval(interval);
      setUploadProgress(100);
      setTimeout(() => {
        setUploadingState('idle');
        setSelectedFile(null);
        
        if (response.data.document) {
          fetchHistory(response.data.document.id);
          setActiveTab('csa'); // Go to dashboard
        }
      }, 500);

    } catch (err) {
      if (interval) clearInterval(interval);
      setUploadingState('error');
      setUploadProgress(0);
      alert(`Analysis failed: ${err.response?.data?.message || err.message || 'Error occurred during upload and analysis pipeline.'}`);
    }
  };

  const downloadPDFReport = async () => {
    if (!activeAnalysisDocId) return;
    try {
      const response = await api.get(`/report/${activeAnalysisDocId}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Financial_Intelligence_Report_${activeAnalysisDocName}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      alert('Failed to download PDF report. Ensure report is generated.');
    }
  };

  const handleSendChatMessage = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim() || !activeAnalysisDocId || isChatLoading) return;

    const userMsg = { role: 'user', content: chatMessage };
    setChatHistory((prev) => [...prev, userMsg]);
    setChatMessage('');
    setIsChatLoading(true);

    try {
      const response = await api.post('/chat', {
        document_id: activeAnalysisDocId,
        message: userMsg.content,
        history: chatHistory
      });

      setChatHistory((prev) => [...prev, { role: 'assistant', content: response.data.response }]);
    } catch (err) {
      console.error(err);
      setChatHistory((prev) => [
        ...prev,
        { role: 'assistant', content: 'Connection timed out or network error. Please try again.' }
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Safe Metric Formatting helper
  const fmtCurr = (val) => {
    if (val === undefined || val === null) return 'INR 0';
    try {
      return `INR ${parseFloat(val).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
    } catch {
      return `INR ${val}`;
    }
  };

  const fmtPct = (val) => {
    return `${val !== undefined && val !== null ? val : 0}%`;
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 transition-colors duration-300 flex flex-col">
      {/* HEADER */}
      <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-200/50 dark:border-slate-800/50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Lucide.ShieldCheck className="h-7 w-7 text-teal-600 dark:text-teal-400" />
          <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-teal-600 to-indigo-500 bg-clip-text text-transparent">
            FinIntel Agent for SMEs
          </span>
        </div>
        
        <div className="flex items-center gap-4">
          <button 
            onClick={toggleDarkMode}
            className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
            title="Toggle theme"
          >
            {darkMode ? <Lucide.Sun className="h-5 w-5 text-teal-400" /> : <Lucide.Moon className="h-5 w-5 text-slate-600" />}
          </button>

          <button 
            onClick={() => setShowProfileModal(true)}
            className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 text-sm font-semibold"
          >
            <Lucide.UserCircle className="h-5 w-5 text-slate-500" />
            <span className="hidden sm:inline">{user?.full_name || 'My Profile'}</span>
          </button>

          <button 
            onClick={handleLogout}
            className="p-2 rounded-lg text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors flex items-center gap-1.5 text-sm font-semibold"
          >
            <Lucide.LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </header>

      {/* DASHBOARD LAYOUT */}
      <main className="max-w-7xl mx-auto p-6 space-y-6 flex-grow w-full">
        
        {/* WELCOME CARD */}
        <div className="p-6 rounded-2xl glass-card border border-white/40 dark:border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden">
          <div className="absolute top-0 right-0 -mt-12 -mr-12 w-32 h-32 bg-teal-500/10 rounded-full blur-2xl pointer-events-none" />
          <div>
            <h1 className="text-xl md:text-2xl font-bold">FinIntel SME Intelligence Dashboard 👋</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Upload spreadsheets, PDFs, or images to calculate key indicators, predict risks, run gap analysis, or ask questions to the AI assistant.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs font-semibold bg-teal-500/10 text-teal-600 dark:text-teal-400 px-3 py-1.5 rounded-full border border-teal-500/20 shrink-0">
            <span className="h-2 w-2 rounded-full bg-teal-500 glow-teal" />
            FinIntel Agent Online
          </div>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          
          {/* LEFT PANEL: UPLOADS & HISTORY */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* UPLOAD CARD */}
            <div className="p-6 rounded-2xl glass-card border border-white/40 dark:border-slate-800 space-y-4">
              <h2 className="text-sm font-bold flex items-center gap-2 text-slate-800 dark:text-slate-100">
                <Lucide.UploadCloud className="h-5 w-5 text-teal-500" />
                Upload Document
              </h2>
              
              <form onSubmit={handleUpload} className="space-y-4">
                <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-teal-500 dark:hover:border-teal-500 rounded-xl p-4 text-center cursor-pointer transition-colors relative">
                  <input 
                    type="file" 
                    onChange={handleFileChange}
                    accept=".pdf,.csv,.xlsx,.xls"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <div className="space-y-2">
                    <Lucide.FileText className="h-8 w-8 text-slate-400 mx-auto" />
                    <p className="text-xs font-semibold truncate text-slate-700 dark:text-slate-200">
                      {selectedFile ? selectedFile.name : 'Click to select document'}
                    </p>
                    <p className="text-[10px] text-slate-400">
                      PDF, Excel, CSV (Max 10MB)
                    </p>
                  </div>
                </div>

                {selectedFile && (
                  <button 
                    type="submit"
                    className="w-full py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-sm"
                  >
                    <Lucide.Play className="h-4 w-4" /> Run AI Pipeline
                  </button>
                )}
              </form>

              {/* PROGRESS BAR */}
              {uploadingState !== 'idle' && uploadingState !== '' && (
                <div className="space-y-2 pt-2">
                  <div className="flex items-center justify-between text-xs font-semibold">
                    <span className="text-teal-600 dark:text-teal-400 flex items-center gap-1.5">
                      {uploadingState === 'uploading' ? (
                        <><Lucide.Loader className="h-3 w-3 animate-spin" /> Uploading...</>
                      ) : uploadingState === 'reasoning' ? (
                        <><Lucide.Cpu className="h-3 w-3 animate-spin" /> Processing AI analysis...</>
                      ) : (
                        'Finished'
                      )}
                    </span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div 
                      className="bg-teal-600 h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* RECENT UPLOADS */}
            <div className="p-6 rounded-2xl glass-card border border-white/40 dark:border-slate-800 space-y-4">
              <h2 className="text-sm font-bold flex items-center gap-2 text-slate-800 dark:text-slate-100">
                <Lucide.History className="h-5 w-5 text-indigo-500" />
                Recent Uploads
              </h2>
              
              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {filesHistory.length === 0 ? (
                  <p className="text-xs text-slate-500 py-4 text-center">No documents uploaded yet.</p>
                ) : (
                  filesHistory.map((doc) => (
                    <div 
                      key={doc.id}
                      onClick={() => doc.status === 'analyzed' && loadAnalysis(doc.id, doc.filename)}
                      className={`p-2.5 rounded-xl border text-left cursor-pointer transition-all flex items-center justify-between ${
                        activeAnalysisDocId === doc.id
                          ? 'border-teal-500 bg-teal-500/10 dark:bg-teal-900/20'
                          : 'border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800/40'
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <Lucide.FileSpreadsheet className="h-4 w-4 text-slate-400 shrink-0" />
                        <div className="min-w-0">
                          <p className="text-[11px] font-bold truncate text-slate-800 dark:text-slate-100">{doc.filename}</p>
                          <span className="text-[9px] text-slate-400 dark:text-slate-400 block mt-0.5 leading-none">
                            Date: {new Date(doc.created_at).toLocaleDateString()}
                          </span>
                          <span className="text-[9px] text-slate-400 dark:text-slate-400 block mt-0.5 leading-none">
                            Time: {new Date(doc.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} • {doc.file_type}
                          </span>
                        </div>
                      </div>
                      
                      <div className="shrink-0 flex items-center gap-2">
                        {doc.status === 'analyzed' ? (
                          <span className="h-2 w-2 rounded-full bg-green-500" />
                        ) : doc.status === 'failed' ? (
                          <span className="h-2 w-2 rounded-full bg-red-500" />
                        ) : (
                          <Lucide.Loader className="h-3 w-3 animate-spin text-teal-500" />
                        )}
                        
                        <button 
                          onClick={(e) => handleDeleteDoc(e, doc.id, doc.filename)}
                          className="p-1 rounded text-slate-400 hover:text-rose-500 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
                          title="Delete document"
                        >
                          <Lucide.Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

          </div>

          {/* MAIN ANALYSIS & METRICS AREA */}
          <div className="lg:col-span-3 space-y-6">
            
            {!activeAnalysis ? (
              <div className="p-12 rounded-2xl glass-card border border-white/40 dark:border-slate-800 text-center py-32 space-y-4">
                <Lucide.Binary className="h-12 w-12 text-slate-400 mx-auto" />
                <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">No Financial Document Selected</h3>
                <p className="text-xs text-slate-400 max-w-xs mx-auto">
                  Upload a PDF statement, transaction ledger, or spreadsheet to generate real-time metrics, interactive charts, and start questioning the chatbot.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                
                {/* 12 CORE FINANCIAL METRICS CARDS */}
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                  
                  {/* Card 1 */}
                  <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-800/50 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Revenue</span>
                    <span className="text-sm font-extrabold text-slate-800 dark:text-slate-100">
                      {fmtCurr(activeAnalysis.metrics?.total_revenue)}
                    </span>
                  </div>

                  {/* Card 2 */}
                  <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-800/50 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Total Expense</span>
                    <span className="text-sm font-extrabold text-slate-800 dark:text-slate-100">
                      {fmtCurr(activeAnalysis.metrics?.total_expense)}
                    </span>
                  </div>

                  {/* Card 3 */}
                  <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-800/50 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Gross Profit</span>
                    <span className="text-sm font-extrabold text-slate-800 dark:text-slate-100">
                      {fmtCurr(activeAnalysis.metrics?.gross_profit)}
                    </span>
                  </div>

                  {/* Card 4 */}
                  <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-800/50 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Net Profit</span>
                    <span className={`text-sm font-extrabold ${(activeAnalysis.metrics?.net_profit || 0) >= 0 ? 'text-emerald-600 dark:text-emerald-450' : 'text-rose-500'}`}>
                      {fmtCurr(activeAnalysis.metrics?.net_profit)}
                    </span>
                  </div>

                  {/* Card 5 */}
                  <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-800/50 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Net Cash Flow</span>
                    <span className={`text-sm font-extrabold ${(activeAnalysis.metrics?.cash_flow || 0) >= 0 ? 'text-teal-600 dark:text-teal-400' : 'text-rose-500'}`}>
                      {fmtCurr(activeAnalysis.metrics?.cash_flow)}
                    </span>
                  </div>

                  {/* Card 6 */}
                  <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-800/50 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Current Ratio</span>
                    <span className={`text-sm font-extrabold ${(activeAnalysis.metrics?.current_ratio || 0) >= 1.2 ? 'text-teal-600 dark:text-teal-400' : 'text-amber-500'}`}>
                      {activeAnalysis.metrics?.current_ratio || '1.50'}
                    </span>
                  </div>

                  {/* Card 7 */}
                  <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-800/50 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Quick Ratio</span>
                    <span className="text-sm font-extrabold text-slate-800 dark:text-slate-100">
                      {activeAnalysis.metrics?.quick_ratio || '1.20'}
                    </span>
                  </div>

                  {/* Card 8 */}
                  <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-800/50 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Debt Ratio</span>
                    <span className={`text-sm font-extrabold ${(activeAnalysis.metrics?.debt_ratio || 0) <= 0.6 ? 'text-teal-600 dark:text-teal-400' : 'text-rose-500'}`}>
                      {activeAnalysis.metrics?.debt_ratio || '0.45'}
                    </span>
                  </div>

                  {/* Card 9 */}
                  <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-800/50 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Profit Margin</span>
                    <span className="text-sm font-extrabold text-slate-800 dark:text-slate-100">
                      {fmtPct(activeAnalysis.metrics?.profit_margin)}
                    </span>
                  </div>

                  {/* Card 10 */}
                  <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-800/50 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Operating Margin</span>
                    <span className="text-sm font-extrabold text-slate-800 dark:text-slate-100">
                      {fmtPct(activeAnalysis.metrics?.operating_margin)}
                    </span>
                  </div>

                  {/* Card 11 */}
                  <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-800/50 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Avg Monthly Revenue</span>
                    <span className="text-sm font-extrabold text-slate-800 dark:text-slate-100">
                      {fmtCurr(activeAnalysis.metrics?.avg_monthly_revenue)}
                    </span>
                  </div>

                  {/* Card 12 */}
                  <div className="p-4 rounded-xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-800/50 shadow-sm space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Avg Monthly Expense</span>
                    <span className="text-sm font-extrabold text-slate-800 dark:text-slate-100">
                      {fmtCurr(activeAnalysis.metrics?.avg_monthly_expense)}
                    </span>
                  </div>

                </div>

                {/* VISUAL CHARTS SECTION */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Revenue vs Expense Chart */}
                  <div className="p-5 rounded-2xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-400 flex items-center gap-1.5">
                      <Lucide.TrendingUp className="h-4 w-4 text-teal-500" />
                      Revenue vs Expense Trends
                    </h3>
                    <SVGLineChart 
                      data={activeAnalysis.charts?.revenue_trend || []} 
                      labels={activeAnalysis.charts?.monthly_comparison?.labels || []} 
                      color="#0f766e"
                    />
                  </div>

                  {/* Profit Trend Chart */}
                  <div className="p-5 rounded-2xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-400 flex items-center gap-1.5">
                      <Lucide.PieChart className="h-4 w-4 text-indigo-500" />
                      Net Profit Growth Trend
                    </h3>
                    <SVGBarChart 
                      data={activeAnalysis.charts?.profit_trend || []} 
                      labels={activeAnalysis.charts?.monthly_comparison?.labels || []} 
                      color="#6366f1"
                    />
                  </div>

                  {/* Net Cash Flow Chart */}
                  <div className="p-5 rounded-2xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-400 flex items-center gap-1.5">
                      <Lucide.ArrowUpDown className="h-4 w-4 text-emerald-500" />
                      Net Cash Flow Trend
                    </h3>
                    <SVGLineChart 
                      data={activeAnalysis.charts?.cash_flow || []} 
                      labels={activeAnalysis.charts?.monthly_comparison?.labels || []} 
                      color="#10b981"
                    />
                  </div>

                  {/* Assets vs Liabilities Chart */}
                  <div className="p-5 rounded-2xl border border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-950 shadow-sm space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-400 flex items-center gap-1.5">
                      <Lucide.Scale className="h-4 w-4 text-rose-500" />
                      Assets vs Liabilities Comparison
                    </h3>
                    <AssetsVsLiabilitiesChart 
                      assets={activeAnalysis.charts?.assets_vs_liabilities?.assets || []}
                      liabilities={activeAnalysis.charts?.assets_vs_liabilities?.liabilities || []}
                      labels={activeAnalysis.charts?.monthly_comparison?.labels || []}
                    />
                  </div>
                </div>

                {/* LOWER SECTION: DETAILED INTELLIGENCE REPORT & CHAT TABS */}
                <div className="p-6 rounded-2xl glass-card border border-white/40 dark:border-slate-800 space-y-6">
                  
                  {/* TABS HEADER */}
                  <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 pb-2 border-b border-slate-200/50 dark:border-slate-800/50">
                    <div className="flex flex-wrap gap-1.5">
                      <button 
                        onClick={() => setActiveTab('csa')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                          activeTab === 'csa' 
                            ? 'bg-teal-500/15 text-teal-600 dark:text-teal-400 border border-teal-500/30' 
                            : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800/50'
                        }`}
                      >
                        <Lucide.Activity className="h-3.5 w-3.5" /> Current State
                      </button>

                      <button 
                        onClick={() => setActiveTab('gaps')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                          activeTab === 'gaps' 
                            ? 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30' 
                            : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800/50'
                        }`}
                      >
                        <Lucide.AlertTriangle className="h-3.5 w-3.5" /> Gap Detection
                      </button>

                      <button 
                        onClick={() => setActiveTab('missing')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                          activeTab === 'missing' 
                            ? 'bg-red-500/15 text-red-600 dark:text-red-400 border border-red-500/30' 
                            : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800/50'
                        }`}
                      >
                        <Lucide.FileWarning className="h-3.5 w-3.5" /> Missing Data
                      </button>

                      <button 
                        onClick={() => setActiveTab('flags')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                          activeTab === 'flags' 
                            ? 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30' 
                            : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800/50'
                        }`}
                      >
                        <Lucide.ShieldAlert className="h-3.5 w-3.5" /> Risk Flags
                      </button>

                      <button 
                        onClick={() => setActiveTab('chat')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                          activeTab === 'chat' 
                            ? 'bg-teal-600 text-white shadow-md' 
                            : 'text-slate-400 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800/50 border border-slate-200 dark:border-slate-800'
                        }`}
                      >
                        <Lucide.MessageSquare className="h-3.5 w-3.5" /> Ask FinIntel AI
                      </button>
                    </div>

                    <button 
                      onClick={downloadPDFReport}
                      className="px-4 py-2 bg-slate-800 hover:bg-slate-900 dark:bg-slate-800 dark:hover:bg-slate-750 text-white rounded-lg text-xs font-bold shadow-sm transition-all flex items-center gap-1.5"
                    >
                      <Lucide.Download className="h-4 w-4" /> Download PDF Report
                    </button>
                  </div>

                  {/* TAB CONTENT: CURRENT STATE ANALYSIS */}
                  {activeTab === 'csa' && (
                    <div className="space-y-4">
                      <h3 className="text-sm font-bold text-teal-600 dark:text-teal-400">1. Current State Observations</h3>
                      
                      <div className="grid sm:grid-cols-2 gap-4">
                        
                        <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Revenue Trend</span>
                          <p className="text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                            {activeAnalysis.current_state_analysis?.revenue_trend || 'Not available in document.'}
                          </p>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Expense Trend</span>
                          <p className="text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                            {activeAnalysis.current_state_analysis?.expense_trend || 'Not available in document.'}
                          </p>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Net Profit</span>
                          <p className="text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                            {activeAnalysis.current_state_analysis?.net_profit || 'Not available in document.'}
                          </p>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Operating Margin</span>
                          <p className="text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                            {activeAnalysis.current_state_analysis?.operating_margin || 'Not available in document.'}
                          </p>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Net Cash Flow</span>
                          <p className="text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                            {activeAnalysis.current_state_analysis?.cash_flow || 'Not available in document.'}
                          </p>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Liquidity Status</span>
                          <p className="text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                            {activeAnalysis.current_state_analysis?.liquidity || 'Not available in document.'}
                          </p>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Assets Valuation</span>
                          <p className="text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                            {activeAnalysis.current_state_analysis?.assets || 'Not available in document.'}
                          </p>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Liabilities Standing</span>
                          <p className="text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                            {activeAnalysis.current_state_analysis?.liabilities || 'Not available in document.'}
                          </p>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Equity Breakdown</span>
                          <p className="text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                            {activeAnalysis.current_state_analysis?.equity || 'Not available in document.'}
                          </p>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Debt Ratio</span>
                          <p className="text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                            {activeAnalysis.current_state_analysis?.debt_ratio || 'Not available in document.'}
                          </p>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Current Ratio Interpretation</span>
                          <p className="text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                            {activeAnalysis.current_state_analysis?.current_ratio || 'Not available in document.'}
                          </p>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Overall Profitability</span>
                          <p className="text-[11px] leading-relaxed text-slate-600 dark:text-slate-300">
                            {activeAnalysis.current_state_analysis?.profitability || 'Not available in document.'}
                          </p>
                        </div>

                        <div className="sm:col-span-2 p-3.5 rounded-xl bg-slate-100/50 dark:bg-slate-800/40 border border-slate-200/50 dark:border-slate-700/50 space-y-1.5">
                          <span className="text-[10px] font-bold uppercase text-slate-400">Overall Business Health</span>
                          <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-300 font-semibold">
                            {activeAnalysis.current_state_analysis?.financial_health || 'Not available in document.'}
                          </p>
                        </div>

                      </div>

                      {activeAnalysis.current_state_analysis?.source && (
                        <div className="flex items-center gap-1 text-[10px] text-slate-500 mt-2 bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded w-fit">
                          <Lucide.Link2 className="h-3 w-3 text-slate-400" />
                          <span>Traceable Document: <b>{activeAnalysis.current_state_analysis.source.document}</b> (Page {activeAnalysis.current_state_analysis.source.page})</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* TAB CONTENT: GAP DETECTION */}
                  {activeTab === 'gaps' && (
                    <div className="space-y-4">
                      <h3 className="text-sm font-bold text-amber-600 dark:text-amber-400">2. Critical Gaps & Problems Identified</h3>
                      
                      <div className="space-y-3">
                        {!activeAnalysis.gap_detection || activeAnalysis.gap_detection.length === 0 ? (
                          <p className="text-xs text-slate-500 italic pl-4">No gaps detected from documents.</p>
                        ) : (
                          activeAnalysis.gap_detection.map((gap, idx) => (
                            <div key={idx} className="p-4 rounded-xl border border-amber-200/50 bg-amber-500/5 dark:border-amber-950/50 dark:bg-amber-950/10 space-y-2">
                              <div className="flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
                                <h4 className="text-xs font-bold text-slate-700 dark:text-slate-200">{gap.problem}</h4>
                              </div>
                              <div className="grid sm:grid-cols-2 gap-4 pl-4 text-xs">
                                <div>
                                  <span className="font-bold text-slate-400 block text-[9px] uppercase tracking-wide">Business Impact</span>
                                  <span className="text-slate-600 dark:text-slate-300 leading-relaxed block mt-0.5">{gap.impact}</span>
                                </div>
                                <div>
                                  <span className="font-bold text-slate-400 block text-[9px] uppercase tracking-wide">Actionable Recommendation</span>
                                  <span className="text-slate-600 dark:text-slate-300 leading-relaxed block mt-0.5">{gap.recommendation}</span>
                                </div>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}

                  {/* TAB CONTENT: MISSING DATA DETECTION */}
                  {activeTab === 'missing' && (
                    <div className="space-y-4">
                      <h3 className="text-sm font-bold text-rose-500 dark:text-rose-400">3. Missing Information & Statement Audit</h3>
                      
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border-collapse">
                          <thead>
                            <tr className="border-b border-slate-200 dark:border-slate-800 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                              <th className="py-2.5">Missing Attribute / Statement</th>
                              <th className="py-2.5 px-4">Importance</th>
                              <th className="py-2.5">AI Recommendation</th>
                            </tr>
                          </thead>
                          <tbody>
                            {!activeAnalysis.missing_data_detection || activeAnalysis.missing_data_detection.length === 0 ? (
                              <tr>
                                <td colSpan="3" className="py-4 text-center text-slate-500 italic">No missing fields detected from document.</td>
                              </tr>
                            ) : (
                              activeAnalysis.missing_data_detection.map((item, idx) => (
                                <tr key={idx} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-100/30 dark:hover:bg-slate-900/20">
                                  <td className="py-3 font-semibold text-slate-800 dark:text-slate-200">{item.missing_data}</td>
                                  <td className="py-3 px-4">
                                    <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                                      item.importance === 'High' 
                                        ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20' 
                                        : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                                    }`}>
                                      {item.importance}
                                    </span>
                                  </td>
                                  <td className="py-3 text-slate-500 dark:text-slate-400">{item.recommendation}</td>
                                </tr>
                              ))
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* TAB CONTENT: RISK & GROWTH FLAGS */}
                  {activeTab === 'flags' && (
                    <div className="space-y-4">
                      <h3 className="text-sm font-bold text-indigo-600 dark:text-indigo-400">4. Forward Looking Risks & Opportunities</h3>
                      
                      <div className="space-y-3">
                        {!activeAnalysis.forward_looking_flags || activeAnalysis.forward_looking_flags.length === 0 ? (
                          <p className="text-xs text-slate-500 italic pl-4">No risk flags mapped.</p>
                        ) : (
                          activeAnalysis.forward_looking_flags.map((flag, idx) => (
                            <div key={idx} className="p-4 rounded-xl border border-indigo-200/50 bg-indigo-500/5 dark:border-indigo-950/50 dark:bg-indigo-950/10 space-y-2">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className="h-2 w-2 rounded-full bg-indigo-500" />
                                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-200">{flag.flag}</h4>
                                </div>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                                  flag.risk_level === 'High' 
                                    ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/25' 
                                    : flag.risk_level === 'Medium'
                                    ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/25'
                                    : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/25'
                                }`}>
                                  Risk: {flag.risk_level}
                                </span>
                              </div>
                              <p className="text-[11px] text-slate-600 dark:text-slate-300 pl-4 leading-relaxed">
                                {flag.reason}
                              </p>
                              <div className="flex items-center gap-6 pl-4 pt-1 text-[10px] text-slate-500 dark:text-slate-400">
                                <span>Growth Score: <b className="text-indigo-600 dark:text-indigo-400">{flag.growth_score}/100</b></span>
                                <span>Confidence: <b className="text-teal-600 dark:text-teal-400">{flag.confidence_score}%</b></span>
                                {flag.source && <span className="italic">Trace: {flag.source}</span>}
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}

                  {/* TAB CONTENT: CHATBOT WIDGET */}
                  {activeTab === 'chat' && (
                    <div className="flex flex-col h-[350px] border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden bg-slate-100/20 dark:bg-slate-950/20">
                      
                      {/* Chat messages history */}
                      <div className="flex-grow p-4 overflow-y-auto space-y-3.5 scrollbar-thin">
                        {chatHistory.length === 0 ? (
                          <div className="text-center py-16 space-y-2">
                            <Lucide.Bot className="h-10 w-10 text-teal-500 mx-auto" />
                            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-100">Ask about {activeAnalysisDocName}</h4>
                            <p className="text-[10px] text-slate-400 max-w-xs mx-auto">
                              I can answer questions regarding revenue, expense margins, tax guidance, cash flow, debt ratios, or overall SME finance.
                            </p>
                          </div>
                        ) : (
                          chatHistory.map((msg, idx) => (
                            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                              <div className={`max-w-[80%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
                                msg.role === 'user'
                                  ? 'bg-teal-600 text-white rounded-br-none'
                                  : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 border border-slate-200/50 dark:border-slate-800/80 rounded-bl-none shadow-sm'
                              }`}>
                                <p className="whitespace-pre-line">{msg.content}</p>
                              </div>
                            </div>
                          ))
                        )}
                        {isChatLoading && (
                          <div className="flex justify-start">
                            <div className="bg-white dark:bg-slate-800 rounded-xl rounded-bl-none px-4 py-2 border border-slate-200/50 dark:border-slate-800/80 flex items-center gap-1.5 text-xs text-slate-400 shadow-sm">
                              <Lucide.Loader className="h-3 w-3 animate-spin text-teal-500" />
                              Analyzing context chunks...
                            </div>
                          </div>
                        )}
                        <div ref={chatBottomRef} />
                      </div>

                      {/* Input controls */}
                      <form onSubmit={handleSendChatMessage} className="p-3 border-t border-slate-200/50 dark:border-slate-800 bg-white dark:bg-slate-900 flex gap-2">
                        <input 
                          type="text" 
                          value={chatMessage}
                          onChange={(e) => setChatMessage(e.target.value)}
                          placeholder="E.g., What is our debt ratio and should we optimize expenses?"
                          className="flex-grow bg-slate-100 dark:bg-slate-800 text-xs px-3.5 py-2.5 rounded-lg border-none focus:outline-none focus:ring-1 focus:ring-teal-500 text-slate-800 dark:text-slate-100"
                        />
                        <button 
                          type="submit"
                          disabled={!chatMessage.trim() || isChatLoading}
                          className="px-3.5 py-2.5 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition-colors"
                        >
                          <Lucide.Send className="h-4 w-4" />
                        </button>
                      </form>
                    </div>
                  )}

                </div>

              </div>
            )}

          </div>

        </div>

      </main>

      {/* PROFILE DETAIL MODAL */}
      <AnimatePresence>
        {showProfileModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-slate-900/60 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 30 }}
              className="w-full max-w-sm p-6 rounded-2xl glass-card border border-white/40 dark:border-slate-800 shadow-2xl relative bg-white dark:bg-slate-900"
            >
              <button 
                onClick={() => setShowProfileModal(false)}
                className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
              >
                <Lucide.X className="h-4 w-4" />
              </button>
              
              <div className="text-center space-y-4 mt-2">
                <Lucide.UserCircle className="h-14 w-14 text-teal-600 mx-auto" />
                <div>
                  <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">{user?.full_name || 'Fintech User'}</h3>
                  <p className="text-xs text-slate-400">{user?.email || 'user@company.com'}</p>
                </div>
                
                <div className="border-t border-slate-200 dark:border-slate-800 pt-4 text-left space-y-2.5 text-xs text-slate-700 dark:text-slate-300">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Account Reference</span>
                    <span className="font-semibold">USR-00{user?.id || '99'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">History Size</span>
                    <span className="font-semibold">{filesHistory.length} uploads</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">System Role</span>
                    <span className="font-semibold text-teal-500">Business Analyst</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

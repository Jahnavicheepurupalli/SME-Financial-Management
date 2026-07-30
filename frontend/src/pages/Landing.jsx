import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

// Note: Using standard Lucide icons fallback structure if HeroIcons fail to resolve.
import * as Lucide from 'lucide-react';

export default function Landing({ darkMode, toggleDarkMode }) {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 transition-colors duration-300">
      {/* NAVBAR */}
      <nav className="fixed top-0 left-0 w-full z-50 glass-panel border-b border-slate-200/50 dark:border-slate-800/50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Lucide.TrendingUp className="h-8 w-8 text-teal-600 dark:text-teal-400" />
          <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-teal-600 to-indigo-500 bg-clip-text text-transparent">
            FinIntel SME
          </span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium">
          <a href="#features" className="hover:text-teal-600 dark:hover:text-teal-400 transition-colors">Features</a>
          <a href="#why-choose-us" className="hover:text-teal-600 dark:hover:text-teal-400 transition-colors">Why Us</a>
          <a href="#how-it-works" className="hover:text-teal-600 dark:hover:text-teal-400 transition-colors">Workflow</a>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={toggleDarkMode} 
            className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
          >
            {darkMode ? <Lucide.Sun className="h-5 w-5" /> : <Lucide.Moon className="h-5 w-5" />}
          </button>
          <Link to="/login" className="text-sm font-medium hover:text-teal-600 transition-colors">
            Login
          </Link>
          <Link 
            to="/signup" 
            className="px-4 py-2 text-sm font-semibold text-white bg-teal-600 hover:bg-teal-700 dark:bg-teal-500 dark:hover:bg-teal-600 rounded-lg shadow-sm hover:shadow transition-all"
          >
            Sign Up
          </Link>
        </div>
      </nav>

      {/* HERO SECTION */}
      <header className="relative pt-32 pb-20 px-6 max-w-7xl mx-auto flex flex-col md:flex-row items-center gap-12">
        <div className="flex-1 space-y-6">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="px-3 py-1 text-xs font-semibold text-teal-600 dark:text-teal-400 bg-teal-100/50 dark:bg-teal-900/30 rounded-full">
              Automated AI Agent
            </span>
          </motion.div>
          <motion.h1 
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl md:text-5xl font-extrabold tracking-tight leading-tight"
          >
            Real-Time Financial <br />
            <span className="bg-gradient-to-r from-teal-600 to-indigo-500 bg-clip-text text-transparent">
              Document Intelligence
            </span> for SMEs
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg text-slate-600 dark:text-slate-400 max-w-xl"
          >
            Instantly extract liquidity status, detect documentation gaps, and map forward-looking risks from bank statements, invoices, and ledger sheets with zero setup.
          </motion.p>
          <motion.div 
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-wrap gap-4 pt-4"
          >
            <Link 
              to="/signup" 
              className="px-6 py-3 font-semibold text-white bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-700 hover:to-teal-600 rounded-xl shadow-lg shadow-teal-500/10 hover:shadow-teal-500/20 transition-all flex items-center gap-2"
            >
              Get Started Now <Lucide.ArrowRight className="h-4 w-4" />
            </Link>
            <a 
              href="#features" 
              className="px-6 py-3 font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700/50 rounded-xl transition-all"
            >
              Learn More
            </a>
          </motion.div>
        </div>

        {/* HERO ILLUSTRATION */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="flex-1 w-full flex justify-center"
        >
          <div className="relative w-full max-w-md h-80 rounded-2xl glass-card flex flex-col justify-between p-6 border border-white/40 dark:border-slate-800 shadow-xl overflow-hidden">
            <div className="absolute top-0 right-0 -mt-10 -mr-10 w-40 h-40 bg-teal-500/10 dark:bg-teal-400/10 rounded-full blur-2xl" />
            <div className="absolute bottom-0 left-0 -mb-10 -ml-10 w-40 h-40 bg-indigo-500/10 dark:bg-indigo-400/10 rounded-full blur-2xl" />
            
            <div className="flex items-center justify-between border-b border-slate-200/50 dark:border-slate-700/50 pb-4">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 bg-red-400 rounded-full" />
                <div className="h-3 w-3 bg-yellow-400 rounded-full" />
                <div className="h-3 w-3 bg-green-400 rounded-full" />
              </div>
              <span className="text-xs text-slate-500">Agentic Engine v1.0</span>
            </div>

            <div className="space-y-4 my-auto">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded bg-teal-100 dark:bg-teal-900/50 text-teal-600 dark:text-teal-400">
                  <Lucide.FileSpreadsheet className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <div className="h-2 w-24 bg-slate-300 dark:bg-slate-700 rounded mb-1" />
                  <div className="h-1.5 w-32 bg-slate-200 dark:bg-slate-800 rounded" />
                </div>
                <span className="text-xs text-teal-600 font-semibold bg-teal-100/50 px-2 py-0.5 rounded">Uploaded</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400">
                  <Lucide.Cpu className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <div className="h-2 w-32 bg-slate-300 dark:bg-slate-700 rounded mb-1" />
                  <div className="h-1.5 w-16 bg-slate-200 dark:bg-slate-800 rounded" />
                </div>
                <span className="text-xs text-indigo-600 font-semibold bg-indigo-100/50 px-2 py-0.5 rounded">Reasoning...</span>
              </div>
            </div>

            <div className="flex items-center justify-between border-t border-slate-200/50 dark:border-slate-700/50 pt-4 text-xs text-slate-500">
              <span>Ratios Extracted</span>
              <span>100% Traceability</span>
            </div>
          </div>
        </motion.div>
      </header>

      {/* FEATURES SECTION */}
      <section id="features" className="py-20 bg-white dark:bg-slate-900/60 border-t border-slate-200/50 dark:border-slate-800/50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto space-y-4 mb-16">
            <h2 className="text-3xl font-bold tracking-tight">Structured Document Intelligence</h2>
            <p className="text-slate-600 dark:text-slate-400">
              The AI Agent automatically performs reasoning without chat inputs, producing exactly three critical evaluation models.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl glass-card hover:translate-y-[-4px] transition-transform duration-300">
              <div className="p-3 bg-teal-100 dark:bg-teal-900/50 text-teal-600 dark:text-teal-400 rounded-xl w-fit mb-6">
                <Lucide.Activity className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-semibold mb-3">1. Current State Analysis</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                Extracts liquidity, revenue levels, net profit margins, and expense structures, complete with automated financial ratio calculations and definitions.
              </p>
            </div>

            <div className="p-6 rounded-2xl glass-card hover:translate-y-[-4px] transition-transform duration-300">
              <div className="p-3 bg-orange-100 dark:bg-orange-900/50 text-orange-600 dark:text-orange-400 rounded-xl w-fit mb-6">
                <Lucide.AlertCircle className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-semibold mb-3">2. Gap Detection</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                Flags missing ledger lines, balance sheet statements, or necessary ratio metrics. Intended as soft reminders to secure compliance.
              </p>
            </div>

            <div className="p-6 rounded-2xl glass-card hover:translate-y-[-4px] transition-transform duration-300">
              <div className="p-3 bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 rounded-xl w-fit mb-6">
                <Lucide.Clock className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-semibold mb-3">3. Forward Looking Flags</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                Maps historical patterns of receivable delays, cash runways, and cost growth metrics without simulating future predictions.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how-it-works" className="py-20 px-6 max-w-7xl mx-auto">
        <div className="text-center max-w-2xl mx-auto space-y-4 mb-16">
          <h2 className="text-3xl font-bold tracking-tight">How It Works</h2>
          <p className="text-slate-600 dark:text-slate-400">
            Upload a single file, and let the agent manage the entire data intelligence pipeline.
          </p>
        </div>

        <div className="grid md:grid-cols-4 gap-8 relative">
          <div className="flex flex-col items-center text-center space-y-4">
            <div className="h-12 w-12 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold text-lg">
              1
            </div>
            <h4 className="font-semibold text-lg">Upload</h4>
            <p className="text-sm text-slate-500">
              Upload PDF, CSV, Excel sheets, or scanned PNG/JPG receipts.
            </p>
          </div>

          <div className="flex flex-col items-center text-center space-y-4">
            <div className="h-12 w-12 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold text-lg">
              2
            </div>
            <h4 className="font-semibold text-lg">OCR & Index</h4>
            <p className="text-sm text-slate-500">
              Automatically extract text and index pages inside the vector store.
            </p>
          </div>

          <div className="flex flex-col items-center text-center space-y-4">
            <div className="h-12 w-12 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold text-lg">
              3
            </div>
            <h4 className="font-semibold text-lg">Agent Inference</h4>
            <p className="text-sm text-slate-500">
              LangChain tools extract data, detect gaps, and map flags.
            </p>
          </div>

          <div className="flex flex-col items-center text-center space-y-4">
            <div className="h-12 w-12 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold text-lg">
              4
            </div>
            <h4 className="font-semibold text-lg">PDF & Dashboard</h4>
            <p className="text-sm text-slate-500">
              Instantly view reports on your screen and download a PDF.
            </p>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-slate-200 dark:border-slate-800 py-8 px-6 text-center text-sm text-slate-500 bg-white dark:bg-slate-950">
        <p>&copy; {new Date().getFullYear()} FinIntel SME. Built for Hackathon judging. All rights reserved.</p>
      </footer>
    </div>
  );
}

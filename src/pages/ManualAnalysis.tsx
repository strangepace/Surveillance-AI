
import React from 'react';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

const ManualAnalysis = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black flex items-center justify-center">
      <div className="text-center text-white space-y-6">
        <h1 className="text-4xl font-mono font-bold">Manual Video Analysis</h1>
        <p className="text-xl text-gray-300">M1 Screen - Coming Soon</p>
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-purple-400 hover:text-purple-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </div>
    </div>
  );
};

export default ManualAnalysis;

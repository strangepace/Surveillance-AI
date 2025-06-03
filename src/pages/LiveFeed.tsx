
import React from 'react';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

const LiveFeed = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black flex items-center justify-center">
      <div className="text-center text-white space-y-6">
        <h1 className="text-4xl font-mono font-bold">Live Feed Dashboard</h1>
        <p className="text-xl text-gray-300">L1 Screen - Coming Soon</p>
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </div>
    </div>
  );
};

export default LiveFeed;

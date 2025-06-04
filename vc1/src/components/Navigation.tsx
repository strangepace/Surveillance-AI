
import React from 'react';
import { Menu, Shield, FileText, LogIn } from 'lucide-react';

const Navigation = () => {
  return (
    <nav className="absolute top-0 left-0 right-0 z-50 p-6">
      <div className="flex justify-between items-center">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <Shield className="w-8 h-8 text-cyan-400" />
          <span className="text-xl font-mono font-bold text-white tracking-wider">
            SURVEILLANCE.AI
          </span>
        </div>
        
        {/* Navigation Links */}
        <div className="hidden md:flex items-center gap-6">
          <a href="#about" className="text-gray-300 hover:text-cyan-400 transition-colors font-mono tracking-wide">
            About
          </a>
          <a href="#docs" className="text-gray-300 hover:text-cyan-400 transition-colors font-mono tracking-wide flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Docs
          </a>
          <button className="text-gray-300 hover:text-cyan-400 transition-colors font-mono tracking-wide flex items-center gap-2 px-4 py-2 border border-gray-600 hover:border-cyan-400 rounded">
            <LogIn className="w-4 h-4" />
            Login
          </button>
        </div>
        
        {/* Mobile menu */}
        <button className="md:hidden text-gray-300 hover:text-cyan-400">
          <Menu className="w-6 h-6" />
        </button>
      </div>
    </nav>
  );
};

export default Navigation;

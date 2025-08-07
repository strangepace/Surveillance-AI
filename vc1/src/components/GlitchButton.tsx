
import React from 'react';
import { cn } from '@/lib/utils';

interface GlitchButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
  className?: string;
}

const GlitchButton = ({ children, onClick, variant = 'primary', className }: GlitchButtonProps) => {
  const baseClasses = "relative group px-8 py-4 font-mono font-bold text-lg tracking-wider transition-all duration-300 transform overflow-hidden";
  
  const variantClasses = {
    primary: "bg-gradient-to-r from-cyan-500/20 to-blue-600/20 border border-cyan-400/50 text-cyan-300 hover:text-white hover:border-cyan-300 hover:shadow-[0_0_30px_rgba(6,182,212,0.5)]",
    secondary: "bg-gradient-to-r from-purple-500/20 to-pink-600/20 border border-purple-400/50 text-purple-300 hover:text-white hover:border-purple-300 hover:shadow-[0_0_30px_rgba(168,85,247,0.5)]"
  };

  return (
    <button
      onClick={onClick}
      className={cn(baseClasses, variantClasses[variant], className)}
    >
      {/* Glitch effect overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
      
      {/* Button content */}
      <span className="relative z-10 flex items-center justify-center gap-3">
        {children}
      </span>
      
      {/* Animated border */}
      <div className="absolute inset-0 rounded border-2 border-transparent group-hover:border-current animate-pulse" />
    </button>
  );
};

export default GlitchButton;

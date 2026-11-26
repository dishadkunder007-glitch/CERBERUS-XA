import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

export const StatCard = ({ title, value, subtitle, icon: Icon, color = 'blue', trend, badge }) => {
  const shouldReduceMotion = useReducedMotion();

  const colorStyles = {
    blue: {
      border: 'border-slate-200 dark:border-cerberus-blue/30 hover:border-blue-500 dark:hover:border-cerberus-blue/60',
      iconBg: 'bg-blue-50 dark:bg-cerberus-blue/15 text-blue-600 dark:text-cerberus-cyan',
      valueText: 'text-slate-900 dark:text-white',
      glow: 'hover:shadow-lg dark:hover:shadow-glow-blue'
    },
    cyan: {
      border: 'border-slate-200 dark:border-cerberus-cyan/30 hover:border-cyan-500 dark:hover:border-cerberus-cyan/60',
      iconBg: 'bg-cyan-50 dark:bg-cerberus-cyan/15 text-cyan-600 dark:text-cerberus-cyan',
      valueText: 'text-cyan-700 dark:text-cerberus-cyan',
      glow: 'hover:shadow-lg dark:hover:shadow-glow-cyan'
    },
    red: {
      border: 'border-slate-200 dark:border-cerberus-red/30 hover:border-rose-500 dark:hover:border-cerberus-red/60',
      iconBg: 'bg-rose-50 dark:bg-cerberus-red/15 text-rose-600 dark:text-cerberus-red',
      valueText: 'text-rose-700 dark:text-cerberus-red',
      glow: 'hover:shadow-lg dark:hover:shadow-glow-red'
    },
    amber: {
      border: 'border-slate-200 dark:border-cerberus-amber/30 hover:border-amber-500 dark:hover:border-cerberus-amber/60',
      iconBg: 'bg-amber-50 dark:bg-cerberus-amber/15 text-amber-600 dark:text-cerberus-amber',
      valueText: 'text-amber-700 dark:text-cerberus-amber',
      glow: 'hover:shadow-lg dark:hover:shadow-glow-amber'
    },
    green: {
      border: 'border-slate-200 dark:border-cerberus-green/30 hover:border-emerald-500 dark:hover:border-cerberus-green/60',
      iconBg: 'bg-emerald-50 dark:bg-cerberus-green/15 text-emerald-600 dark:text-cerberus-green',
      valueText: 'text-emerald-700 dark:text-cerberus-green',
      glow: 'hover:shadow-lg dark:hover:shadow-glass'
    }
  }[color] || {
    border: 'border-slate-200 dark:border-cerberus-border',
    iconBg: 'bg-slate-100 dark:bg-cerberus-bg text-slate-600 dark:text-cerberus-muted',
    valueText: 'text-slate-900 dark:text-white',
    glow: 'hover:shadow-md'
  };

  return (
    <motion.div 
      whileHover={shouldReduceMotion ? {} : { y: -3, transition: { duration: 0.2 } }}
      className={`relative p-5 rounded-2xl bg-white dark:bg-cerberus-card/90 border ${colorStyles.border} transition-colors duration-200 ${colorStyles.glow} shadow-sm dark:shadow-panel group`}
    >
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-bold tracking-wider text-slate-500 dark:text-cerberus-muted uppercase font-mono">
          {title}
        </span>
        {Icon && (
          <div className={`p-2 rounded-xl ${colorStyles.iconBg} transition-transform group-hover:scale-105`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className={`text-2xl sm:text-3xl font-black tracking-tight ${colorStyles.valueText} font-mono`}>
          {value}
        </span>
        {badge && (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-cerberus-bg-secondary text-blue-700 dark:text-cerberus-cyan border border-slate-200 dark:border-cerberus-border font-bold">
            {badge}
          </span>
        )}
      </div>

      {(subtitle || trend) && (
        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-600 dark:text-cerberus-muted font-sans">
          <span>{subtitle}</span>
          {trend && (
            <span className={`font-mono font-bold ${trend.startsWith('+') ? 'text-rose-600 dark:text-cerberus-red' : 'text-emerald-600 dark:text-cerberus-green'}`}>
              {trend}
            </span>
          )}
        </div>
      )}
    </motion.div>
  );
};

export default StatCard;

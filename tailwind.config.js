/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cerberus: {
          bg: '#050A16',
          'bg-secondary': '#0B1426',
          'card': '#101C30',
          'card-hover': '#162540',
          'border': '#1A2C4B',
          'border-light': '#243C66',
          'blue': '#3478F6',
          'cyan': '#36D8F2',
          'gold': '#F5B942',
          'green': '#21C997',
          'amber': '#FFB547',
          'red': '#FF536B',
          'text': '#F1F5F9',
          'muted': '#94A3B8',
          'dark-muted': '#64748B',
        },
        dark: {
          950: '#050A16',
          900: '#0B1426',
          850: '#0E1A32',
          800: '#101C30',
          750: '#15243E',
          700: '#1A2C4B',
          600: '#263E68',
        }
      },
      fontFamily: {
        display: ['Space Grotesk', 'system-ui', 'sans-serif'],
        sans: ['Plus Jakarta Sans', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Roboto Mono', 'monospace'],
      },
      boxShadow: {
        'glow-blue': '0 0 25px -4px rgba(52, 120, 246, 0.45)',
        'glow-cyan': '0 0 25px -4px rgba(54, 216, 242, 0.45)',
        'glow-red': '0 0 25px -4px rgba(255, 83, 107, 0.45)',
        'glow-amber': '0 0 25px -4px rgba(255, 181, 71, 0.4)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.45)',
        'panel': '0 4px 24px -2px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(54, 216, 242, 0.08)',
      },
      backdropBlur: {
        'xs': '2px',
      }
    },
  },
  plugins: [],
}

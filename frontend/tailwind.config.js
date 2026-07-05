/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Design tokens
        bg:       '#0d0e11',
        surface:  '#13151a',
        surface2: '#1a1d24',
        border:   '#282c36',
        border2:  '#343844',
        // Text
        'text-base':  '#e2e4ea',
        'text-muted': '#6b7280',
        'text-dim':   '#3f4451',
        // Brand
        accent:  '#5b7fff',
        accent2: '#7c63f5',
        // Status
        'status-green':  '#22c55e',
        'status-red':    '#ef4444',
        'status-yellow': '#f59e0b',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '10px',
        lg: '14px',
        xl: '18px',
      },
      boxShadow: {
        card: '0 0 0 1px #282c36, 0 2px 8px rgba(0,0,0,0.4)',
        'card-hover': '0 0 0 1px #343844, 0 4px 16px rgba(0,0,0,0.5)',
        accent: '0 0 20px rgba(91,127,255,0.25)',
      },
    },
  },
  plugins: [],
}

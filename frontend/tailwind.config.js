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
        dark: {
          950: '#000000',
          900: '#09090b',
          850: '#121215',
          800: '#18181b',
          700: '#27272a',
          600: '#3f3f46'
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace', 'ui-monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif']
      }
    },
  },
  plugins: [],
}

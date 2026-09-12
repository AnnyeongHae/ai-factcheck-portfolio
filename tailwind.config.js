/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{html,js}',
    './public/**/*.{html,js}',
    './docs/**/*.{html,js}'
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Pretendard', 'Noto Sans SC', 'Geist', '-apple-system', 'BlinkMacSystemFont', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        surface: {
          canvas: '#f8f9fa',
          subtle: '#f1f3f5',
          card: '#ffffff',
          border: '#e9ecef',
          borderHover: '#ced4da',
        },
        ink: {
          primary: '#111827',
          secondary: '#374151',
          muted: '#6b7280',
          faint: '#9ca3af',
        }
      }
    }
  },
  plugins: []
};

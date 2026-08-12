/** @type {import('tailwindcss').Config} */
export default {
  content: ['./*.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        avyro: {
          50: '#eef6ff',
          500: '#2563eb',
          600: '#1d4ed8',
          700: '#1e40af',
        },
      },
    },
  },
  plugins: [],
}

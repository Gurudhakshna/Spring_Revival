/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eff6f4', 100: '#d7ebe5', 200: '#b0d7cc', 300: '#7dbdad',
          400: '#4a9d8b', 500: '#2c7f70', 600: '#20665b', 700: '#1c534b',
          800: '#1a433d', 900: '#173834',
        },
      },
    },
  },
  plugins: [],
};
